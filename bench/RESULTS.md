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

Harness check on the walking skeleton -- not a bound (L07); Phase 7 re-sweeps.

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

Harness check on the walking skeleton -- not a bound (L07); Phase 7 re-sweeps.

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

Harness check on the walking skeleton -- not a bound (L07); Phase 7 re-sweeps.

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

Harness check on the walking skeleton -- not a bound (L07); Phase 7 re-sweeps.

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

## Coverage floor (Phase 1)

Measured on the finished skeleton suite (285 tests across params, calc, solid, pool, api,
records, cli, parity, pr_land, skip_tokens and bench), 2026-10-06, by spur L34's rule: one
serial run and three `-n 8` runs, the floor being `floor(L - max(0.25, S))` with L the lowest of
the four totals and S the spread (max minus min) of the three `-n 8` totals. This is a floor on
what the suite covers today, not a statement that the code is correct to that fraction.

Host: Apple M2 Max, 12 CPUs, 32 GiB RAM, macOS (Darwin 27.0.0), Python 3.12.13, pytest-cov 7.1.0,
pytest-xdist 3.8.0, native arm64 (no container). Other projects were running on this host, so it
was not idle; `uptime` immediately before each run read:

| Run | Command | Load averages (1, 5, 15 min) | TOTAL | Wall |
|---|---|---|---|---|
| serial | `.venv/bin/python -m pytest -n0 --cov --cov-report=term --cov-fail-under=0` | 3.09, 2.72, 2.56 | 95.03 % | 34.28 s |
| -n 8 (1) | `.venv/bin/python -m pytest -n 8 --cov --cov-report=term --cov-fail-under=0` | 2.59, 2.63, 2.53 | 95.56 % | 16.90 s |
| -n 8 (2) | same | 2.67, 2.64, 2.54 | 95.56 % | 16.92 s |
| -n 8 (3) | same | 3.21, 2.77, 2.59 | 95.56 % | 16.97 s |

L = 95.03 (the serial run). S = 0.00 (three identical `-n 8` totals). Floor =
floor(95.03 - max(0.25, 0.00)) = floor(94.78) = **94**, set as `fail_under` in `pyproject.toml`.

The serial run reads 0.53 below the `-n 8` runs, and the whole difference is `pool.py`: the
serial run missed 3 of its lines (95.31 %), all four `-n 8` runs (the three above and one more
taken to read the per-module column) covered it fully (100.00 %). That is spur's Pitfall 13
(serial runs lose `pool.py` lines); the cause was not isolated here, and the rule already takes
the lowest total, so nothing was chased. Every other module reads the same serial and `-n 8`:

| Module | Cover |
|---|---|
| `__init__.py` | 71.43 % |
| `__main__.py` | 0.00 % |
| `app.py` | 96.83 % |
| `build_errors.py` | 100.00 % |
| `calc/__init__.py` | 100.00 % |
| `cli.py` | 95.88 % |
| `params.py` | 96.00 % |
| `pool.py` | 95.31 % serial, 100.00 % at `-n 8` |
| `records.py` | 94.03 % |
| `solid/__init__.py` | 91.30 % |
| `solid/bolt.py` | 100.00 % |

`PYTEST_WORKERS` is 8, spur L34's knee, not re-measured for screw. `make test` runs
`-n 8 --cov`: the 16.9 s above is pytest's own time with coverage on, against 34.3 s serial.

## Thread spike (Phase 2)

This section records the pre-registered thread spike campaign of
`.planning/phases/02-thread-spike/02-SPIKE.md` (protocol file blob
`4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, landed on main as commit
`fd40abc09947744b3e030446085e26a9e1a0c87f`, PR 5). It is a measurement and not a bound (L07):
nothing here sets a limit, and every input the protocol labels UNVERIFIED or INTERIM keeps
that label in the outputs below. Run id prefix `2026-10-08-a`, nine blocks, run on HEAD
`32cdeacce53cedc2fe3791d27104b599197f45e9` between 2026-10-08 and 2026-10-09 (UTC); each
block's window is in its entry.

Host for every native block: Apple M5 Max, 18 CPUs, arm64, 64 GiB RAM, macOS 27.0.1 (build
26A434), Python 3.12.15, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1. The container block ran the
image `screw:latest` (`sha256:7d992a89557b01bf2e35e0d368f8b68fd11e9c2774bbdfb45a26f1f7a31638f6`,
created 2026-10-08T16:52:13.591964824+06:00, linux/amd64) under emulation on that arm64 host
(OrbStack, docker server 29.4.0). The reference package the harness imports through SCREW_SPIKE_CQW is
cq_warehouse at commit `daa46507ecc429c0e2dce11d9d5ffd09b12a42af`, installed outside the repo.

Two departures from the protocol's registered conditions, stated as plain fact:

- **The host differs from the registered one.** The protocol's Environment section registers
  `Apple M2 Max, 12 CPUs, arm64, 32 GiB RAM` and Python 3.12.13. The host that ran is the one
  above. The kernel pair is identical to the protocol's (cadquery 2.8.0, cadquery-ocp
  7.9.3.1.1), so the protocol's re-measure trigger did not fire, and the run went ahead without
  amending the protocol's Environment section (the owner's option A).
- **Owner ruling R4 was overridden by the owner on 2026-10-08.** R4 asks for the campaign to be
  run from a plain terminal with every agent session closed. The owner decided to run it
  anyway ("No, I don't want to idle for the whole day. Run yourself as is, I won't exit any
  app"), and the campaign was launched from the orchestrating Claude Code session, with other
  agent sessions and applications open, at about 2026-10-08T11:01Z:
  `SCREW_SPIKE_CQW="$HOME/.cache/screw-spike/cq_warehouse-daa4650" DOCKER_DEFAULT_PLATFORM=linux/amd64 nohup caffeinate -i make bench.thread ARGS="campaign --run-id 2026-10-08-a"`.
  The host carried other load throughout. Each block's quiet-gate readings and its end reading
  (which includes the run's own load) are in its output below; those are the load record, and
  the quiet gate's release line says whether the block is decisive.

No block was restarted, interrupted or refused, and nothing was re-run toward a pass: a block
whose gate did not release is recorded as non-decisive. Outputs below are the run's own `.md`
files concatenated unedited; the raw per-row records are the JSONL files named in each entry,
identified by line count (one header line, then one line per row) and sha256.

### 2026-10-08-a-ksweep

Run window (UTC): 2026-10-08T11:01:06+00:00 (first gate reading) to 2026-10-08T11:26:43+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: non-decisive after 900 s (31 readings). Gate readings: 31; first load1 1.93 read 2026-10-08T11:01:06+00:00; last load1 3.49 read 2026-10-08T11:16:06+00:00. Every reading is in the output below.
End reading: load1 9.68 read 2026-10-08T11:26:43+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-ksweep.jsonl` — 193 lines, sha256 b37e51137000318eda411215671e4b1e865c2bc6c769be01b27be2b07b5ea73a. Markdown output: `bench/results/thread-spike/2026-10-08-a-ksweep.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-ksweep

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: ksweep
- K: swept (swept over K in 3, 5, 10)
- load1 1.93 read 2026-10-08T11:01:06+00:00
- load1 2.18 read 2026-10-08T11:01:36+00:00
- load1 1.76 read 2026-10-08T11:02:06+00:00
- load1 1.99 read 2026-10-08T11:02:36+00:00
- load1 2.04 read 2026-10-08T11:03:06+00:00
- load1 1.91 read 2026-10-08T11:03:36+00:00
- load1 2.36 read 2026-10-08T11:04:06+00:00
- load1 2.26 read 2026-10-08T11:04:36+00:00
- load1 2.29 read 2026-10-08T11:05:06+00:00
- load1 2.66 read 2026-10-08T11:05:36+00:00
- load1 2.41 read 2026-10-08T11:06:06+00:00
- load1 2.33 read 2026-10-08T11:06:36+00:00
- load1 2.61 read 2026-10-08T11:07:06+00:00
- load1 2.68 read 2026-10-08T11:07:36+00:00
- load1 3.05 read 2026-10-08T11:08:06+00:00
- load1 3.50 read 2026-10-08T11:08:36+00:00
- load1 3.66 read 2026-10-08T11:09:06+00:00
- load1 3.58 read 2026-10-08T11:09:36+00:00
- load1 3.50 read 2026-10-08T11:10:06+00:00
- load1 2.70 read 2026-10-08T11:10:36+00:00
- load1 2.69 read 2026-10-08T11:11:06+00:00
- load1 2.52 read 2026-10-08T11:11:36+00:00
- load1 2.16 read 2026-10-08T11:12:06+00:00
- load1 2.49 read 2026-10-08T11:12:36+00:00
- load1 5.22 read 2026-10-08T11:13:06+00:00
- load1 3.73 read 2026-10-08T11:13:36+00:00
- load1 3.26 read 2026-10-08T11:14:06+00:00
- load1 4.92 read 2026-10-08T11:14:36+00:00
- load1 4.52 read 2026-10-08T11:15:06+00:00
- load1 3.47 read 2026-10-08T11:15:36+00:00
- load1 3.49 read 2026-10-08T11:16:06+00:00
- release: non-decisive after 900 s (31 readings)

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 24 | 24 | 0 | 0 | 0 | 0 | +1.492e-05 | -4.227e-05 | 339808 | 16990484 | 24877521 | 0.66 | 2613515 | 0 |
| M2.5 | 24 | 24 | 0 | 0 | 0 | 0 | +1.315e-05 | -4.228e-05 | 417022 | 20851184 | 30559238 | 0.72 | 2912578 | 0 |
| M3 | 24 | 24 | 0 | 0 | 0 | 0 | +1.032e-05 | -4.230e-05 | 550460 | 27523084 | 40571158 | 1.04 | 3193587 | 0 |
| M6 | 24 | 24 | 0 | 0 | 0 | 0 | +8.409e-06 | +1.504e-05 | 792016 | 39600884 | 58468682 | 1.42 | 3570200 | 0 |
| M8 | 24 | 24 | 0 | 0 | 0 | 0 | +1.091e-05 | +7.334e-05 | 1075998 | 53799984 | 79618132 | 1.59 | 3840361 | 1 |
| M10 | 24 | 24 | 0 | 0 | 0 | 0 | +1.156e-05 | +4.526e-05 | 1617392 | 80869684 | 118560997 | 2.28 | 3994621 | 5 |
| M16 | 24 | 24 | 0 | 0 | 0 | 0 | +1.479e-05 | +4.504e-05 | 3401772 | 170088684 | 251181247 | 6.68 | 4866050 | 6 |
| M20 | 24 | 24 | 0 | 0 | 0 | 0 | +1.147e-06 | -4.229e-06 | 3781796 | 189089884 | 279090458 | 6.84 | 5569643 | 8 |

- M8 right L=80 rod: over budget: fine raw + gzip-1 79618132 bytes > 67108864
- M8 right L=80 rod: over budget: fine raw + gzip-1 67678940 bytes > 67108864
- M10 right L=100 rod: over budget: fine raw + gzip-1 118560997 bytes > 67108864
- M10 left L=100 rod: over budget: fine raw + gzip-1 92186917 bytes > 67108864
- M10 right L=100 rod: over budget: fine raw + gzip-1 104774303 bytes > 67108864
- M10 left L=100 rod: over budget: fine raw + gzip-1 77049495 bytes > 67108864
- M10 right L=100 rod: over budget: fine raw + gzip-1 98619341 bytes > 67108864
- M10 left L=100 rod: over budget: fine raw + gzip-1 70904448 bytes > 67108864
- M16 right L=160 rod: over budget: fine raw + gzip-1 200304425 bytes > 67108864
- M16 left L=160 rod: over budget: fine raw + gzip-1 142616156 bytes > 67108864
- M16 right L=160 rod: over budget: fine raw + gzip-1 226174645 bytes > 67108864
- M16 left L=160 rod: over budget: fine raw + gzip-1 161765376 bytes > 67108864
- M16 right L=160 rod: over budget: fine raw + gzip-1 251181247 bytes > 67108864
- M16 left L=160 rod: over budget: fine raw + gzip-1 185076523 bytes > 67108864
- M20 right L=200 rod: over budget: fine raw + gzip-1 211134421 bytes > 67108864
- M20 left L=200 rod: over budget: fine raw + gzip-1 147962487 bytes > 67108864
- M20 right L=200 rod: over budget: fine raw + gzip-1 237498134 bytes > 67108864
- M20 left L=200 rod: over budget: fine raw + gzip-1 172932968 bytes > 67108864
- M20 right L=200 rod: over budget: fine raw + gzip-1 279090458 bytes > 67108864
- M20 left L=200 rod: over budget: fine raw + gzip-1 227206152 bytes > 67108864
- load1 9.68 read 2026-10-08T11:26:43+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The output lists 24 rows per size for the eight sizes M2 to M20 (K swept over 3, 5 and 10), every row class ok, and no silent_wrong, failure, timeout or worker_died row. The quiet gate did not release (non-decisive after 900 s, 31 readings), so the seconds columns are recorded but are not established timings. The output lists the rows over the 67108864-byte budget for M8 to M20. Which K the campaign selected is in the campaign entry below, not in this block.


### 2026-10-08-a-grid

Run window (UTC): 2026-10-08T11:26:45+00:00 (first gate reading) to 2026-10-08T15:33:58+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: non-decisive after 900 s (31 readings). Gate readings: 31; first load1 9.07 read 2026-10-08T11:26:45+00:00; last load1 3.68 read 2026-10-08T11:41:45+00:00. Every reading is in the output below.
End reading: load1 8.92 read 2026-10-08T15:33:58+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-grid.jsonl` — 7161 lines, sha256 365b059f3f54036b663c7898b3041c25d80a7c439cc03131f03999b5f3e947bb. Markdown output: `bench/results/thread-spike/2026-10-08-a-grid.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-grid

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: grid
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 9.07 read 2026-10-08T11:26:45+00:00
- load1 7.20 read 2026-10-08T11:27:15+00:00
- load1 7.17 read 2026-10-08T11:27:45+00:00
- load1 5.33 read 2026-10-08T11:28:15+00:00
- load1 4.71 read 2026-10-08T11:28:45+00:00
- load1 4.39 read 2026-10-08T11:29:15+00:00
- load1 4.76 read 2026-10-08T11:29:45+00:00
- load1 4.37 read 2026-10-08T11:30:15+00:00
- load1 3.94 read 2026-10-08T11:30:45+00:00
- load1 3.38 read 2026-10-08T11:31:15+00:00
- load1 3.44 read 2026-10-08T11:31:45+00:00
- load1 10.87 read 2026-10-08T11:32:15+00:00
- load1 7.93 read 2026-10-08T11:32:45+00:00
- load1 7.28 read 2026-10-08T11:33:15+00:00
- load1 7.89 read 2026-10-08T11:33:45+00:00
- load1 13.10 read 2026-10-08T11:34:15+00:00
- load1 10.02 read 2026-10-08T11:34:45+00:00
- load1 7.29 read 2026-10-08T11:35:15+00:00
- load1 5.43 read 2026-10-08T11:35:45+00:00
- load1 6.12 read 2026-10-08T11:36:15+00:00
- load1 13.69 read 2026-10-08T11:36:45+00:00
- load1 12.46 read 2026-10-08T11:37:15+00:00
- load1 8.25 read 2026-10-08T11:37:45+00:00
- load1 5.82 read 2026-10-08T11:38:15+00:00
- load1 4.38 read 2026-10-08T11:38:45+00:00
- load1 8.40 read 2026-10-08T11:39:15+00:00
- load1 6.41 read 2026-10-08T11:39:45+00:00
- load1 4.66 read 2026-10-08T11:40:15+00:00
- load1 3.37 read 2026-10-08T11:40:45+00:00
- load1 3.48 read 2026-10-08T11:41:15+00:00
- load1 3.68 read 2026-10-08T11:41:45+00:00
- release: non-decisive after 900 s (31 readings)

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 240 | 240 | 0 | 0 | 0 | 0 | -8.147e-06 | -1.309e-05 | 305432 | 15271684 | 22296145 | 0.34 | 2613519 | 0 |
| M2.5 | 312 | 312 | 0 | 0 | 0 | 0 | -7.586e-06 | -1.308e-05 | 411140 | 20557084 | 30196865 | 0.64 | 2912582 | 0 |
| M3 | 240 | 240 | 0 | 0 | 0 | 0 | -7.301e-06 | -1.307e-05 | 450704 | 22535284 | 33169558 | 0.48 | 3193589 | 0 |
| M3.5 | 328 | 328 | 0 | 0 | 0 | 0 | -6.920e-06 | -8.620e-06 | 449598 | 22479984 | 33063505 | 0.94 | 3112318 | 0 |
| M4 | 368 | 368 | 0 | 0 | 0 | 0 | -4.100e-06 | -8.805e-06 | 533096 | 26654884 | 39011328 | 0.74 | 3441224 | 0 |
| M5 | 400 | 400 | 0 | 0 | 0 | 0 | +1.708e-06 | -3.070e-06 | 598016 | 29900884 | 43751764 | 1.24 | 3702044 | 0 |
| M6 | 240 | 240 | 0 | 0 | 0 | 0 | +1.357e-06 | +1.806e-06 | 604344 | 30217284 | 44188214 | 0.84 | 3570204 | 0 |
| M7 | 280 | 280 | 0 | 0 | 0 | 0 | +1.299e-06 | +1.732e-06 | 738280 | 36914084 | 54163228 | 1.60 | 4170228 | 0 |
| M8 | 512 | 512 | 0 | 0 | 0 | 0 | +1.369e-06 | -2.572e-06 | 1075998 | 53799984 | 79618132 | 3.29 | 3840365 | 9 |
| M10 | 532 | 532 | 0 | 0 | 0 | 0 | +1.232e-06 | -1.911e-06 | 1617392 | 80869684 | 118560997 | 4.66 | 3612050 | 76 |
| M12 | 684 | 684 | 0 | 0 | 0 | 0 | +1.230e-06 | -2.311e-06 | 1808452 | 90422684 | 132507506 | 3.49 | 4119725 | 127 |
| M14 | 560 | 560 | 0 | 0 | 0 | 0 | +1.020e-06 | -2.472e-06 | 2199490 | 109974584 | 160586533 | 2.78 | 4270225 | 131 |
| M16 | 640 | 640 | 0 | 0 | 0 | 0 | +1.014e-06 | -2.491e-06 | 2751566 | 137578384 | 200304425 | 2.44 | 4866054 | 180 |
| M18 | 864 | 864 | 0 | 0 | 0 | 0 | +1.019e-06 | -1.519e-06 | 2478116 | 123905884 | 180733808 | 2.04 | 4415353 | 225 |
| M20 | 960 | 960 | 0 | 0 | 0 | 0 | +1.014e-06 | -1.529e-06 | 2898882 | 144944184 | 211134421 | 6.90 | 4917817 | 277 |

- M8 right L=68 rod: over budget: fine raw + gzip-1 67575320 bytes > 67108864
- M8 right L=68.75 rod: over budget: fine raw + gzip-1 68446934 bytes > 67108864
- M8 right L=69 rod: over budget: fine raw + gzip-1 68599883 bytes > 67108864
- M8 right L=70 rod: over budget: fine raw + gzip-1 69289487 bytes > 67108864
- M8 right L=71 rod: over budget: fine raw + gzip-1 69473437 bytes > 67108864
- M8 right L=71.25 rod: over budget: fine raw + gzip-1 70761920 bytes > 67108864
- M8 right L=72 rod: over budget: fine raw + gzip-1 71431328 bytes > 67108864
- M8 right L=72.5 rod: over budget: fine raw + gzip-1 72169715 bytes > 67108864
- M8 right L=73 rod: over budget: fine raw + gzip-1 71973355 bytes > 67108864
- M8 right L=73.75 rod: over budget: fine raw + gzip-1 73009820 bytes > 67108864
- M8 right L=74 rod: over budget: fine raw + gzip-1 72966894 bytes > 67108864
- M8 right L=75 rod: over budget: fine raw + gzip-1 74487144 bytes > 67108864
- M8 right L=76 rod: over budget: fine raw + gzip-1 75304290 bytes > 67108864
- M8 right L=76.25 rod: over budget: fine raw + gzip-1 75897526 bytes > 67108864
- M8 right L=77 rod: over budget: fine raw + gzip-1 76772853 bytes > 67108864
- M8 right L=77.5 rod: over budget: fine raw + gzip-1 76737795 bytes > 67108864
- M8 right L=78 rod: over budget: fine raw + gzip-1 76712296 bytes > 67108864
- M8 right L=78.75 rod: over budget: fine raw + gzip-1 78208704 bytes > 67108864
- M8 right L=79 rod: over budget: fine raw + gzip-1 78458002 bytes > 67108864
- M8 right L=80 rod: over budget: fine raw + gzip-1 79618132 bytes > 67108864
- M10 right L=57 rod: over budget: fine raw + gzip-1 67426226 bytes > 67108864
- M10 right L=58 rod: over budget: fine raw + gzip-1 68753799 bytes > 67108864
- M10 right L=58.5 rod: over budget: fine raw + gzip-1 69389448 bytes > 67108864
- M10 right L=59 rod: over budget: fine raw + gzip-1 69979548 bytes > 67108864
- M10 right L=60 rod: over budget: fine raw + gzip-1 71198991 bytes > 67108864
- M10 right L=61 rod: over budget: fine raw + gzip-1 72004283 bytes > 67108864
- M10 right L=61.5 rod: over budget: fine raw + gzip-1 72761398 bytes > 67108864
- M10 right L=62 rod: over budget: fine raw + gzip-1 73219898 bytes > 67108864
- M10 right L=63 rod: over budget: fine raw + gzip-1 74719572 bytes > 67108864
- M10 right L=64 rod: over budget: fine raw + gzip-1 75901892 bytes > 67108864
- M10 right L=64.5 rod: over budget: fine raw + gzip-1 76521049 bytes > 67108864
- M10 right L=65 rod: over budget: fine raw + gzip-1 77079457 bytes > 67108864
- M10 right L=66 rod: over budget: fine raw + gzip-1 78090626 bytes > 67108864
- M10 right L=67 rod: over budget: fine raw + gzip-1 79415985 bytes > 67108864
- M10 right L=67.5 rod: over budget: fine raw + gzip-1 80054369 bytes > 67108864
- M10 right L=68 rod: over budget: fine raw + gzip-1 80645215 bytes > 67108864
- M10 right L=69 rod: over budget: fine raw + gzip-1 81861519 bytes > 67108864
- M10 right L=70 rod: over budget: fine raw + gzip-1 82664654 bytes > 67108864
- M10 right L=70.5 rod: over budget: fine raw + gzip-1 83426887 bytes > 67108864
- M10 right L=71 rod: over budget: fine raw + gzip-1 83884794 bytes > 67108864
- M10 right L=72 rod: over budget: fine raw + gzip-1 85389187 bytes > 67108864
- M10 right L=73 rod: over budget: fine raw + gzip-1 86568037 bytes > 67108864
- M10 left L=73 rod: over budget: fine raw + gzip-1 67317113 bytes > 67108864
- M10 right L=73.5 rod: over budget: fine raw + gzip-1 87197342 bytes > 67108864
- M10 left L=73.5 rod: over budget: fine raw + gzip-1 67854428 bytes > 67108864
- M10 right L=74 rod: over budget: fine raw + gzip-1 87747951 bytes > 67108864
- M10 left L=74 rod: over budget: fine raw + gzip-1 68238586 bytes > 67108864
- M10 right L=75 rod: over budget: fine raw + gzip-1 88762262 bytes > 67108864
- M10 left L=75 rod: over budget: fine raw + gzip-1 68770178 bytes > 67108864
- M10 right L=76 rod: over budget: fine raw + gzip-1 90085161 bytes > 67108864
- M10 left L=76 rod: over budget: fine raw + gzip-1 70106002 bytes > 67108864
- M10 right L=76.5 rod: over budget: fine raw + gzip-1 90723874 bytes > 67108864
- M10 left L=76.5 rod: over budget: fine raw + gzip-1 70500950 bytes > 67108864
- M10 right L=77 rod: over budget: fine raw + gzip-1 91315609 bytes > 67108864
- M10 left L=77 rod: over budget: fine raw + gzip-1 71009802 bytes > 67108864
- M10 right L=78 rod: over budget: fine raw + gzip-1 92532256 bytes > 67108864
- M10 left L=78 rod: over budget: fine raw + gzip-1 72007268 bytes > 67108864
- M10 right L=79 rod: over budget: fine raw + gzip-1 93334219 bytes > 67108864
- M10 left L=79 rod: over budget: fine raw + gzip-1 72569995 bytes > 67108864
- M10 right L=79.5 rod: over budget: fine raw + gzip-1 94097030 bytes > 67108864
- M10 left L=79.5 rod: over budget: fine raw + gzip-1 72919091 bytes > 67108864
- M10 right L=80 rod: over budget: fine raw + gzip-1 94554351 bytes > 67108864
- M10 left L=80 rod: over budget: fine raw + gzip-1 73278753 bytes > 67108864
- M10 right L=81 rod: over budget: fine raw + gzip-1 96058616 bytes > 67108864
- M10 left L=81 rod: over budget: fine raw + gzip-1 74649896 bytes > 67108864
- M10 right L=82 rod: over budget: fine raw + gzip-1 97240315 bytes > 67108864
- M10 left L=82 rod: over budget: fine raw + gzip-1 75608822 bytes > 67108864
- M10 right L=82.5 rod: over budget: fine raw + gzip-1 97868605 bytes > 67108864
- M10 left L=82.5 rod: over budget: fine raw + gzip-1 76147695 bytes > 67108864
- M10 right L=83 rod: over budget: fine raw + gzip-1 98417430 bytes > 67108864
- M10 left L=83 rod: over budget: fine raw + gzip-1 76536329 bytes > 67108864
- M10 right L=84 rod: over budget: fine raw + gzip-1 99431209 bytes > 67108864
- M10 left L=84 rod: over budget: fine raw + gzip-1 77068035 bytes > 67108864
- M10 right L=85 rod: over budget: fine raw + gzip-1 100754182 bytes > 67108864
- M10 left L=85 rod: over budget: fine raw + gzip-1 78400437 bytes > 67108864
- M10 right L=85.5 rod: over budget: fine raw + gzip-1 101388339 bytes > 67108864
- M10 left L=85.5 rod: over budget: fine raw + gzip-1 78796761 bytes > 67108864
- M10 right L=86 rod: over budget: fine raw + gzip-1 101979532 bytes > 67108864
- M10 left L=86 rod: over budget: fine raw + gzip-1 79304491 bytes > 67108864
- M10 right L=87 rod: over budget: fine raw + gzip-1 103198818 bytes > 67108864
- M10 left L=87 rod: over budget: fine raw + gzip-1 80294917 bytes > 67108864
- M10 right L=88 rod: over budget: fine raw + gzip-1 103998793 bytes > 67108864
- M10 left L=88 rod: over budget: fine raw + gzip-1 80866353 bytes > 67108864
- M10 right L=88.5 rod: over budget: fine raw + gzip-1 104756639 bytes > 67108864
- M10 left L=88.5 rod: over budget: fine raw + gzip-1 81213095 bytes > 67108864
- M10 right L=89 rod: over budget: fine raw + gzip-1 105220307 bytes > 67108864
- M10 left L=89 rod: over budget: fine raw + gzip-1 81574041 bytes > 67108864
- M10 right L=90 rod: over budget: fine raw + gzip-1 106722747 bytes > 67108864
- M10 left L=90 rod: over budget: fine raw + gzip-1 82938698 bytes > 67108864
- M10 right L=91 rod: over budget: fine raw + gzip-1 107903608 bytes > 67108864
- M10 left L=91 rod: over budget: fine raw + gzip-1 83898364 bytes > 67108864
- M10 right L=91.5 rod: over budget: fine raw + gzip-1 108531129 bytes > 67108864
- M10 left L=91.5 rod: over budget: fine raw + gzip-1 84438526 bytes > 67108864
- M10 right L=92 rod: over budget: fine raw + gzip-1 109081886 bytes > 67108864
- M10 left L=92 rod: over budget: fine raw + gzip-1 84823461 bytes > 67108864
- M10 right L=93 rod: over budget: fine raw + gzip-1 110093310 bytes > 67108864
- M10 left L=93 rod: over budget: fine raw + gzip-1 85355816 bytes > 67108864
- M10 right L=94 rod: over budget: fine raw + gzip-1 111419702 bytes > 67108864
- M10 left L=94 rod: over budget: fine raw + gzip-1 86690264 bytes > 67108864
- M10 right L=94.5 rod: over budget: fine raw + gzip-1 112057384 bytes > 67108864
- M10 left L=94.5 rod: over budget: fine raw + gzip-1 87084842 bytes > 67108864
- M10 right L=95 rod: over budget: fine raw + gzip-1 112648217 bytes > 67108864
- M10 left L=95 rod: over budget: fine raw + gzip-1 87591878 bytes > 67108864
- M10 right L=96 rod: over budget: fine raw + gzip-1 113866743 bytes > 67108864
- M10 left L=96 rod: over budget: fine raw + gzip-1 88582118 bytes > 67108864
- M10 right L=97 rod: over budget: fine raw + gzip-1 114705278 bytes > 67108864
- M10 left L=97 rod: over budget: fine raw + gzip-1 89154347 bytes > 67108864
- M10 right L=97.5 rod: over budget: fine raw + gzip-1 115426867 bytes > 67108864
- M10 left L=97.5 rod: over budget: fine raw + gzip-1 89499417 bytes > 67108864
- M10 right L=98 rod: over budget: fine raw + gzip-1 115882790 bytes > 67108864
- M10 left L=98 rod: over budget: fine raw + gzip-1 89902436 bytes > 67108864
- M10 right L=99 rod: over budget: fine raw + gzip-1 117391392 bytes > 67108864
- M10 left L=99 rod: over budget: fine raw + gzip-1 91233738 bytes > 67108864
- M10 right L=100 rod: over budget: fine raw + gzip-1 118560997 bytes > 67108864
- M10 left L=100 rod: over budget: fine raw + gzip-1 92186917 bytes > 67108864
- M12 right L=61 rod: over budget: fine raw + gzip-1 67181228 bytes > 67108864
- M12 right L=61.25 rod: over budget: fine raw + gzip-1 67325279 bytes > 67108864
- M12 right L=62 rod: over budget: fine raw + gzip-1 68685617 bytes > 67108864
- M12 right L=63 rod: over budget: fine raw + gzip-1 69197472 bytes > 67108864
- M12 right L=64 rod: over budget: fine raw + gzip-1 70347793 bytes > 67108864
- M12 right L=64.75 rod: over budget: fine raw + gzip-1 71426144 bytes > 67108864
- M12 right L=65 rod: over budget: fine raw + gzip-1 71513256 bytes > 67108864
- M12 right L=66 rod: over budget: fine raw + gzip-1 72834937 bytes > 67108864
- M12 right L=66.5 rod: over budget: fine raw + gzip-1 73089039 bytes > 67108864
- M12 right L=67 rod: over budget: fine raw + gzip-1 73517274 bytes > 67108864
- M12 right L=68 rod: over budget: fine raw + gzip-1 74967697 bytes > 67108864
- M12 right L=68.25 rod: over budget: fine raw + gzip-1 74960035 bytes > 67108864
- M12 right L=69 rod: over budget: fine raw + gzip-1 75840486 bytes > 67108864
- M12 right L=70 rod: over budget: fine raw + gzip-1 77182699 bytes > 67108864
- M12 right L=71 rod: over budget: fine raw + gzip-1 78095973 bytes > 67108864
- M12 right L=71.75 rod: over budget: fine raw + gzip-1 78851867 bytes > 67108864
- M12 right L=72 rod: over budget: fine raw + gzip-1 79083438 bytes > 67108864
- M12 right L=73 rod: over budget: fine raw + gzip-1 80699656 bytes > 67108864
- M12 right L=73.5 rod: over budget: fine raw + gzip-1 80720101 bytes > 67108864
- M12 right L=74 rod: over budget: fine raw + gzip-1 81335494 bytes > 67108864
- M12 right L=75 rod: over budget: fine raw + gzip-1 82616307 bytes > 67108864
- M12 right L=75.25 rod: over budget: fine raw + gzip-1 82940439 bytes > 67108864
- M12 right L=76 rod: over budget: fine raw + gzip-1 83620426 bytes > 67108864
- M12 right L=77 rod: over budget: fine raw + gzip-1 84613098 bytes > 67108864
- M12 right L=78 rod: over budget: fine raw + gzip-1 86426989 bytes > 67108864
- M12 left L=78 rod: over budget: fine raw + gzip-1 68536506 bytes > 67108864
- M12 right L=78.75 rod: over budget: fine raw + gzip-1 86482768 bytes > 67108864
- M12 left L=78.75 rod: over budget: fine raw + gzip-1 68666589 bytes > 67108864
- M12 right L=79 rod: over budget: fine raw + gzip-1 86806287 bytes > 67108864
- M12 left L=79 rod: over budget: fine raw + gzip-1 68936133 bytes > 67108864
- M12 right L=80 rod: over budget: fine raw + gzip-1 88106869 bytes > 67108864
- M12 left L=80 rod: over budget: fine raw + gzip-1 70165540 bytes > 67108864
- M12 right L=80.5 rod: over budget: fine raw + gzip-1 88705525 bytes > 67108864
- M12 left L=80.5 rod: over budget: fine raw + gzip-1 70432877 bytes > 67108864
- M12 right L=81 rod: over budget: fine raw + gzip-1 89350333 bytes > 67108864
- M12 left L=81 rod: over budget: fine raw + gzip-1 70862717 bytes > 67108864
- M12 right L=82 rod: over budget: fine raw + gzip-1 90251045 bytes > 67108864
- M12 left L=82 rod: over budget: fine raw + gzip-1 71341115 bytes > 67108864
- M12 right L=82.25 rod: over budget: fine raw + gzip-1 90377653 bytes > 67108864
- M12 left L=82.25 rod: over budget: fine raw + gzip-1 71442741 bytes > 67108864
- M12 right L=83 rod: over budget: fine raw + gzip-1 91728872 bytes > 67108864
- M12 left L=83 rod: over budget: fine raw + gzip-1 72839041 bytes > 67108864
- M12 right L=84 rod: over budget: fine raw + gzip-1 92245551 bytes > 67108864
- M12 left L=84 rod: over budget: fine raw + gzip-1 73238450 bytes > 67108864
- M12 right L=85 rod: over budget: fine raw + gzip-1 93395779 bytes > 67108864
- M12 left L=85 rod: over budget: fine raw + gzip-1 74195608 bytes > 67108864
- M12 right L=85.75 rod: over budget: fine raw + gzip-1 94466524 bytes > 67108864
- M12 left L=85.75 rod: over budget: fine raw + gzip-1 74999092 bytes > 67108864
- M12 right L=86 rod: over budget: fine raw + gzip-1 94560823 bytes > 67108864
- M12 left L=86 rod: over budget: fine raw + gzip-1 75060307 bytes > 67108864
- M12 right L=87 rod: over budget: fine raw + gzip-1 95880790 bytes > 67108864
- M12 left L=87 rod: over budget: fine raw + gzip-1 75797114 bytes > 67108864
- M12 right L=87.5 rod: over budget: fine raw + gzip-1 96138930 bytes > 67108864
- M12 left L=87.5 rod: over budget: fine raw + gzip-1 76014037 bytes > 67108864
- M12 right L=88 rod: over budget: fine raw + gzip-1 96566536 bytes > 67108864
- M12 left L=88 rod: over budget: fine raw + gzip-1 76517166 bytes > 67108864
- M12 right L=89 rod: over budget: fine raw + gzip-1 98016382 bytes > 67108864
- M12 left L=89 rod: over budget: fine raw + gzip-1 77746904 bytes > 67108864
- M12 right L=89.25 rod: over budget: fine raw + gzip-1 98005660 bytes > 67108864
- M12 left L=89.25 rod: over budget: fine raw + gzip-1 77810244 bytes > 67108864
- M12 right L=90 rod: over budget: fine raw + gzip-1 98888228 bytes > 67108864
- M12 left L=90 rod: over budget: fine raw + gzip-1 78544913 bytes > 67108864
- M12 right L=91 rod: over budget: fine raw + gzip-1 100228177 bytes > 67108864
- M12 left L=91 rod: over budget: fine raw + gzip-1 79576133 bytes > 67108864
- M12 right L=92 rod: over budget: fine raw + gzip-1 101141522 bytes > 67108864
- M12 left L=92 rod: over budget: fine raw + gzip-1 80236193 bytes > 67108864
- M12 right L=92.75 rod: over budget: fine raw + gzip-1 101899111 bytes > 67108864
- M12 left L=92.75 rod: over budget: fine raw + gzip-1 80587329 bytes > 67108864
- M12 right L=93 rod: over budget: fine raw + gzip-1 102129226 bytes > 67108864
- M12 left L=93 rod: over budget: fine raw + gzip-1 80823008 bytes > 67108864
- M12 right L=94 rod: over budget: fine raw + gzip-1 103746085 bytes > 67108864
- M12 left L=94 rod: over budget: fine raw + gzip-1 82303130 bytes > 67108864
- M12 right L=94.5 rod: over budget: fine raw + gzip-1 103771157 bytes > 67108864
- M12 left L=94.5 rod: over budget: fine raw + gzip-1 82381219 bytes > 67108864
- M12 right L=95 rod: over budget: fine raw + gzip-1 104386444 bytes > 67108864
- M12 left L=95 rod: over budget: fine raw + gzip-1 82899651 bytes > 67108864
- M12 right L=96 rod: over budget: fine raw + gzip-1 105662782 bytes > 67108864
- M12 left L=96 rod: over budget: fine raw + gzip-1 83971379 bytes > 67108864
- M12 right L=96.25 rod: over budget: fine raw + gzip-1 105992606 bytes > 67108864
- M12 left L=96.25 rod: over budget: fine raw + gzip-1 84144863 bytes > 67108864
- M12 right L=97 rod: over budget: fine raw + gzip-1 106669442 bytes > 67108864
- M12 left L=97 rod: over budget: fine raw + gzip-1 84643468 bytes > 67108864
- M12 right L=98 rod: over budget: fine raw + gzip-1 107662048 bytes > 67108864
- M12 left L=98 rod: over budget: fine raw + gzip-1 85154221 bytes > 67108864
- M12 right L=99 rod: over budget: fine raw + gzip-1 109474680 bytes > 67108864
- M12 left L=99 rod: over budget: fine raw + gzip-1 86823077 bytes > 67108864
- M12 right L=99.75 rod: over budget: fine raw + gzip-1 109535943 bytes > 67108864
- M12 left L=99.75 rod: over budget: fine raw + gzip-1 86952444 bytes > 67108864
- M12 right L=100 rod: over budget: fine raw + gzip-1 109859611 bytes > 67108864
- M12 left L=100 rod: over budget: fine raw + gzip-1 87221962 bytes > 67108864
- M12 right L=101 rod: over budget: fine raw + gzip-1 111159888 bytes > 67108864
- M12 left L=101 rod: over budget: fine raw + gzip-1 88452315 bytes > 67108864
- M12 right L=101.5 rod: over budget: fine raw + gzip-1 111752048 bytes > 67108864
- M12 left L=101.5 rod: over budget: fine raw + gzip-1 88718846 bytes > 67108864
- M12 right L=102 rod: over budget: fine raw + gzip-1 112403545 bytes > 67108864
- M12 left L=102 rod: over budget: fine raw + gzip-1 89153070 bytes > 67108864
- M12 right L=103 rod: over budget: fine raw + gzip-1 113306222 bytes > 67108864
- M12 left L=103 rod: over budget: fine raw + gzip-1 89632204 bytes > 67108864
- M12 right L=103.25 rod: over budget: fine raw + gzip-1 113429843 bytes > 67108864
- M12 left L=103.25 rod: over budget: fine raw + gzip-1 89727346 bytes > 67108864
- M12 right L=104 rod: over budget: fine raw + gzip-1 114786949 bytes > 67108864
- M12 left L=104 rod: over budget: fine raw + gzip-1 91123942 bytes > 67108864
- M12 right L=105 rod: over budget: fine raw + gzip-1 115299676 bytes > 67108864
- M12 left L=105 rod: over budget: fine raw + gzip-1 91524454 bytes > 67108864
- M12 right L=106 rod: over budget: fine raw + gzip-1 116447420 bytes > 67108864
- M12 left L=106 rod: over budget: fine raw + gzip-1 92481738 bytes > 67108864
- M12 right L=106.75 rod: over budget: fine raw + gzip-1 117522152 bytes > 67108864
- M12 left L=106.75 rod: over budget: fine raw + gzip-1 93285708 bytes > 67108864
- M12 right L=107 rod: over budget: fine raw + gzip-1 117614301 bytes > 67108864
- M12 left L=107 rod: over budget: fine raw + gzip-1 93344692 bytes > 67108864
- M12 right L=108 rod: over budget: fine raw + gzip-1 118934339 bytes > 67108864
- M12 left L=108 rod: over budget: fine raw + gzip-1 94082870 bytes > 67108864
- M12 right L=108.5 rod: over budget: fine raw + gzip-1 119191742 bytes > 67108864
- M12 left L=108.5 rod: over budget: fine raw + gzip-1 94297907 bytes > 67108864
- M12 right L=109 rod: over budget: fine raw + gzip-1 119620811 bytes > 67108864
- M12 left L=109 rod: over budget: fine raw + gzip-1 94803459 bytes > 67108864
- M12 right L=110 rod: over budget: fine raw + gzip-1 121069852 bytes > 67108864
- M12 left L=110 rod: over budget: fine raw + gzip-1 96026520 bytes > 67108864
- M12 right L=110.25 rod: over budget: fine raw + gzip-1 121056127 bytes > 67108864
- M12 left L=110.25 rod: over budget: fine raw + gzip-1 96104286 bytes > 67108864
- M12 right L=111 rod: over budget: fine raw + gzip-1 121937756 bytes > 67108864
- M12 left L=111 rod: over budget: fine raw + gzip-1 96839107 bytes > 67108864
- M12 right L=112 rod: over budget: fine raw + gzip-1 123278629 bytes > 67108864
- M12 left L=112 rod: over budget: fine raw + gzip-1 97865634 bytes > 67108864
- M12 right L=113 rod: over budget: fine raw + gzip-1 124192076 bytes > 67108864
- M12 left L=113 rod: over budget: fine raw + gzip-1 98534709 bytes > 67108864
- M12 right L=113.75 rod: over budget: fine raw + gzip-1 124951281 bytes > 67108864
- M12 left L=113.75 rod: over budget: fine raw + gzip-1 98880035 bytes > 67108864
- M12 right L=114 rod: over budget: fine raw + gzip-1 125140956 bytes > 67108864
- M12 left L=114 rod: over budget: fine raw + gzip-1 99118768 bytes > 67108864
- M12 right L=115 rod: over budget: fine raw + gzip-1 126681796 bytes > 67108864
- M12 left L=115 rod: over budget: fine raw + gzip-1 100553143 bytes > 67108864
- M12 right L=115.5 rod: over budget: fine raw + gzip-1 126816313 bytes > 67108864
- M12 left L=115.5 rod: over budget: fine raw + gzip-1 100682928 bytes > 67108864
- M12 right L=116 rod: over budget: fine raw + gzip-1 127425575 bytes > 67108864
- M12 left L=116 rod: over budget: fine raw + gzip-1 101215787 bytes > 67108864
- M12 right L=117 rod: over budget: fine raw + gzip-1 128716147 bytes > 67108864
- M12 left L=117 rod: over budget: fine raw + gzip-1 102260882 bytes > 67108864
- M12 right L=117.25 rod: over budget: fine raw + gzip-1 129037357 bytes > 67108864
- M12 left L=117.25 rod: over budget: fine raw + gzip-1 102449494 bytes > 67108864
- M12 right L=118 rod: over budget: fine raw + gzip-1 129717187 bytes > 67108864
- M12 left L=118 rod: over budget: fine raw + gzip-1 102949713 bytes > 67108864
- M12 right L=119 rod: over budget: fine raw + gzip-1 130708428 bytes > 67108864
- M12 left L=119 rod: over budget: fine raw + gzip-1 103459165 bytes > 67108864
- M12 right L=120 rod: over budget: fine raw + gzip-1 132507506 bytes > 67108864
- M12 left L=120 rod: over budget: fine raw + gzip-1 105124644 bytes > 67108864
- M14 right L=59 rod: over budget: fine raw + gzip-1 67775474 bytes > 67108864
- M14 right L=60 rod: over budget: fine raw + gzip-1 68785733 bytes > 67108864
- M14 right L=61 rod: over budget: fine raw + gzip-1 69882184 bytes > 67108864
- M14 right L=62 rod: over budget: fine raw + gzip-1 71258720 bytes > 67108864
- M14 right L=63 rod: over budget: fine raw + gzip-1 72337699 bytes > 67108864
- M14 right L=64 rod: over budget: fine raw + gzip-1 72837227 bytes > 67108864
- M14 right L=65 rod: over budget: fine raw + gzip-1 74650329 bytes > 67108864
- M14 right L=66 rod: over budget: fine raw + gzip-1 75660224 bytes > 67108864
- M14 right L=67 rod: over budget: fine raw + gzip-1 76758665 bytes > 67108864
- M14 right L=68 rod: over budget: fine raw + gzip-1 78132446 bytes > 67108864
- M14 right L=69 rod: over budget: fine raw + gzip-1 79205797 bytes > 67108864
- M14 right L=70 rod: over budget: fine raw + gzip-1 79708901 bytes > 67108864
- M14 right L=71 rod: over budget: fine raw + gzip-1 81529367 bytes > 67108864
- M14 right L=72 rod: over budget: fine raw + gzip-1 82534410 bytes > 67108864
- M14 right L=73 rod: over budget: fine raw + gzip-1 83634103 bytes > 67108864
- M14 right L=74 rod: over budget: fine raw + gzip-1 85005567 bytes > 67108864
- M14 right L=75 rod: over budget: fine raw + gzip-1 86078176 bytes > 67108864
- M14 right L=76 rod: over budget: fine raw + gzip-1 86585081 bytes > 67108864
- M14 right L=77 rod: over budget: fine raw + gzip-1 88400915 bytes > 67108864
- M14 right L=78 rod: over budget: fine raw + gzip-1 89407949 bytes > 67108864
- M14 right L=79 rod: over budget: fine raw + gzip-1 90506498 bytes > 67108864
- M14 left L=79 rod: over budget: fine raw + gzip-1 67952096 bytes > 67108864
- M14 right L=80 rod: over budget: fine raw + gzip-1 91876771 bytes > 67108864
- M14 left L=80 rod: over budget: fine raw + gzip-1 69015048 bytes > 67108864
- M14 right L=81 rod: over budget: fine raw + gzip-1 92951008 bytes > 67108864
- M14 left L=81 rod: over budget: fine raw + gzip-1 69637183 bytes > 67108864
- M14 right L=82 rod: over budget: fine raw + gzip-1 93457079 bytes > 67108864
- M14 left L=82 rod: over budget: fine raw + gzip-1 69992038 bytes > 67108864
- M14 right L=83 rod: over budget: fine raw + gzip-1 95275158 bytes > 67108864
- M14 left L=83 rod: over budget: fine raw + gzip-1 71599690 bytes > 67108864
- M14 right L=84 rod: over budget: fine raw + gzip-1 96278071 bytes > 67108864
- M14 left L=84 rod: over budget: fine raw + gzip-1 72200048 bytes > 67108864
- M14 right L=85 rod: over budget: fine raw + gzip-1 97377852 bytes > 67108864
- M14 left L=85 rod: over budget: fine raw + gzip-1 73108598 bytes > 67108864
- M14 right L=86 rod: over budget: fine raw + gzip-1 98749612 bytes > 67108864
- M14 left L=86 rod: over budget: fine raw + gzip-1 74171348 bytes > 67108864
- M14 right L=87 rod: over budget: fine raw + gzip-1 99823615 bytes > 67108864
- M14 left L=87 rod: over budget: fine raw + gzip-1 74800227 bytes > 67108864
- M14 right L=88 rod: over budget: fine raw + gzip-1 100326302 bytes > 67108864
- M14 left L=88 rod: over budget: fine raw + gzip-1 75150155 bytes > 67108864
- M14 right L=89 rod: over budget: fine raw + gzip-1 102145598 bytes > 67108864
- M14 left L=89 rod: over budget: fine raw + gzip-1 76748291 bytes > 67108864
- M14 right L=90 rod: over budget: fine raw + gzip-1 103151128 bytes > 67108864
- M14 left L=90 rod: over budget: fine raw + gzip-1 77362093 bytes > 67108864
- M14 right L=91 rod: over budget: fine raw + gzip-1 104248951 bytes > 67108864
- M14 left L=91 rod: over budget: fine raw + gzip-1 78270120 bytes > 67108864
- M14 right L=92 rod: over budget: fine raw + gzip-1 105621746 bytes > 67108864
- M14 left L=92 rod: over budget: fine raw + gzip-1 79331573 bytes > 67108864
- M14 right L=93 rod: over budget: fine raw + gzip-1 106696254 bytes > 67108864
- M14 left L=93 rod: over budget: fine raw + gzip-1 79955802 bytes > 67108864
- M14 right L=94 rod: over budget: fine raw + gzip-1 107200793 bytes > 67108864
- M14 left L=94 rod: over budget: fine raw + gzip-1 80310197 bytes > 67108864
- M14 right L=95 rod: over budget: fine raw + gzip-1 109015234 bytes > 67108864
- M14 left L=95 rod: over budget: fine raw + gzip-1 81917826 bytes > 67108864
- M14 right L=96 rod: over budget: fine raw + gzip-1 110023256 bytes > 67108864
- M14 left L=96 rod: over budget: fine raw + gzip-1 82523130 bytes > 67108864
- M14 right L=97 rod: over budget: fine raw + gzip-1 111123163 bytes > 67108864
- M14 left L=97 rod: over budget: fine raw + gzip-1 83432589 bytes > 67108864
- M14 right L=98 rod: over budget: fine raw + gzip-1 112496569 bytes > 67108864
- M14 left L=98 rod: over budget: fine raw + gzip-1 84494593 bytes > 67108864
- M14 right L=99 rod: over budget: fine raw + gzip-1 113566420 bytes > 67108864
- M14 left L=99 rod: over budget: fine raw + gzip-1 85117881 bytes > 67108864
- M14 right L=100 rod: over budget: fine raw + gzip-1 114072452 bytes > 67108864
- M14 left L=100 rod: over budget: fine raw + gzip-1 85473912 bytes > 67108864
- M14 right L=101 rod: over budget: fine raw + gzip-1 115891954 bytes > 67108864
- M14 left L=101 rod: over budget: fine raw + gzip-1 87079566 bytes > 67108864
- M14 right L=102 rod: over budget: fine raw + gzip-1 116893379 bytes > 67108864
- M14 left L=102 rod: over budget: fine raw + gzip-1 87685326 bytes > 67108864
- M14 right L=103 rod: over budget: fine raw + gzip-1 117991936 bytes > 67108864
- M14 left L=103 rod: over budget: fine raw + gzip-1 88594298 bytes > 67108864
- M14 right L=104 rod: over budget: fine raw + gzip-1 119364846 bytes > 67108864
- M14 left L=104 rod: over budget: fine raw + gzip-1 89655049 bytes > 67108864
- M14 right L=105 rod: over budget: fine raw + gzip-1 120439213 bytes > 67108864
- M14 left L=105 rod: over budget: fine raw + gzip-1 90284423 bytes > 67108864
- M14 right L=106 rod: over budget: fine raw + gzip-1 120942174 bytes > 67108864
- M14 left L=106 rod: over budget: fine raw + gzip-1 90634919 bytes > 67108864
- M14 right L=107 rod: over budget: fine raw + gzip-1 122762882 bytes > 67108864
- M14 left L=107 rod: over budget: fine raw + gzip-1 92241921 bytes > 67108864
- M14 right L=108 rod: over budget: fine raw + gzip-1 123763531 bytes > 67108864
- M14 left L=108 rod: over budget: fine raw + gzip-1 92844458 bytes > 67108864
- M14 right L=109 rod: over budget: fine raw + gzip-1 124863278 bytes > 67108864
- M14 left L=109 rod: over budget: fine raw + gzip-1 93753547 bytes > 67108864
- M14 right L=110 rod: over budget: fine raw + gzip-1 126234106 bytes > 67108864
- M14 left L=110 rod: over budget: fine raw + gzip-1 94815998 bytes > 67108864
- M14 right L=111 rod: over budget: fine raw + gzip-1 127309164 bytes > 67108864
- M14 left L=111 rod: over budget: fine raw + gzip-1 95437765 bytes > 67108864
- M14 right L=112 rod: over budget: fine raw + gzip-1 127812366 bytes > 67108864
- M14 left L=112 rod: over budget: fine raw + gzip-1 95792405 bytes > 67108864
- M14 right L=113 rod: over budget: fine raw + gzip-1 129632935 bytes > 67108864
- M14 left L=113 rod: over budget: fine raw + gzip-1 97401060 bytes > 67108864
- M14 right L=114 rod: over budget: fine raw + gzip-1 130637762 bytes > 67108864
- M14 left L=114 rod: over budget: fine raw + gzip-1 98001175 bytes > 67108864
- M14 right L=115 rod: over budget: fine raw + gzip-1 131737153 bytes > 67108864
- M14 left L=115 rod: over budget: fine raw + gzip-1 98909245 bytes > 67108864
- M14 right L=116 rod: over budget: fine raw + gzip-1 133110687 bytes > 67108864
- M14 left L=116 rod: over budget: fine raw + gzip-1 99972614 bytes > 67108864
- M14 right L=117 rod: over budget: fine raw + gzip-1 134182890 bytes > 67108864
- M14 left L=117 rod: over budget: fine raw + gzip-1 100602381 bytes > 67108864
- M14 right L=118 rod: over budget: fine raw + gzip-1 134687704 bytes > 67108864
- M14 left L=118 rod: over budget: fine raw + gzip-1 100952228 bytes > 67108864
- M14 right L=119 rod: over budget: fine raw + gzip-1 136504645 bytes > 67108864
- M14 left L=119 rod: over budget: fine raw + gzip-1 102557225 bytes > 67108864
- M14 right L=120 rod: over budget: fine raw + gzip-1 137511576 bytes > 67108864
- M14 left L=120 rod: over budget: fine raw + gzip-1 103162594 bytes > 67108864
- M14 right L=121 rod: over budget: fine raw + gzip-1 138611694 bytes > 67108864
- M14 left L=121 rod: over budget: fine raw + gzip-1 104070554 bytes > 67108864
- M14 right L=122 rod: over budget: fine raw + gzip-1 139984399 bytes > 67108864
- M14 left L=122 rod: over budget: fine raw + gzip-1 105133780 bytes > 67108864
- M14 right L=123 rod: over budget: fine raw + gzip-1 141057543 bytes > 67108864
- M14 left L=123 rod: over budget: fine raw + gzip-1 105755352 bytes > 67108864
- M14 right L=124 rod: over budget: fine raw + gzip-1 141559953 bytes > 67108864
- M14 left L=124 rod: over budget: fine raw + gzip-1 106113442 bytes > 67108864
- M14 right L=125 rod: over budget: fine raw + gzip-1 143378412 bytes > 67108864
- M14 left L=125 rod: over budget: fine raw + gzip-1 107718463 bytes > 67108864
- M14 right L=126 rod: over budget: fine raw + gzip-1 144384325 bytes > 67108864
- M14 left L=126 rod: over budget: fine raw + gzip-1 108321210 bytes > 67108864
- M14 right L=127 rod: over budget: fine raw + gzip-1 145484147 bytes > 67108864
- M14 left L=127 rod: over budget: fine raw + gzip-1 109229175 bytes > 67108864
- M14 right L=128 rod: over budget: fine raw + gzip-1 146855197 bytes > 67108864
- M14 left L=128 rod: over budget: fine raw + gzip-1 110291952 bytes > 67108864
- M14 right L=129 rod: over budget: fine raw + gzip-1 147937785 bytes > 67108864
- M14 left L=129 rod: over budget: fine raw + gzip-1 110920812 bytes > 67108864
- M14 right L=130 rod: over budget: fine raw + gzip-1 148439013 bytes > 67108864
- M14 left L=130 rod: over budget: fine raw + gzip-1 111284709 bytes > 67108864
- M14 right L=131 rod: over budget: fine raw + gzip-1 150248031 bytes > 67108864
- M14 left L=131 rod: over budget: fine raw + gzip-1 112877092 bytes > 67108864
- M14 right L=132 rod: over budget: fine raw + gzip-1 151256040 bytes > 67108864
- M14 left L=132 rod: over budget: fine raw + gzip-1 113479103 bytes > 67108864
- M14 right L=133 rod: over budget: fine raw + gzip-1 152356087 bytes > 67108864
- M14 left L=133 rod: over budget: fine raw + gzip-1 114384447 bytes > 67108864
- M14 right L=134 rod: over budget: fine raw + gzip-1 153721346 bytes > 67108864
- M14 left L=134 rod: over budget: fine raw + gzip-1 115439409 bytes > 67108864
- M14 right L=135 rod: over budget: fine raw + gzip-1 154800229 bytes > 67108864
- M14 left L=135 rod: over budget: fine raw + gzip-1 116078642 bytes > 67108864
- M14 right L=136 rod: over budget: fine raw + gzip-1 155309437 bytes > 67108864
- M14 left L=136 rod: over budget: fine raw + gzip-1 116440650 bytes > 67108864
- M14 right L=137 rod: over budget: fine raw + gzip-1 157119352 bytes > 67108864
- M14 left L=137 rod: over budget: fine raw + gzip-1 118035273 bytes > 67108864
- M14 right L=138 rod: over budget: fine raw + gzip-1 158123044 bytes > 67108864
- M14 left L=138 rod: over budget: fine raw + gzip-1 118630868 bytes > 67108864
- M14 right L=139 rod: over budget: fine raw + gzip-1 159222897 bytes > 67108864
- M14 left L=139 rod: over budget: fine raw + gzip-1 119536170 bytes > 67108864
- M14 right L=140 rod: over budget: fine raw + gzip-1 160586533 bytes > 67108864
- M14 left L=140 rod: over budget: fine raw + gzip-1 120591902 bytes > 67108864
- M16 right L=53 rod: over budget: fine raw + gzip-1 67478936 bytes > 67108864
- M16 right L=54 rod: over budget: fine raw + gzip-1 67966728 bytes > 67108864
- M16 right L=55 rod: over budget: fine raw + gzip-1 69123813 bytes > 67108864
- M16 right L=56 rod: over budget: fine raw + gzip-1 70697984 bytes > 67108864
- M16 right L=57 rod: over budget: fine raw + gzip-1 71674009 bytes > 67108864
- M16 right L=58 rod: over budget: fine raw + gzip-1 72052900 bytes > 67108864
- M16 right L=59 rod: over budget: fine raw + gzip-1 75020229 bytes > 67108864
- M16 right L=60 rod: over budget: fine raw + gzip-1 75512332 bytes > 67108864
- M16 right L=61 rod: over budget: fine raw + gzip-1 76663996 bytes > 67108864
- M16 right L=62 rod: over budget: fine raw + gzip-1 78242138 bytes > 67108864
- M16 right L=63 rod: over budget: fine raw + gzip-1 79215225 bytes > 67108864
- M16 right L=64 rod: over budget: fine raw + gzip-1 79598287 bytes > 67108864
- M16 right L=65 rod: over budget: fine raw + gzip-1 82565371 bytes > 67108864
- M16 right L=66 rod: over budget: fine raw + gzip-1 83055766 bytes > 67108864
- M16 right L=67 rod: over budget: fine raw + gzip-1 84205993 bytes > 67108864
- M16 right L=68 rod: over budget: fine raw + gzip-1 85789308 bytes > 67108864
- M16 right L=69 rod: over budget: fine raw + gzip-1 86756171 bytes > 67108864
- M16 right L=70 rod: over budget: fine raw + gzip-1 87140449 bytes > 67108864
- M16 right L=71 rod: over budget: fine raw + gzip-1 90108736 bytes > 67108864
- M16 right L=72 rod: over budget: fine raw + gzip-1 90600852 bytes > 67108864
- M16 right L=73 rod: over budget: fine raw + gzip-1 91753990 bytes > 67108864
- M16 right L=74 rod: over budget: fine raw + gzip-1 93340110 bytes > 67108864
- M16 right L=75 rod: over budget: fine raw + gzip-1 94305093 bytes > 67108864
- M16 right L=76 rod: over budget: fine raw + gzip-1 94685807 bytes > 67108864
- M16 left L=76 rod: over budget: fine raw + gzip-1 67364502 bytes > 67108864
- M16 right L=77 rod: over budget: fine raw + gzip-1 97658717 bytes > 67108864
- M16 left L=77 rod: over budget: fine raw + gzip-1 69470116 bytes > 67108864
- M16 right L=78 rod: over budget: fine raw + gzip-1 98146718 bytes > 67108864
- M16 left L=78 rod: over budget: fine raw + gzip-1 69740646 bytes > 67108864
- M16 right L=79 rod: over budget: fine raw + gzip-1 99299510 bytes > 67108864
- M16 left L=79 rod: over budget: fine raw + gzip-1 70697339 bytes > 67108864
- M16 right L=80 rod: over budget: fine raw + gzip-1 100882589 bytes > 67108864
- M16 left L=80 rod: over budget: fine raw + gzip-1 71842066 bytes > 67108864
- M16 right L=81 rod: over budget: fine raw + gzip-1 101851086 bytes > 67108864
- M16 left L=81 rod: over budget: fine raw + gzip-1 72412170 bytes > 67108864
- M16 right L=82 rod: over budget: fine raw + gzip-1 102231454 bytes > 67108864
- M16 left L=82 rod: over budget: fine raw + gzip-1 72742328 bytes > 67108864
- M16 right L=83 rod: over budget: fine raw + gzip-1 105202690 bytes > 67108864
- M16 left L=83 rod: over budget: fine raw + gzip-1 74847614 bytes > 67108864
- M16 right L=84 rod: over budget: fine raw + gzip-1 105691415 bytes > 67108864
- M16 left L=84 rod: over budget: fine raw + gzip-1 75118481 bytes > 67108864
- M16 right L=85 rod: over budget: fine raw + gzip-1 106844485 bytes > 67108864
- M16 left L=85 rod: over budget: fine raw + gzip-1 76073554 bytes > 67108864
- M16 right L=86 rod: over budget: fine raw + gzip-1 108426996 bytes > 67108864
- M16 left L=86 rod: over budget: fine raw + gzip-1 77220382 bytes > 67108864
- M16 right L=87 rod: over budget: fine raw + gzip-1 109391034 bytes > 67108864
- M16 left L=87 rod: over budget: fine raw + gzip-1 77789711 bytes > 67108864
- M16 right L=88 rod: over budget: fine raw + gzip-1 109778000 bytes > 67108864
- M16 left L=88 rod: over budget: fine raw + gzip-1 78119609 bytes > 67108864
- M16 right L=89 rod: over budget: fine raw + gzip-1 112746965 bytes > 67108864
- M16 left L=89 rod: over budget: fine raw + gzip-1 80221011 bytes > 67108864
- M16 right L=90 rod: over budget: fine raw + gzip-1 113236037 bytes > 67108864
- M16 left L=90 rod: over budget: fine raw + gzip-1 80490840 bytes > 67108864
- M16 right L=91 rod: over budget: fine raw + gzip-1 114386305 bytes > 67108864
- M16 left L=91 rod: over budget: fine raw + gzip-1 81447767 bytes > 67108864
- M16 right L=92 rod: over budget: fine raw + gzip-1 115972143 bytes > 67108864
- M16 left L=92 rod: over budget: fine raw + gzip-1 82592292 bytes > 67108864
- M16 right L=93 rod: over budget: fine raw + gzip-1 116940501 bytes > 67108864
- M16 left L=93 rod: over budget: fine raw + gzip-1 83161876 bytes > 67108864
- M16 right L=94 rod: over budget: fine raw + gzip-1 117320435 bytes > 67108864
- M16 left L=94 rod: over budget: fine raw + gzip-1 83492859 bytes > 67108864
- M16 right L=95 rod: over budget: fine raw + gzip-1 120294032 bytes > 67108864
- M16 left L=95 rod: over budget: fine raw + gzip-1 85597451 bytes > 67108864
- M16 right L=96 rod: over budget: fine raw + gzip-1 120781088 bytes > 67108864
- M16 left L=96 rod: over budget: fine raw + gzip-1 85867610 bytes > 67108864
- M16 right L=97 rod: over budget: fine raw + gzip-1 121931275 bytes > 67108864
- M16 left L=97 rod: over budget: fine raw + gzip-1 86824205 bytes > 67108864
- M16 right L=98 rod: over budget: fine raw + gzip-1 123516517 bytes > 67108864
- M16 left L=98 rod: over budget: fine raw + gzip-1 87965703 bytes > 67108864
- M16 right L=99 rod: over budget: fine raw + gzip-1 124485290 bytes > 67108864
- M16 left L=99 rod: over budget: fine raw + gzip-1 88538847 bytes > 67108864
- M16 right L=100 rod: over budget: fine raw + gzip-1 124865749 bytes > 67108864
- M16 left L=100 rod: over budget: fine raw + gzip-1 88868673 bytes > 67108864
- M16 right L=101 rod: over budget: fine raw + gzip-1 127836592 bytes > 67108864
- M16 left L=101 rod: over budget: fine raw + gzip-1 90974824 bytes > 67108864
- M16 right L=102 rod: over budget: fine raw + gzip-1 128328545 bytes > 67108864
- M16 left L=102 rod: over budget: fine raw + gzip-1 91245064 bytes > 67108864
- M16 right L=103 rod: over budget: fine raw + gzip-1 129479991 bytes > 67108864
- M16 left L=103 rod: over budget: fine raw + gzip-1 92201564 bytes > 67108864
- M16 right L=104 rod: over budget: fine raw + gzip-1 131064577 bytes > 67108864
- M16 left L=104 rod: over budget: fine raw + gzip-1 93346603 bytes > 67108864
- M16 right L=105 rod: over budget: fine raw + gzip-1 132028529 bytes > 67108864
- M16 left L=105 rod: over budget: fine raw + gzip-1 93916420 bytes > 67108864
- M16 right L=106 rod: over budget: fine raw + gzip-1 132412930 bytes > 67108864
- M16 left L=106 rod: over budget: fine raw + gzip-1 94246727 bytes > 67108864
- M16 right L=107 rod: over budget: fine raw + gzip-1 135384287 bytes > 67108864
- M16 left L=107 rod: over budget: fine raw + gzip-1 96351989 bytes > 67108864
- M16 right L=108 rod: over budget: fine raw + gzip-1 135875098 bytes > 67108864
- M16 left L=108 rod: over budget: fine raw + gzip-1 96622823 bytes > 67108864
- M16 right L=109 rod: over budget: fine raw + gzip-1 137026351 bytes > 67108864
- M16 left L=109 rod: over budget: fine raw + gzip-1 97578988 bytes > 67108864
- M16 right L=110 rod: over budget: fine raw + gzip-1 138610529 bytes > 67108864
- M16 left L=110 rod: over budget: fine raw + gzip-1 98721163 bytes > 67108864
- M16 right L=111 rod: over budget: fine raw + gzip-1 139579486 bytes > 67108864
- M16 left L=111 rod: over budget: fine raw + gzip-1 99294061 bytes > 67108864
- M16 right L=112 rod: over budget: fine raw + gzip-1 139959187 bytes > 67108864
- M16 left L=112 rod: over budget: fine raw + gzip-1 99624649 bytes > 67108864
- M16 right L=113 rod: over budget: fine raw + gzip-1 142930869 bytes > 67108864
- M16 left L=113 rod: over budget: fine raw + gzip-1 101729580 bytes > 67108864
- M16 right L=114 rod: over budget: fine raw + gzip-1 143419622 bytes > 67108864
- M16 left L=114 rod: over budget: fine raw + gzip-1 102000315 bytes > 67108864
- M16 right L=115 rod: over budget: fine raw + gzip-1 144568982 bytes > 67108864
- M16 left L=115 rod: over budget: fine raw + gzip-1 102957080 bytes > 67108864
- M16 right L=116 rod: over budget: fine raw + gzip-1 146155615 bytes > 67108864
- M16 left L=116 rod: over budget: fine raw + gzip-1 104101606 bytes > 67108864
- M16 right L=117 rod: over budget: fine raw + gzip-1 147124251 bytes > 67108864
- M16 left L=117 rod: over budget: fine raw + gzip-1 104671500 bytes > 67108864
- M16 right L=118 rod: over budget: fine raw + gzip-1 147504345 bytes > 67108864
- M16 left L=118 rod: over budget: fine raw + gzip-1 105002426 bytes > 67108864
- M16 right L=119 rod: over budget: fine raw + gzip-1 150475522 bytes > 67108864
- M16 left L=119 rod: over budget: fine raw + gzip-1 107106973 bytes > 67108864
- M16 right L=120 rod: over budget: fine raw + gzip-1 150965302 bytes > 67108864
- M16 left L=120 rod: over budget: fine raw + gzip-1 107377941 bytes > 67108864
- M16 right L=121 rod: over budget: fine raw + gzip-1 152116609 bytes > 67108864
- M16 left L=121 rod: over budget: fine raw + gzip-1 108334286 bytes > 67108864
- M16 right L=122 rod: over budget: fine raw + gzip-1 153700997 bytes > 67108864
- M16 left L=122 rod: over budget: fine raw + gzip-1 109479330 bytes > 67108864
- M16 right L=123 rod: over budget: fine raw + gzip-1 154665277 bytes > 67108864
- M16 left L=123 rod: over budget: fine raw + gzip-1 110048836 bytes > 67108864
- M16 right L=124 rod: over budget: fine raw + gzip-1 155050221 bytes > 67108864
- M16 left L=124 rod: over budget: fine raw + gzip-1 110380075 bytes > 67108864
- M16 right L=125 rod: over budget: fine raw + gzip-1 158017691 bytes > 67108864
- M16 left L=125 rod: over budget: fine raw + gzip-1 112482510 bytes > 67108864
- M16 right L=126 rod: over budget: fine raw + gzip-1 158510831 bytes > 67108864
- M16 left L=126 rod: over budget: fine raw + gzip-1 112750172 bytes > 67108864
- M16 right L=127 rod: over budget: fine raw + gzip-1 159660482 bytes > 67108864
- M16 left L=127 rod: over budget: fine raw + gzip-1 113707212 bytes > 67108864
- M16 right L=128 rod: over budget: fine raw + gzip-1 161246087 bytes > 67108864
- M16 left L=128 rod: over budget: fine raw + gzip-1 114850854 bytes > 67108864
- M16 right L=129 rod: over budget: fine raw + gzip-1 162214479 bytes > 67108864
- M16 left L=129 rod: over budget: fine raw + gzip-1 115423360 bytes > 67108864
- M16 right L=130 rod: over budget: fine raw + gzip-1 162592119 bytes > 67108864
- M16 left L=130 rod: over budget: fine raw + gzip-1 115750493 bytes > 67108864
- M16 right L=131 rod: over budget: fine raw + gzip-1 165565393 bytes > 67108864
- M16 left L=131 rod: over budget: fine raw + gzip-1 117849815 bytes > 67108864
- M16 right L=132 rod: over budget: fine raw + gzip-1 166053492 bytes > 67108864
- M16 left L=132 rod: over budget: fine raw + gzip-1 118121048 bytes > 67108864
- M16 right L=133 rod: over budget: fine raw + gzip-1 167204077 bytes > 67108864
- M16 left L=133 rod: over budget: fine raw + gzip-1 119067699 bytes > 67108864
- M16 right L=134 rod: over budget: fine raw + gzip-1 168789106 bytes > 67108864
- M16 left L=134 rod: over budget: fine raw + gzip-1 120216481 bytes > 67108864
- M16 right L=135 rod: over budget: fine raw + gzip-1 169755213 bytes > 67108864
- M16 left L=135 rod: over budget: fine raw + gzip-1 120793476 bytes > 67108864
- M16 right L=136 rod: over budget: fine raw + gzip-1 170133767 bytes > 67108864
- M16 left L=136 rod: over budget: fine raw + gzip-1 121121018 bytes > 67108864
- M16 right L=137 rod: over budget: fine raw + gzip-1 173104969 bytes > 67108864
- M16 left L=137 rod: over budget: fine raw + gzip-1 123225290 bytes > 67108864
- M16 right L=138 rod: over budget: fine raw + gzip-1 173596644 bytes > 67108864
- M16 left L=138 rod: over budget: fine raw + gzip-1 123493741 bytes > 67108864
- M16 right L=139 rod: over budget: fine raw + gzip-1 174745352 bytes > 67108864
- M16 left L=139 rod: over budget: fine raw + gzip-1 124442551 bytes > 67108864
- M16 right L=140 rod: over budget: fine raw + gzip-1 176332284 bytes > 67108864
- M16 left L=140 rod: over budget: fine raw + gzip-1 125601316 bytes > 67108864
- M16 right L=141 rod: over budget: fine raw + gzip-1 177300029 bytes > 67108864
- M16 left L=141 rod: over budget: fine raw + gzip-1 126166504 bytes > 67108864
- M16 right L=142 rod: over budget: fine raw + gzip-1 177679202 bytes > 67108864
- M16 left L=142 rod: over budget: fine raw + gzip-1 126493546 bytes > 67108864
- M16 right L=143 rod: over budget: fine raw + gzip-1 180648364 bytes > 67108864
- M16 left L=143 rod: over budget: fine raw + gzip-1 128597961 bytes > 67108864
- M16 right L=144 rod: over budget: fine raw + gzip-1 181138796 bytes > 67108864
- M16 left L=144 rod: over budget: fine raw + gzip-1 128864132 bytes > 67108864
- M16 right L=145 rod: over budget: fine raw + gzip-1 182289414 bytes > 67108864
- M16 left L=145 rod: over budget: fine raw + gzip-1 129810929 bytes > 67108864
- M16 right L=146 rod: over budget: fine raw + gzip-1 183868812 bytes > 67108864
- M16 left L=146 rod: over budget: fine raw + gzip-1 130963750 bytes > 67108864
- M16 right L=147 rod: over budget: fine raw + gzip-1 184837657 bytes > 67108864
- M16 left L=147 rod: over budget: fine raw + gzip-1 131537094 bytes > 67108864
- M16 right L=148 rod: over budget: fine raw + gzip-1 185221454 bytes > 67108864
- M16 left L=148 rod: over budget: fine raw + gzip-1 131864234 bytes > 67108864
- M16 right L=149 rod: over budget: fine raw + gzip-1 188195862 bytes > 67108864
- M16 left L=149 rod: over budget: fine raw + gzip-1 133969004 bytes > 67108864
- M16 right L=150 rod: over budget: fine raw + gzip-1 188681161 bytes > 67108864
- M16 left L=150 rod: over budget: fine raw + gzip-1 134239837 bytes > 67108864
- M16 right L=151 rod: over budget: fine raw + gzip-1 189831736 bytes > 67108864
- M16 left L=151 rod: over budget: fine raw + gzip-1 135186784 bytes > 67108864
- M16 right L=152 rod: over budget: fine raw + gzip-1 191416814 bytes > 67108864
- M16 left L=152 rod: over budget: fine raw + gzip-1 136346900 bytes > 67108864
- M16 right L=153 rod: over budget: fine raw + gzip-1 192383934 bytes > 67108864
- M16 left L=153 rod: over budget: fine raw + gzip-1 136912525 bytes > 67108864
- M16 right L=154 rod: over budget: fine raw + gzip-1 192763770 bytes > 67108864
- M16 left L=154 rod: over budget: fine raw + gzip-1 137239738 bytes > 67108864
- M16 right L=155 rod: over budget: fine raw + gzip-1 195738279 bytes > 67108864
- M16 left L=155 rod: over budget: fine raw + gzip-1 139343474 bytes > 67108864
- M16 right L=156 rod: over budget: fine raw + gzip-1 196223533 bytes > 67108864
- M16 left L=156 rod: over budget: fine raw + gzip-1 139615584 bytes > 67108864
- M16 right L=157 rod: over budget: fine raw + gzip-1 197378918 bytes > 67108864
- M16 left L=157 rod: over budget: fine raw + gzip-1 140562352 bytes > 67108864
- M16 right L=158 rod: over budget: fine raw + gzip-1 198955884 bytes > 67108864
- M16 left L=158 rod: over budget: fine raw + gzip-1 141715756 bytes > 67108864
- M16 right L=159 rod: over budget: fine raw + gzip-1 199920945 bytes > 67108864
- M16 left L=159 rod: over budget: fine raw + gzip-1 142291709 bytes > 67108864
- M16 right L=160 rod: over budget: fine raw + gzip-1 200304425 bytes > 67108864
- M16 left L=160 rod: over budget: fine raw + gzip-1 142616156 bytes > 67108864
- M18 right L=66 rod: over budget: fine raw + gzip-1 67566627 bytes > 67108864
- M18 right L=67 rod: over budget: fine raw + gzip-1 67722440 bytes > 67108864
- M18 right L=67.5 rod: over budget: fine raw + gzip-1 67724033 bytes > 67108864
- M18 right L=68 rod: over budget: fine raw + gzip-1 68315644 bytes > 67108864
- M18 right L=69 rod: over budget: fine raw + gzip-1 69616840 bytes > 67108864
- M18 right L=70 rod: over budget: fine raw + gzip-1 70461876 bytes > 67108864
- M18 right L=71 rod: over budget: fine raw + gzip-1 71483209 bytes > 67108864
- M18 right L=72 rod: over budget: fine raw + gzip-1 71678161 bytes > 67108864
- M18 right L=72.5 rod: over budget: fine raw + gzip-1 73010173 bytes > 67108864
- M18 right L=73 rod: over budget: fine raw + gzip-1 74520992 bytes > 67108864
- M18 right L=74 rod: over budget: fine raw + gzip-1 75306053 bytes > 67108864
- M18 right L=75 rod: over budget: fine raw + gzip-1 75250225 bytes > 67108864
- M18 right L=76 rod: over budget: fine raw + gzip-1 76214196 bytes > 67108864
- M18 right L=77 rod: over budget: fine raw + gzip-1 77669900 bytes > 67108864
- M18 right L=77.5 rod: over budget: fine raw + gzip-1 77987119 bytes > 67108864
- M18 right L=78 rod: over budget: fine raw + gzip-1 78872082 bytes > 67108864
- M18 right L=79 rod: over budget: fine raw + gzip-1 79100301 bytes > 67108864
- M18 right L=80 rod: over budget: fine raw + gzip-1 80538281 bytes > 67108864
- M18 right L=81 rod: over budget: fine raw + gzip-1 82622016 bytes > 67108864
- M18 right L=82 rod: over budget: fine raw + gzip-1 82782149 bytes > 67108864
- M18 right L=82.5 rod: over budget: fine raw + gzip-1 82780045 bytes > 67108864
- M18 right L=83 rod: over budget: fine raw + gzip-1 83388083 bytes > 67108864
- M18 right L=84 rod: over budget: fine raw + gzip-1 84671843 bytes > 67108864
- M18 right L=85 rod: over budget: fine raw + gzip-1 85517114 bytes > 67108864
- M18 right L=86 rod: over budget: fine raw + gzip-1 86540565 bytes > 67108864
- M18 right L=87 rod: over budget: fine raw + gzip-1 86780220 bytes > 67108864
- M18 right L=87.5 rod: over budget: fine raw + gzip-1 88066787 bytes > 67108864
- M18 right L=88 rod: over budget: fine raw + gzip-1 89581347 bytes > 67108864
- M18 right L=89 rod: over budget: fine raw + gzip-1 90362206 bytes > 67108864
- M18 right L=90 rod: over budget: fine raw + gzip-1 90309815 bytes > 67108864
- M18 right L=91 rod: over budget: fine raw + gzip-1 91273790 bytes > 67108864
- M18 right L=92 rod: over budget: fine raw + gzip-1 92724973 bytes > 67108864
- M18 left L=92 rod: over budget: fine raw + gzip-1 67336201 bytes > 67108864
- M18 right L=92.5 rod: over budget: fine raw + gzip-1 93047337 bytes > 67108864
- M18 left L=92.5 rod: over budget: fine raw + gzip-1 67562412 bytes > 67108864
- M18 right L=93 rod: over budget: fine raw + gzip-1 93896900 bytes > 67108864
- M18 left L=93 rod: over budget: fine raw + gzip-1 68049605 bytes > 67108864
- M18 right L=94 rod: over budget: fine raw + gzip-1 94161655 bytes > 67108864
- M18 left L=94 rod: over budget: fine raw + gzip-1 68208656 bytes > 67108864
- M18 right L=95 rod: over budget: fine raw + gzip-1 95595806 bytes > 67108864
- M18 left L=95 rod: over budget: fine raw + gzip-1 69675143 bytes > 67108864
- M18 right L=96 rod: over budget: fine raw + gzip-1 97680762 bytes > 67108864
- M18 left L=96 rod: over budget: fine raw + gzip-1 70688278 bytes > 67108864
- M18 right L=97 rod: over budget: fine raw + gzip-1 97840435 bytes > 67108864
- M18 left L=97 rod: over budget: fine raw + gzip-1 70888184 bytes > 67108864
- M18 right L=97.5 rod: over budget: fine raw + gzip-1 97838451 bytes > 67108864
- M18 left L=97.5 rod: over budget: fine raw + gzip-1 70868303 bytes > 67108864
- M18 right L=98 rod: over budget: fine raw + gzip-1 98446574 bytes > 67108864
- M18 left L=98 rod: over budget: fine raw + gzip-1 71380433 bytes > 67108864
- M18 right L=99 rod: over budget: fine raw + gzip-1 99727778 bytes > 67108864
- M18 left L=99 rod: over budget: fine raw + gzip-1 72419864 bytes > 67108864
- M18 right L=100 rod: over budget: fine raw + gzip-1 100574673 bytes > 67108864
- M18 left L=100 rod: over budget: fine raw + gzip-1 73004960 bytes > 67108864
- M18 right L=101 rod: over budget: fine raw + gzip-1 101598881 bytes > 67108864
- M18 left L=101 rod: over budget: fine raw + gzip-1 73617987 bytes > 67108864
- M18 right L=102 rod: over budget: fine raw + gzip-1 101843766 bytes > 67108864
- M18 left L=102 rod: over budget: fine raw + gzip-1 73737572 bytes > 67108864
- M18 right L=102.5 rod: over budget: fine raw + gzip-1 103124374 bytes > 67108864
- M18 left L=102.5 rod: over budget: fine raw + gzip-1 75115950 bytes > 67108864
- M18 right L=103 rod: over budget: fine raw + gzip-1 104643476 bytes > 67108864
- M18 left L=103 rod: over budget: fine raw + gzip-1 75925666 bytes > 67108864
- M18 right L=104 rod: over budget: fine raw + gzip-1 105421575 bytes > 67108864
- M18 left L=104 rod: over budget: fine raw + gzip-1 76243680 bytes > 67108864
- M18 right L=105 rod: over budget: fine raw + gzip-1 105368306 bytes > 67108864
- M18 left L=105 rod: over budget: fine raw + gzip-1 76317138 bytes > 67108864
- M18 right L=106 rod: over budget: fine raw + gzip-1 106332414 bytes > 67108864
- M18 left L=106 rod: over budget: fine raw + gzip-1 77126592 bytes > 67108864
- M18 right L=107 rod: over budget: fine raw + gzip-1 107783837 bytes > 67108864
- M18 left L=107 rod: over budget: fine raw + gzip-1 78229501 bytes > 67108864
- M18 right L=107.5 rod: over budget: fine raw + gzip-1 108106708 bytes > 67108864
- M18 left L=107.5 rod: over budget: fine raw + gzip-1 78454176 bytes > 67108864
- M18 right L=108 rod: over budget: fine raw + gzip-1 108953816 bytes > 67108864
- M18 left L=108 rod: over budget: fine raw + gzip-1 78939655 bytes > 67108864
- M18 right L=109 rod: over budget: fine raw + gzip-1 109218802 bytes > 67108864
- M18 left L=109 rod: over budget: fine raw + gzip-1 79102459 bytes > 67108864
- M18 right L=110 rod: over budget: fine raw + gzip-1 110654135 bytes > 67108864
- M18 left L=110 rod: over budget: fine raw + gzip-1 80569431 bytes > 67108864
- M18 right L=111 rod: over budget: fine raw + gzip-1 112739711 bytes > 67108864
- M18 left L=111 rod: over budget: fine raw + gzip-1 81582602 bytes > 67108864
- M18 right L=112 rod: over budget: fine raw + gzip-1 112900331 bytes > 67108864
- M18 left L=112 rod: over budget: fine raw + gzip-1 81777540 bytes > 67108864
- M18 right L=112.5 rod: over budget: fine raw + gzip-1 112898108 bytes > 67108864
- M18 left L=112.5 rod: over budget: fine raw + gzip-1 81766483 bytes > 67108864
- M18 right L=113 rod: over budget: fine raw + gzip-1 113506852 bytes > 67108864
- M18 left L=113 rod: over budget: fine raw + gzip-1 82277139 bytes > 67108864
- M18 right L=114 rod: over budget: fine raw + gzip-1 114789856 bytes > 67108864
- M18 left L=114 rod: over budget: fine raw + gzip-1 83319703 bytes > 67108864
- M18 right L=115 rod: over budget: fine raw + gzip-1 115635715 bytes > 67108864
- M18 left L=115 rod: over budget: fine raw + gzip-1 83903101 bytes > 67108864
- M18 right L=116 rod: over budget: fine raw + gzip-1 116659266 bytes > 67108864
- M18 left L=116 rod: over budget: fine raw + gzip-1 84512613 bytes > 67108864
- M18 right L=117 rod: over budget: fine raw + gzip-1 116903120 bytes > 67108864
- M18 left L=117 rod: over budget: fine raw + gzip-1 84638039 bytes > 67108864
- M18 right L=117.5 rod: over budget: fine raw + gzip-1 118185643 bytes > 67108864
- M18 left L=117.5 rod: over budget: fine raw + gzip-1 86018193 bytes > 67108864
- M18 right L=118 rod: over budget: fine raw + gzip-1 119698984 bytes > 67108864
- M18 left L=118 rod: over budget: fine raw + gzip-1 86824308 bytes > 67108864
- M18 right L=119 rod: over budget: fine raw + gzip-1 120480630 bytes > 67108864
- M18 left L=119 rod: over budget: fine raw + gzip-1 87133051 bytes > 67108864
- M18 right L=120 rod: over budget: fine raw + gzip-1 120431061 bytes > 67108864
- M18 left L=120 rod: over budget: fine raw + gzip-1 87219278 bytes > 67108864
- M18 right L=121 rod: over budget: fine raw + gzip-1 121390471 bytes > 67108864
- M18 left L=121 rod: over budget: fine raw + gzip-1 88025351 bytes > 67108864
- M18 right L=122 rod: over budget: fine raw + gzip-1 122848614 bytes > 67108864
- M18 left L=122 rod: over budget: fine raw + gzip-1 89131411 bytes > 67108864
- M18 right L=122.5 rod: over budget: fine raw + gzip-1 123168641 bytes > 67108864
- M18 left L=122.5 rod: over budget: fine raw + gzip-1 89358369 bytes > 67108864
- M18 right L=123 rod: over budget: fine raw + gzip-1 124017584 bytes > 67108864
- M18 left L=123 rod: over budget: fine raw + gzip-1 89842988 bytes > 67108864
- M18 right L=124 rod: over budget: fine raw + gzip-1 124280663 bytes > 67108864
- M18 left L=124 rod: over budget: fine raw + gzip-1 90004919 bytes > 67108864
- M18 right L=125 rod: over budget: fine raw + gzip-1 125715921 bytes > 67108864
- M18 left L=125 rod: over budget: fine raw + gzip-1 91477527 bytes > 67108864
- M18 right L=126 rod: over budget: fine raw + gzip-1 127802998 bytes > 67108864
- M18 left L=126 rod: over budget: fine raw + gzip-1 92487061 bytes > 67108864
- M18 right L=127 rod: over budget: fine raw + gzip-1 127965527 bytes > 67108864
- M18 left L=127 rod: over budget: fine raw + gzip-1 92679459 bytes > 67108864
- M18 right L=127.5 rod: over budget: fine raw + gzip-1 127963944 bytes > 67108864
- M18 left L=127.5 rod: over budget: fine raw + gzip-1 92676083 bytes > 67108864
- M18 right L=128 rod: over budget: fine raw + gzip-1 128573334 bytes > 67108864
- M18 left L=128 rod: over budget: fine raw + gzip-1 93188072 bytes > 67108864
- M18 right L=129 rod: over budget: fine raw + gzip-1 129855116 bytes > 67108864
- M18 left L=129 rod: over budget: fine raw + gzip-1 94227598 bytes > 67108864
- M18 right L=130 rod: over budget: fine raw + gzip-1 130703217 bytes > 67108864
- M18 left L=130 rod: over budget: fine raw + gzip-1 94812077 bytes > 67108864
- M18 right L=131 rod: over budget: fine raw + gzip-1 131708482 bytes > 67108864
- M18 left L=131 rod: over budget: fine raw + gzip-1 95427567 bytes > 67108864
- M18 right L=132 rod: over budget: fine raw + gzip-1 131963667 bytes > 67108864
- M18 left L=132 rod: over budget: fine raw + gzip-1 95546642 bytes > 67108864
- M18 right L=132.5 rod: over budget: fine raw + gzip-1 133238543 bytes > 67108864
- M18 left L=132.5 rod: over budget: fine raw + gzip-1 96928814 bytes > 67108864
- M18 right L=133 rod: over budget: fine raw + gzip-1 134765507 bytes > 67108864
- M18 left L=133 rod: over budget: fine raw + gzip-1 97740697 bytes > 67108864
- M18 right L=134 rod: over budget: fine raw + gzip-1 135538848 bytes > 67108864
- M18 left L=134 rod: over budget: fine raw + gzip-1 98037689 bytes > 67108864
- M18 right L=135 rod: over budget: fine raw + gzip-1 135488790 bytes > 67108864
- M18 left L=135 rod: over budget: fine raw + gzip-1 98119949 bytes > 67108864
- M18 right L=136 rod: over budget: fine raw + gzip-1 136456986 bytes > 67108864
- M18 left L=136 rod: over budget: fine raw + gzip-1 98924799 bytes > 67108864
- M18 right L=137 rod: over budget: fine raw + gzip-1 137903315 bytes > 67108864
- M18 left L=137 rod: over budget: fine raw + gzip-1 100031441 bytes > 67108864
- M18 right L=137.5 rod: over budget: fine raw + gzip-1 138226158 bytes > 67108864
- M18 left L=137.5 rod: over budget: fine raw + gzip-1 100256245 bytes > 67108864
- M18 right L=138 rod: over budget: fine raw + gzip-1 139077885 bytes > 67108864
- M18 left L=138 rod: over budget: fine raw + gzip-1 100749475 bytes > 67108864
- M18 right L=139 rod: over budget: fine raw + gzip-1 139336717 bytes > 67108864
- M18 left L=139 rod: over budget: fine raw + gzip-1 100902362 bytes > 67108864
- M18 right L=140 rod: over budget: fine raw + gzip-1 140766113 bytes > 67108864
- M18 left L=140 rod: over budget: fine raw + gzip-1 102367370 bytes > 67108864
- M18 right L=141 rod: over budget: fine raw + gzip-1 142859788 bytes > 67108864
- M18 left L=141 rod: over budget: fine raw + gzip-1 103378563 bytes > 67108864
- M18 right L=142 rod: over budget: fine raw + gzip-1 143016891 bytes > 67108864
- M18 left L=142 rod: over budget: fine raw + gzip-1 103552084 bytes > 67108864
- M18 right L=142.5 rod: over budget: fine raw + gzip-1 143020782 bytes > 67108864
- M18 left L=142.5 rod: over budget: fine raw + gzip-1 103566161 bytes > 67108864
- M18 right L=143 rod: over budget: fine raw + gzip-1 143630569 bytes > 67108864
- M18 left L=143 rod: over budget: fine raw + gzip-1 104076620 bytes > 67108864
- M18 right L=144 rod: over budget: fine raw + gzip-1 144912680 bytes > 67108864
- M18 left L=144 rod: over budget: fine raw + gzip-1 105117463 bytes > 67108864
- M18 right L=145 rod: over budget: fine raw + gzip-1 145759551 bytes > 67108864
- M18 left L=145 rod: over budget: fine raw + gzip-1 105702385 bytes > 67108864
- M18 right L=146 rod: over budget: fine raw + gzip-1 146768066 bytes > 67108864
- M18 left L=146 rod: over budget: fine raw + gzip-1 106318937 bytes > 67108864
- M18 right L=147 rod: over budget: fine raw + gzip-1 147020762 bytes > 67108864
- M18 left L=147 rod: over budget: fine raw + gzip-1 106440922 bytes > 67108864
- M18 right L=147.5 rod: over budget: fine raw + gzip-1 148296616 bytes > 67108864
- M18 left L=147.5 rod: over budget: fine raw + gzip-1 107823828 bytes > 67108864
- M18 right L=148 rod: over budget: fine raw + gzip-1 149824533 bytes > 67108864
- M18 left L=148 rod: over budget: fine raw + gzip-1 108623013 bytes > 67108864
- M18 right L=149 rod: over budget: fine raw + gzip-1 150597143 bytes > 67108864
- M18 left L=149 rod: over budget: fine raw + gzip-1 108919712 bytes > 67108864
- M18 right L=150 rod: over budget: fine raw + gzip-1 150549563 bytes > 67108864
- M18 left L=150 rod: over budget: fine raw + gzip-1 109012467 bytes > 67108864
- M18 right L=151 rod: over budget: fine raw + gzip-1 151516846 bytes > 67108864
- M18 left L=151 rod: over budget: fine raw + gzip-1 109820345 bytes > 67108864
- M18 right L=152 rod: over budget: fine raw + gzip-1 152963970 bytes > 67108864
- M18 left L=152 rod: over budget: fine raw + gzip-1 110925659 bytes > 67108864
- M18 right L=152.5 rod: over budget: fine raw + gzip-1 153288253 bytes > 67108864
- M18 left L=152.5 rod: over budget: fine raw + gzip-1 111148878 bytes > 67108864
- M18 right L=153 rod: over budget: fine raw + gzip-1 154137613 bytes > 67108864
- M18 left L=153 rod: over budget: fine raw + gzip-1 111638252 bytes > 67108864
- M18 right L=154 rod: over budget: fine raw + gzip-1 154399208 bytes > 67108864
- M18 left L=154 rod: over budget: fine raw + gzip-1 111796347 bytes > 67108864
- M18 right L=155 rod: over budget: fine raw + gzip-1 155827948 bytes > 67108864
- M18 left L=155 rod: over budget: fine raw + gzip-1 113264751 bytes > 67108864
- M18 right L=156 rod: over budget: fine raw + gzip-1 157919818 bytes > 67108864
- M18 left L=156 rod: over budget: fine raw + gzip-1 114271272 bytes > 67108864
- M18 right L=157 rod: over budget: fine raw + gzip-1 158083944 bytes > 67108864
- M18 left L=157 rod: over budget: fine raw + gzip-1 114449606 bytes > 67108864
- M18 right L=157.5 rod: over budget: fine raw + gzip-1 158081693 bytes > 67108864
- M18 left L=157.5 rod: over budget: fine raw + gzip-1 114452949 bytes > 67108864
- M18 right L=158 rod: over budget: fine raw + gzip-1 158689352 bytes > 67108864
- M18 left L=158 rod: over budget: fine raw + gzip-1 114963196 bytes > 67108864
- M18 right L=159 rod: over budget: fine raw + gzip-1 159973674 bytes > 67108864
- M18 left L=159 rod: over budget: fine raw + gzip-1 116006499 bytes > 67108864
- M18 right L=160 rod: over budget: fine raw + gzip-1 160817461 bytes > 67108864
- M18 left L=160 rod: over budget: fine raw + gzip-1 116589657 bytes > 67108864
- M18 right L=161 rod: over budget: fine raw + gzip-1 161895245 bytes > 67108864
- M18 left L=161 rod: over budget: fine raw + gzip-1 117181206 bytes > 67108864
- M18 right L=162 rod: over budget: fine raw + gzip-1 162087021 bytes > 67108864
- M18 left L=162 rod: over budget: fine raw + gzip-1 117325133 bytes > 67108864
- M18 right L=162.5 rod: over budget: fine raw + gzip-1 163357895 bytes > 67108864
- M18 left L=162.5 rod: over budget: fine raw + gzip-1 118711213 bytes > 67108864
- M18 right L=163 rod: over budget: fine raw + gzip-1 164885621 bytes > 67108864
- M18 left L=163 rod: over budget: fine raw + gzip-1 119509954 bytes > 67108864
- M18 right L=164 rod: over budget: fine raw + gzip-1 165676915 bytes > 67108864
- M18 left L=164 rod: over budget: fine raw + gzip-1 119850076 bytes > 67108864
- M18 right L=165 rod: over budget: fine raw + gzip-1 165610646 bytes > 67108864
- M18 left L=165 rod: over budget: fine raw + gzip-1 119896918 bytes > 67108864
- M18 right L=166 rod: over budget: fine raw + gzip-1 166572299 bytes > 67108864
- M18 left L=166 rod: over budget: fine raw + gzip-1 120718957 bytes > 67108864
- M18 right L=167 rod: over budget: fine raw + gzip-1 168027523 bytes > 67108864
- M18 left L=167 rod: over budget: fine raw + gzip-1 121808516 bytes > 67108864
- M18 right L=167.5 rod: over budget: fine raw + gzip-1 168347609 bytes > 67108864
- M18 left L=167.5 rod: over budget: fine raw + gzip-1 122037526 bytes > 67108864
- M18 right L=168 rod: over budget: fine raw + gzip-1 169201378 bytes > 67108864
- M18 left L=168 rod: over budget: fine raw + gzip-1 122521976 bytes > 67108864
- M18 right L=169 rod: over budget: fine raw + gzip-1 169454066 bytes > 67108864
- M18 left L=169 rod: over budget: fine raw + gzip-1 122682813 bytes > 67108864
- M18 right L=170 rod: over budget: fine raw + gzip-1 170889181 bytes > 67108864
- M18 left L=170 rod: over budget: fine raw + gzip-1 124148635 bytes > 67108864
- M18 right L=171 rod: over budget: fine raw + gzip-1 173019950 bytes > 67108864
- M18 left L=171 rod: over budget: fine raw + gzip-1 125128558 bytes > 67108864
- M18 right L=172 rod: over budget: fine raw + gzip-1 173138771 bytes > 67108864
- M18 left L=172 rod: over budget: fine raw + gzip-1 125333917 bytes > 67108864
- M18 right L=172.5 rod: over budget: fine raw + gzip-1 173139793 bytes > 67108864
- M18 left L=172.5 rod: over budget: fine raw + gzip-1 125342905 bytes > 67108864
- M18 right L=173 rod: over budget: fine raw + gzip-1 173747932 bytes > 67108864
- M18 left L=173 rod: over budget: fine raw + gzip-1 125854806 bytes > 67108864
- M18 right L=174 rod: over budget: fine raw + gzip-1 175044043 bytes > 67108864
- M18 left L=174 rod: over budget: fine raw + gzip-1 126881742 bytes > 67108864
- M18 right L=175 rod: over budget: fine raw + gzip-1 175877271 bytes > 67108864
- M18 left L=175 rod: over budget: fine raw + gzip-1 127479239 bytes > 67108864
- M18 right L=176 rod: over budget: fine raw + gzip-1 176952451 bytes > 67108864
- M18 left L=176 rod: over budget: fine raw + gzip-1 128071141 bytes > 67108864
- M18 right L=177 rod: over budget: fine raw + gzip-1 177141496 bytes > 67108864
- M18 left L=177 rod: over budget: fine raw + gzip-1 128215256 bytes > 67108864
- M18 right L=177.5 rod: over budget: fine raw + gzip-1 178416681 bytes > 67108864
- M18 left L=177.5 rod: over budget: fine raw + gzip-1 129590482 bytes > 67108864
- M18 right L=178 rod: over budget: fine raw + gzip-1 179939660 bytes > 67108864
- M18 left L=178 rod: over budget: fine raw + gzip-1 130398948 bytes > 67108864
- M18 right L=179 rod: over budget: fine raw + gzip-1 180733808 bytes > 67108864
- M18 left L=179 rod: over budget: fine raw + gzip-1 130737010 bytes > 67108864
- M18 right L=180 rod: over budget: fine raw + gzip-1 180668320 bytes > 67108864
- M18 left L=180 rod: over budget: fine raw + gzip-1 130791074 bytes > 67108864
- M20 right L=65 rod: over budget: fine raw + gzip-1 70089640 bytes > 67108864
- M20 right L=66 rod: over budget: fine raw + gzip-1 70134879 bytes > 67108864
- M20 right L=67 rod: over budget: fine raw + gzip-1 70405731 bytes > 67108864
- M20 right L=67.5 rod: over budget: fine raw + gzip-1 70469082 bytes > 67108864
- M20 right L=68 rod: over budget: fine raw + gzip-1 71092238 bytes > 67108864
- M20 right L=69 rod: over budget: fine raw + gzip-1 72466212 bytes > 67108864
- M20 right L=70 rod: over budget: fine raw + gzip-1 73286085 bytes > 67108864
- M20 right L=71 rod: over budget: fine raw + gzip-1 74277074 bytes > 67108864
- M20 right L=72 rod: over budget: fine raw + gzip-1 74507734 bytes > 67108864
- M20 right L=72.5 rod: over budget: fine raw + gzip-1 77927034 bytes > 67108864
- M20 right L=73 rod: over budget: fine raw + gzip-1 77947283 bytes > 67108864
- M20 right L=74 rod: over budget: fine raw + gzip-1 78005092 bytes > 67108864
- M20 right L=75 rod: over budget: fine raw + gzip-1 78299122 bytes > 67108864
- M20 right L=76 rod: over budget: fine raw + gzip-1 79502555 bytes > 67108864
- M20 right L=77 rod: over budget: fine raw + gzip-1 80829705 bytes > 67108864
- M20 right L=77.5 rod: over budget: fine raw + gzip-1 81116517 bytes > 67108864
- M20 right L=78 rod: over budget: fine raw + gzip-1 82139867 bytes > 67108864
- M20 right L=79 rod: over budget: fine raw + gzip-1 82241393 bytes > 67108864
- M20 right L=80 rod: over budget: fine raw + gzip-1 85755887 bytes > 67108864
- M20 right L=81 rod: over budget: fine raw + gzip-1 85775217 bytes > 67108864
- M20 right L=82 rod: over budget: fine raw + gzip-1 85990908 bytes > 67108864
- M20 right L=82.5 rod: over budget: fine raw + gzip-1 86144054 bytes > 67108864
- M20 right L=83 rod: over budget: fine raw + gzip-1 86768074 bytes > 67108864
- M20 right L=84 rod: over budget: fine raw + gzip-1 88140985 bytes > 67108864
- M20 right L=85 rod: over budget: fine raw + gzip-1 88960986 bytes > 67108864
- M20 right L=86 rod: over budget: fine raw + gzip-1 89951791 bytes > 67108864
- M20 right L=87 rod: over budget: fine raw + gzip-1 90242864 bytes > 67108864
- M20 right L=87.5 rod: over budget: fine raw + gzip-1 93599660 bytes > 67108864
- M20 right L=88 rod: over budget: fine raw + gzip-1 93594407 bytes > 67108864
- M20 right L=89 rod: over budget: fine raw + gzip-1 93670142 bytes > 67108864
- M20 right L=90 rod: over budget: fine raw + gzip-1 93974166 bytes > 67108864
- M20 right L=91 rod: over budget: fine raw + gzip-1 95175115 bytes > 67108864
- M20 right L=92 rod: over budget: fine raw + gzip-1 96496276 bytes > 67108864
- M20 left L=92 rod: over budget: fine raw + gzip-1 67759962 bytes > 67108864
- M20 right L=92.5 rod: over budget: fine raw + gzip-1 96792173 bytes > 67108864
- M20 left L=92.5 rod: over budget: fine raw + gzip-1 68009412 bytes > 67108864
- M20 right L=93 rod: over budget: fine raw + gzip-1 97727242 bytes > 67108864
- M20 left L=93 rod: over budget: fine raw + gzip-1 68486994 bytes > 67108864
- M20 right L=94 rod: over budget: fine raw + gzip-1 97907807 bytes > 67108864
- M20 left L=94 rod: over budget: fine raw + gzip-1 68713524 bytes > 67108864
- M20 right L=95 rod: over budget: fine raw + gzip-1 101421332 bytes > 67108864
- M20 left L=95 rod: over budget: fine raw + gzip-1 71256502 bytes > 67108864
- M20 right L=96 rod: over budget: fine raw + gzip-1 101446836 bytes > 67108864
- M20 left L=96 rod: over budget: fine raw + gzip-1 71223657 bytes > 67108864
- M20 right L=97 rod: over budget: fine raw + gzip-1 101665343 bytes > 67108864
- M20 left L=97 rod: over budget: fine raw + gzip-1 71245996 bytes > 67108864
- M20 right L=97.5 rod: over budget: fine raw + gzip-1 101802601 bytes > 67108864
- M20 left L=97.5 rod: over budget: fine raw + gzip-1 71289277 bytes > 67108864
- M20 right L=98 rod: over budget: fine raw + gzip-1 102424762 bytes > 67108864
- M20 left L=98 rod: over budget: fine raw + gzip-1 71825143 bytes > 67108864
- M20 right L=99 rod: over budget: fine raw + gzip-1 103800526 bytes > 67108864
- M20 left L=99 rod: over budget: fine raw + gzip-1 72898946 bytes > 67108864
- M20 right L=100 rod: over budget: fine raw + gzip-1 104619488 bytes > 67108864
- M20 left L=100 rod: over budget: fine raw + gzip-1 73486662 bytes > 67108864
- M20 right L=101 rod: over budget: fine raw + gzip-1 105610055 bytes > 67108864
- M20 left L=101 rod: over budget: fine raw + gzip-1 74055490 bytes > 67108864
- M20 right L=102 rod: over budget: fine raw + gzip-1 105901539 bytes > 67108864
- M20 left L=102 rod: over budget: fine raw + gzip-1 74326449 bytes > 67108864
- M20 right L=102.5 rod: over budget: fine raw + gzip-1 109251303 bytes > 67108864
- M20 left L=102.5 rod: over budget: fine raw + gzip-1 76733297 bytes > 67108864
- M20 right L=103 rod: over budget: fine raw + gzip-1 109252964 bytes > 67108864
- M20 left L=103 rod: over budget: fine raw + gzip-1 76647078 bytes > 67108864
- M20 right L=104 rod: over budget: fine raw + gzip-1 109328834 bytes > 67108864
- M20 left L=104 rod: over budget: fine raw + gzip-1 76752799 bytes > 67108864
- M20 right L=105 rod: over budget: fine raw + gzip-1 109633121 bytes > 67108864
- M20 left L=105 rod: over budget: fine raw + gzip-1 76773066 bytes > 67108864
- M20 right L=106 rod: over budget: fine raw + gzip-1 110836065 bytes > 67108864
- M20 left L=106 rod: over budget: fine raw + gzip-1 77808256 bytes > 67108864
- M20 right L=107 rod: over budget: fine raw + gzip-1 112158562 bytes > 67108864
- M20 left L=107 rod: over budget: fine raw + gzip-1 78720247 bytes > 67108864
- M20 right L=107.5 rod: over budget: fine raw + gzip-1 112450339 bytes > 67108864
- M20 left L=107.5 rod: over budget: fine raw + gzip-1 78971914 bytes > 67108864
- M20 right L=108 rod: over budget: fine raw + gzip-1 113385255 bytes > 67108864
- M20 left L=108 rod: over budget: fine raw + gzip-1 79447930 bytes > 67108864
- M20 right L=109 rod: over budget: fine raw + gzip-1 113566467 bytes > 67108864
- M20 left L=109 rod: over budget: fine raw + gzip-1 79668680 bytes > 67108864
- M20 right L=110 rod: over budget: fine raw + gzip-1 117080324 bytes > 67108864
- M20 left L=110 rod: over budget: fine raw + gzip-1 82218012 bytes > 67108864
- M20 right L=111 rod: over budget: fine raw + gzip-1 117106626 bytes > 67108864
- M20 left L=111 rod: over budget: fine raw + gzip-1 82185513 bytes > 67108864
- M20 right L=112 rod: over budget: fine raw + gzip-1 117324937 bytes > 67108864
- M20 left L=112 rod: over budget: fine raw + gzip-1 82206204 bytes > 67108864
- M20 right L=112.5 rod: over budget: fine raw + gzip-1 117477125 bytes > 67108864
- M20 left L=112.5 rod: over budget: fine raw + gzip-1 82252975 bytes > 67108864
- M20 right L=113 rod: over budget: fine raw + gzip-1 118100994 bytes > 67108864
- M20 left L=113 rod: over budget: fine raw + gzip-1 82788826 bytes > 67108864
- M20 right L=114 rod: over budget: fine raw + gzip-1 119479727 bytes > 67108864
- M20 left L=114 rod: over budget: fine raw + gzip-1 83863140 bytes > 67108864
- M20 right L=115 rod: over budget: fine raw + gzip-1 120294214 bytes > 67108864
- M20 left L=115 rod: over budget: fine raw + gzip-1 84449850 bytes > 67108864
- M20 right L=116 rod: over budget: fine raw + gzip-1 121284281 bytes > 67108864
- M20 left L=116 rod: over budget: fine raw + gzip-1 85016503 bytes > 67108864
- M20 right L=117 rod: over budget: fine raw + gzip-1 121576105 bytes > 67108864
- M20 left L=117 rod: over budget: fine raw + gzip-1 85291026 bytes > 67108864
- M20 right L=117.5 rod: over budget: fine raw + gzip-1 124925864 bytes > 67108864
- M20 left L=117.5 rod: over budget: fine raw + gzip-1 87697881 bytes > 67108864
- M20 right L=118 rod: over budget: fine raw + gzip-1 124927504 bytes > 67108864
- M20 left L=118 rod: over budget: fine raw + gzip-1 87593484 bytes > 67108864
- M20 right L=119 rod: over budget: fine raw + gzip-1 125013076 bytes > 67108864
- M20 left L=119 rod: over budget: fine raw + gzip-1 87716575 bytes > 67108864
- M20 right L=120 rod: over budget: fine raw + gzip-1 125321717 bytes > 67108864
- M20 left L=120 rod: over budget: fine raw + gzip-1 87733045 bytes > 67108864
- M20 right L=121 rod: over budget: fine raw + gzip-1 126522630 bytes > 67108864
- M20 left L=121 rod: over budget: fine raw + gzip-1 88766474 bytes > 67108864
- M20 right L=122 rod: over budget: fine raw + gzip-1 127844172 bytes > 67108864
- M20 left L=122 rod: over budget: fine raw + gzip-1 89677890 bytes > 67108864
- M20 right L=122.5 rod: over budget: fine raw + gzip-1 128139156 bytes > 67108864
- M20 left L=122.5 rod: over budget: fine raw + gzip-1 89930111 bytes > 67108864
- M20 right L=123 rod: over budget: fine raw + gzip-1 129062797 bytes > 67108864
- M20 left L=123 rod: over budget: fine raw + gzip-1 90407998 bytes > 67108864
- M20 right L=124 rod: over budget: fine raw + gzip-1 129263659 bytes > 67108864
- M20 left L=124 rod: over budget: fine raw + gzip-1 90630015 bytes > 67108864
- M20 right L=125 rod: over budget: fine raw + gzip-1 132777685 bytes > 67108864
- M20 left L=125 rod: over budget: fine raw + gzip-1 93176826 bytes > 67108864
- M20 right L=126 rod: over budget: fine raw + gzip-1 132794903 bytes > 67108864
- M20 left L=126 rod: over budget: fine raw + gzip-1 93145403 bytes > 67108864
- M20 right L=127 rod: over budget: fine raw + gzip-1 133014288 bytes > 67108864
- M20 left L=127 rod: over budget: fine raw + gzip-1 93166513 bytes > 67108864
- M20 right L=127.5 rod: over budget: fine raw + gzip-1 133166408 bytes > 67108864
- M20 left L=127.5 rod: over budget: fine raw + gzip-1 93213602 bytes > 67108864
- M20 right L=128 rod: over budget: fine raw + gzip-1 133789703 bytes > 67108864
- M20 left L=128 rod: over budget: fine raw + gzip-1 93748980 bytes > 67108864
- M20 right L=129 rod: over budget: fine raw + gzip-1 135158845 bytes > 67108864
- M20 left L=129 rod: over budget: fine raw + gzip-1 94819164 bytes > 67108864
- M20 right L=130 rod: over budget: fine raw + gzip-1 135982987 bytes > 67108864
- M20 left L=130 rod: over budget: fine raw + gzip-1 95396177 bytes > 67108864
- M20 right L=131 rod: over budget: fine raw + gzip-1 136976854 bytes > 67108864
- M20 left L=131 rod: over budget: fine raw + gzip-1 95980591 bytes > 67108864
- M20 right L=132 rod: over budget: fine raw + gzip-1 137269934 bytes > 67108864
- M20 left L=132 rod: over budget: fine raw + gzip-1 96246694 bytes > 67108864
- M20 right L=132.5 rod: over budget: fine raw + gzip-1 140622392 bytes > 67108864
- M20 left L=132.5 rod: over budget: fine raw + gzip-1 98658878 bytes > 67108864
- M20 right L=133 rod: over budget: fine raw + gzip-1 140614907 bytes > 67108864
- M20 left L=133 rod: over budget: fine raw + gzip-1 98569833 bytes > 67108864
- M20 right L=134 rod: over budget: fine raw + gzip-1 140672528 bytes > 67108864
- M20 left L=134 rod: over budget: fine raw + gzip-1 98681217 bytes > 67108864
- M20 right L=135 rod: over budget: fine raw + gzip-1 140995644 bytes > 67108864
- M20 left L=135 rod: over budget: fine raw + gzip-1 98692685 bytes > 67108864
- M20 right L=136 rod: over budget: fine raw + gzip-1 142199573 bytes > 67108864
- M20 left L=136 rod: over budget: fine raw + gzip-1 99725519 bytes > 67108864
- M20 right L=137 rod: over budget: fine raw + gzip-1 143520310 bytes > 67108864
- M20 left L=137 rod: over budget: fine raw + gzip-1 100635936 bytes > 67108864
- M20 right L=137.5 rod: over budget: fine raw + gzip-1 143811993 bytes > 67108864
- M20 left L=137.5 rod: over budget: fine raw + gzip-1 100887832 bytes > 67108864
- M20 right L=138 rod: over budget: fine raw + gzip-1 144735218 bytes > 67108864
- M20 left L=138 rod: over budget: fine raw + gzip-1 101384340 bytes > 67108864
- M20 right L=139 rod: over budget: fine raw + gzip-1 144929388 bytes > 67108864
- M20 left L=139 rod: over budget: fine raw + gzip-1 101585890 bytes > 67108864
- M20 right L=140 rod: over budget: fine raw + gzip-1 148455887 bytes > 67108864
- M20 left L=140 rod: over budget: fine raw + gzip-1 104135858 bytes > 67108864
- M20 right L=141 rod: over budget: fine raw + gzip-1 148491109 bytes > 67108864
- M20 left L=141 rod: over budget: fine raw + gzip-1 104103520 bytes > 67108864
- M20 right L=142 rod: over budget: fine raw + gzip-1 148684031 bytes > 67108864
- M20 left L=142 rod: over budget: fine raw + gzip-1 104124497 bytes > 67108864
- M20 right L=142.5 rod: over budget: fine raw + gzip-1 148824537 bytes > 67108864
- M20 left L=142.5 rod: over budget: fine raw + gzip-1 104168541 bytes > 67108864
- M20 right L=143 rod: over budget: fine raw + gzip-1 149451054 bytes > 67108864
- M20 left L=143 rod: over budget: fine raw + gzip-1 104699029 bytes > 67108864
- M20 right L=144 rod: over budget: fine raw + gzip-1 150825562 bytes > 67108864
- M20 left L=144 rod: over budget: fine raw + gzip-1 105777985 bytes > 67108864
- M20 right L=145 rod: over budget: fine raw + gzip-1 151641772 bytes > 67108864
- M20 left L=145 rod: over budget: fine raw + gzip-1 106367321 bytes > 67108864
- M20 right L=146 rod: over budget: fine raw + gzip-1 152628984 bytes > 67108864
- M20 left L=146 rod: over budget: fine raw + gzip-1 106936149 bytes > 67108864
- M20 right L=147 rod: over budget: fine raw + gzip-1 152926479 bytes > 67108864
- M20 left L=147 rod: over budget: fine raw + gzip-1 107205475 bytes > 67108864
- M20 right L=147.5 rod: over budget: fine raw + gzip-1 156279995 bytes > 67108864
- M20 left L=147.5 rod: over budget: fine raw + gzip-1 109612759 bytes > 67108864
- M20 right L=148 rod: over budget: fine raw + gzip-1 156273198 bytes > 67108864
- M20 left L=148 rod: over budget: fine raw + gzip-1 109536238 bytes > 67108864
- M20 right L=149 rod: over budget: fine raw + gzip-1 156334903 bytes > 67108864
- M20 left L=149 rod: over budget: fine raw + gzip-1 109644434 bytes > 67108864
- M20 right L=150 rod: over budget: fine raw + gzip-1 156669040 bytes > 67108864
- M20 left L=150 rod: over budget: fine raw + gzip-1 109647955 bytes > 67108864
- M20 right L=151 rod: over budget: fine raw + gzip-1 157873747 bytes > 67108864
- M20 left L=151 rod: over budget: fine raw + gzip-1 110680080 bytes > 67108864
- M20 right L=152 rod: over budget: fine raw + gzip-1 159193870 bytes > 67108864
- M20 left L=152 rod: over budget: fine raw + gzip-1 111594197 bytes > 67108864
- M20 right L=152.5 rod: over budget: fine raw + gzip-1 159485266 bytes > 67108864
- M20 left L=152.5 rod: over budget: fine raw + gzip-1 111847769 bytes > 67108864
- M20 right L=153 rod: over budget: fine raw + gzip-1 160407285 bytes > 67108864
- M20 left L=153 rod: over budget: fine raw + gzip-1 112338898 bytes > 67108864
- M20 right L=154 rod: over budget: fine raw + gzip-1 160603078 bytes > 67108864
- M20 left L=154 rod: over budget: fine raw + gzip-1 112540767 bytes > 67108864
- M20 right L=155 rod: over budget: fine raw + gzip-1 164127654 bytes > 67108864
- M20 left L=155 rod: over budget: fine raw + gzip-1 115092201 bytes > 67108864
- M20 right L=156 rod: over budget: fine raw + gzip-1 164159088 bytes > 67108864
- M20 left L=156 rod: over budget: fine raw + gzip-1 115060908 bytes > 67108864
- M20 right L=157 rod: over budget: fine raw + gzip-1 164350245 bytes > 67108864
- M20 left L=157 rod: over budget: fine raw + gzip-1 115080756 bytes > 67108864
- M20 right L=157.5 rod: over budget: fine raw + gzip-1 164497789 bytes > 67108864
- M20 left L=157.5 rod: over budget: fine raw + gzip-1 115124344 bytes > 67108864
- M20 right L=158 rod: over budget: fine raw + gzip-1 165123733 bytes > 67108864
- M20 left L=158 rod: over budget: fine raw + gzip-1 115652999 bytes > 67108864
- M20 right L=159 rod: over budget: fine raw + gzip-1 166493795 bytes > 67108864
- M20 left L=159 rod: over budget: fine raw + gzip-1 116734424 bytes > 67108864
- M20 right L=160 rod: over budget: fine raw + gzip-1 167314740 bytes > 67108864
- M20 left L=160 rod: over budget: fine raw + gzip-1 117323843 bytes > 67108864
- M20 right L=161 rod: over budget: fine raw + gzip-1 168343533 bytes > 67108864
- M20 left L=161 rod: over budget: fine raw + gzip-1 117936255 bytes > 67108864
- M20 right L=162 rod: over budget: fine raw + gzip-1 168600638 bytes > 67108864
- M20 left L=162 rod: over budget: fine raw + gzip-1 118161870 bytes > 67108864
- M20 right L=162.5 rod: over budget: fine raw + gzip-1 171958725 bytes > 67108864
- M20 left L=162.5 rod: over budget: fine raw + gzip-1 120569198 bytes > 67108864
- M20 right L=163 rod: over budget: fine raw + gzip-1 171946576 bytes > 67108864
- M20 left L=163 rod: over budget: fine raw + gzip-1 120492317 bytes > 67108864
- M20 right L=164 rod: over budget: fine raw + gzip-1 172128811 bytes > 67108864
- M20 left L=164 rod: over budget: fine raw + gzip-1 120612773 bytes > 67108864
- M20 right L=165 rod: over budget: fine raw + gzip-1 172327724 bytes > 67108864
- M20 left L=165 rod: over budget: fine raw + gzip-1 120601361 bytes > 67108864
- M20 right L=166 rod: over budget: fine raw + gzip-1 173552295 bytes > 67108864
- M20 left L=166 rod: over budget: fine raw + gzip-1 121630435 bytes > 67108864
- M20 right L=167 rod: over budget: fine raw + gzip-1 174850090 bytes > 67108864
- M20 left L=167 rod: over budget: fine raw + gzip-1 122544557 bytes > 67108864
- M20 right L=167.5 rod: over budget: fine raw + gzip-1 175144749 bytes > 67108864
- M20 left L=167.5 rod: over budget: fine raw + gzip-1 122801184 bytes > 67108864
- M20 right L=168 rod: over budget: fine raw + gzip-1 176065992 bytes > 67108864
- M20 left L=168 rod: over budget: fine raw + gzip-1 123292230 bytes > 67108864
- M20 right L=169 rod: over budget: fine raw + gzip-1 176252111 bytes > 67108864
- M20 left L=169 rod: over budget: fine raw + gzip-1 123485504 bytes > 67108864
- M20 right L=170 rod: over budget: fine raw + gzip-1 179779812 bytes > 67108864
- M20 left L=170 rod: over budget: fine raw + gzip-1 126038899 bytes > 67108864
- M20 right L=171 rod: over budget: fine raw + gzip-1 179795933 bytes > 67108864
- M20 left L=171 rod: over budget: fine raw + gzip-1 126028316 bytes > 67108864
- M20 right L=172 rod: over budget: fine raw + gzip-1 180008626 bytes > 67108864
- M20 left L=172 rod: over budget: fine raw + gzip-1 126031759 bytes > 67108864
- M20 right L=172.5 rod: over budget: fine raw + gzip-1 180171583 bytes > 67108864
- M20 left L=172.5 rod: over budget: fine raw + gzip-1 126078117 bytes > 67108864
- M20 right L=173 rod: over budget: fine raw + gzip-1 180797353 bytes > 67108864
- M20 left L=173 rod: over budget: fine raw + gzip-1 126605922 bytes > 67108864
- M20 right L=174 rod: over budget: fine raw + gzip-1 182181036 bytes > 67108864
- M20 left L=174 rod: over budget: fine raw + gzip-1 127709241 bytes > 67108864
- M20 right L=175 rod: over budget: fine raw + gzip-1 182988759 bytes > 67108864
- M20 left L=175 rod: over budget: fine raw + gzip-1 128273708 bytes > 67108864
- M20 right L=176 rod: over budget: fine raw + gzip-1 184013340 bytes > 67108864
- M20 left L=176 rod: over budget: fine raw + gzip-1 128893493 bytes > 67108864
- M20 right L=177 rod: over budget: fine raw + gzip-1 184274448 bytes > 67108864
- M20 left L=177 rod: over budget: fine raw + gzip-1 129115763 bytes > 67108864
- M20 right L=177.5 rod: over budget: fine raw + gzip-1 187631773 bytes > 67108864
- M20 left L=177.5 rod: over budget: fine raw + gzip-1 131521411 bytes > 67108864
- M20 right L=178 rod: over budget: fine raw + gzip-1 187620537 bytes > 67108864
- M20 left L=178 rod: over budget: fine raw + gzip-1 131445936 bytes > 67108864
- M20 right L=179 rod: over budget: fine raw + gzip-1 187802604 bytes > 67108864
- M20 left L=179 rod: over budget: fine raw + gzip-1 131571069 bytes > 67108864
- M20 right L=180 rod: over budget: fine raw + gzip-1 188001053 bytes > 67108864
- M20 left L=180 rod: over budget: fine raw + gzip-1 131557287 bytes > 67108864
- M20 right L=181 rod: over budget: fine raw + gzip-1 189225527 bytes > 67108864
- M20 left L=181 rod: over budget: fine raw + gzip-1 132586874 bytes > 67108864
- M20 right L=182 rod: over budget: fine raw + gzip-1 190526813 bytes > 67108864
- M20 left L=182 rod: over budget: fine raw + gzip-1 133503613 bytes > 67108864
- M20 right L=182.5 rod: over budget: fine raw + gzip-1 190818443 bytes > 67108864
- M20 left L=182.5 rod: over budget: fine raw + gzip-1 133753082 bytes > 67108864
- M20 right L=183 rod: over budget: fine raw + gzip-1 191728412 bytes > 67108864
- M20 left L=183 rod: over budget: fine raw + gzip-1 134249499 bytes > 67108864
- M20 right L=184 rod: over budget: fine raw + gzip-1 191925415 bytes > 67108864
- M20 left L=184 rod: over budget: fine raw + gzip-1 134441736 bytes > 67108864
- M20 right L=185 rod: over budget: fine raw + gzip-1 195462614 bytes > 67108864
- M20 left L=185 rod: over budget: fine raw + gzip-1 137002415 bytes > 67108864
- M20 right L=186 rod: over budget: fine raw + gzip-1 195469361 bytes > 67108864
- M20 left L=186 rod: over budget: fine raw + gzip-1 136988215 bytes > 67108864
- M20 right L=187 rod: over budget: fine raw + gzip-1 195681768 bytes > 67108864
- M20 left L=187 rod: over budget: fine raw + gzip-1 136990852 bytes > 67108864
- M20 right L=187.5 rod: over budget: fine raw + gzip-1 195830493 bytes > 67108864
- M20 left L=187.5 rod: over budget: fine raw + gzip-1 137036800 bytes > 67108864
- M20 right L=188 rod: over budget: fine raw + gzip-1 196456008 bytes > 67108864
- M20 left L=188 rod: over budget: fine raw + gzip-1 137567392 bytes > 67108864
- M20 right L=189 rod: over budget: fine raw + gzip-1 197836951 bytes > 67108864
- M20 left L=189 rod: over budget: fine raw + gzip-1 138654696 bytes > 67108864
- M20 right L=190 rod: over budget: fine raw + gzip-1 198647013 bytes > 67108864
- M20 left L=190 rod: over budget: fine raw + gzip-1 139235914 bytes > 67108864
- M20 right L=191 rod: over budget: fine raw + gzip-1 199676475 bytes > 67108864
- M20 left L=191 rod: over budget: fine raw + gzip-1 139845448 bytes > 67108864
- M20 right L=192 rod: over budget: fine raw + gzip-1 199930510 bytes > 67108864
- M20 left L=192 rod: over budget: fine raw + gzip-1 140069297 bytes > 67108864
- M20 right L=192.5 rod: over budget: fine raw + gzip-1 203287386 bytes > 67108864
- M20 left L=192.5 rod: over budget: fine raw + gzip-1 142475289 bytes > 67108864
- M20 right L=193 rod: over budget: fine raw + gzip-1 203278453 bytes > 67108864
- M20 left L=193 rod: over budget: fine raw + gzip-1 142403523 bytes > 67108864
- M20 right L=194 rod: over budget: fine raw + gzip-1 203460501 bytes > 67108864
- M20 left L=194 rod: over budget: fine raw + gzip-1 142524769 bytes > 67108864
- M20 right L=195 rod: over budget: fine raw + gzip-1 203673292 bytes > 67108864
- M20 left L=195 rod: over budget: fine raw + gzip-1 142516266 bytes > 67108864
- M20 right L=196 rod: over budget: fine raw + gzip-1 204897473 bytes > 67108864
- M20 left L=196 rod: over budget: fine raw + gzip-1 143545952 bytes > 67108864
- M20 right L=197 rod: over budget: fine raw + gzip-1 206199083 bytes > 67108864
- M20 left L=197 rod: over budget: fine raw + gzip-1 144462430 bytes > 67108864
- M20 right L=197.5 rod: over budget: fine raw + gzip-1 206489563 bytes > 67108864
- M20 left L=197.5 rod: over budget: fine raw + gzip-1 144712566 bytes > 67108864
- M20 right L=198 rod: over budget: fine raw + gzip-1 207411921 bytes > 67108864
- M20 left L=198 rod: over budget: fine raw + gzip-1 145207961 bytes > 67108864
- M20 right L=199 rod: over budget: fine raw + gzip-1 207597041 bytes > 67108864
- M20 left L=199 rod: over budget: fine raw + gzip-1 145399131 bytes > 67108864
- M20 right L=200 rod: over budget: fine raw + gzip-1 211134421 bytes > 67108864
- M20 left L=200 rod: over budget: fine raw + gzip-1 147962487 bytes > 67108864
- load1 8.92 read 2026-10-08T15:33:58+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The output covers 240 to 960 rows per size for M2 to M20, and every row is class ok with no silent_wrong, failure, timeout or worker_died row; the "Checks skipped" column is non-zero from M8 upward, and a skipped check is not a pass for its mesh. The quiet gate did not release (non-decisive after 900 s, 31 readings), so the "Max build + slower export s" figures are recorded but are not established timings. The rows over the byte budget are listed in the output; the turn caps derived from this block are in the campaign entry below.


### 2026-10-08-a-frontier

Run window (UTC): 2026-10-08T15:34:00+00:00 (first gate reading) to 2026-10-08T19:18:18+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: non-decisive after 900 s (31 readings). Gate readings: 31; first load1 8.92 read 2026-10-08T15:34:00+00:00; last load1 3.70 read 2026-10-08T15:49:00+00:00. Every reading is in the output below.
End reading: load1 16.96 read 2026-10-08T19:18:18+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-frontier.jsonl` — 2237 lines, sha256 f8e95669384442f816aa426f254c8a73d7bbe3fe33999f46607bb63b3ebba781. Markdown output: `bench/results/thread-spike/2026-10-08-a-frontier.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-frontier

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: frontier
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 8.92 read 2026-10-08T15:34:00+00:00
- load1 6.05 read 2026-10-08T15:34:30+00:00
- load1 4.59 read 2026-10-08T15:35:00+00:00
- load1 4.10 read 2026-10-08T15:35:30+00:00
- load1 3.13 read 2026-10-08T15:36:00+00:00
- load1 2.83 read 2026-10-08T15:36:30+00:00
- load1 2.19 read 2026-10-08T15:37:00+00:00
- load1 1.84 read 2026-10-08T15:37:30+00:00
- load1 1.96 read 2026-10-08T15:38:00+00:00
- load1 2.10 read 2026-10-08T15:38:30+00:00
- load1 1.92 read 2026-10-08T15:39:00+00:00
- load1 1.95 read 2026-10-08T15:39:30+00:00
- load1 1.81 read 2026-10-08T15:40:00+00:00
- load1 1.50 read 2026-10-08T15:40:30+00:00
- load1 1.34 read 2026-10-08T15:41:00+00:00
- load1 1.50 read 2026-10-08T15:41:30+00:00
- load1 1.58 read 2026-10-08T15:42:00+00:00
- load1 1.63 read 2026-10-08T15:42:30+00:00
- load1 2.03 read 2026-10-08T15:43:00+00:00
- load1 1.89 read 2026-10-08T15:43:30+00:00
- load1 1.52 read 2026-10-08T15:44:00+00:00
- load1 1.62 read 2026-10-08T15:44:30+00:00
- load1 1.60 read 2026-10-08T15:45:00+00:00
- load1 1.92 read 2026-10-08T15:45:30+00:00
- load1 2.21 read 2026-10-08T15:46:00+00:00
- load1 2.46 read 2026-10-08T15:46:30+00:00
- load1 3.04 read 2026-10-08T15:47:00+00:00
- load1 2.92 read 2026-10-08T15:47:30+00:00
- load1 2.46 read 2026-10-08T15:48:00+00:00
- load1 3.28 read 2026-10-08T15:48:30+00:00
- load1 3.70 read 2026-10-08T15:49:00+00:00
- release: non-decisive after 900 s (31 readings)

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 160 | 160 | 0 | 0 | 0 | 0 | -6.270e-06 | -1.309e-05 | 1527254 | 76362784 | 111427062 | 2.65 | 13290281 | 32 |
| M2.5 | 156 | 156 | 0 | 0 | 0 | 0 | -6.214e-06 | -1.307e-05 | 1849022 | 92451184 | 135779813 | 3.03 | 13269158 | 40 |
| M3 | 152 | 152 | 0 | 0 | 0 | 0 | -6.197e-06 | -1.307e-05 | 1876430 | 93821584 | 138038762 | 3.32 | 13550345 | 41 |
| M3.5 | 156 | 156 | 0 | 0 | 0 | 0 | -1.309e-06 | -1.575e-06 | 1918124 | 95906284 | 141045322 | 6.18 | 13536521 | 43 |
| M4 | 156 | 156 | 0 | 0 | 0 | 0 | -1.330e-06 | -1.568e-06 | 2334230 | 116711584 | 170709745 | 2.17 | 15132208 | 50 |
| M5 | 152 | 152 | 0 | 0 | 0 | 0 | -1.241e-06 | -1.586e-06 | 2379002 | 118950184 | 173929849 | 2.23 | 15076311 | 51 |
| M6 | 152 | 152 | 0 | 0 | 0 | 0 | -1.280e-06 | -1.572e-06 | 2514644 | 125732284 | 183750700 | 4.69 | 15079184 | 55 |
| M7 | 144 | 144 | 0 | 0 | 0 | 0 | -1.141e-06 | -1.615e-06 | 2623594 | 131179784 | 192324208 | 4.40 | 15077460 | 57 |
| M8 | 152 | 152 | 0 | 0 | 0 | 0 | -1.219e-06 | -1.584e-06 | 4197042 | 209852184 | 310319264 | 6.33 | 15181165 | 74 |
| M10 | 148 | 148 | 0 | 0 | 0 | 0 | -1.182e-06 | -1.594e-06 | 6067054 | 303352784 | 444489267 | 9.04 | 13702455 | 74 |
| M12 | 148 | 148 | 0 | 0 | 0 | 0 | -1.158e-06 | -1.602e-06 | 6564820 | 328241084 | 480601483 | 9.97 | 15205477 | 74 |
| M14 | 144 | 144 | 0 | 0 | 0 | 0 | -1.039e-06 | -1.190e-06 | 7843182 | 392159184 | 572394494 | 7.46 | 15315744 | 72 |
| M16 | 136 | 136 | 0 | 0 | 0 | 0 | -7.723e-07 | -6.146e-07 | 8642612 | 432130684 | 628759460 | 7.35 | 15336009 | 68 |
| M18 | 144 | 144 | 0 | 0 | 0 | 0 | -8.692e-07 | -5.904e-07 | 8600290 | 430014584 | 626783954 | 6.41 | 15488372 | 83 |
| M20 | 136 | 136 | 0 | 0 | 0 | 0 | -7.723e-07 | -6.139e-07 | 8972812 | 448640684 | 653109977 | 6.83 | 15517622 | 88 |

- M2 right L=62 rod: over budget: fine raw + gzip-1 69038597 bytes > 67108864
- M2 right L=64 rod: over budget: fine raw + gzip-1 71365397 bytes > 67108864
- M2 right L=66 rod: over budget: fine raw + gzip-1 73489419 bytes > 67108864
- M2 right L=68 rod: over budget: fine raw + gzip-1 75715587 bytes > 67108864
- M2 right L=70 rod: over budget: fine raw + gzip-1 78043696 bytes > 67108864
- M2 right L=72 rod: over budget: fine raw + gzip-1 80168400 bytes > 67108864
- M2 right L=74 rod: over budget: fine raw + gzip-1 82391715 bytes > 67108864
- M2 right L=76 rod: over budget: fine raw + gzip-1 84723429 bytes > 67108864
- M2 right L=78 rod: over budget: fine raw + gzip-1 86847321 bytes > 67108864
- M2 right L=80 rod: over budget: fine raw + gzip-1 89070842 bytes > 67108864
- M2 right L=82 rod: over budget: fine raw + gzip-1 91399709 bytes > 67108864
- M2 right L=84 rod: over budget: fine raw + gzip-1 93522307 bytes > 67108864
- M2 right L=86 rod: over budget: fine raw + gzip-1 95746123 bytes > 67108864
- M2 right L=88 rod: over budget: fine raw + gzip-1 98076003 bytes > 67108864
- M2 right L=90 rod: over budget: fine raw + gzip-1 100200189 bytes > 67108864
- M2 right L=92 rod: over budget: fine raw + gzip-1 102421142 bytes > 67108864
- M2 right L=94 rod: over budget: fine raw + gzip-1 104755703 bytes > 67108864
- M2 right L=96 rod: over budget: fine raw + gzip-1 106877361 bytes > 67108864
- M2 right L=98 rod: over budget: fine raw + gzip-1 109099698 bytes > 67108864
- M2 right L=100 rod: over budget: fine raw + gzip-1 111427062 bytes > 67108864
- M2 left L=68 rod: over budget: fine raw + gzip-1 67755286 bytes > 67108864
- M2 left L=70 rod: over budget: fine raw + gzip-1 69929465 bytes > 67108864
- M2 left L=72 rod: over budget: fine raw + gzip-1 71825963 bytes > 67108864
- M2 left L=74 rod: over budget: fine raw + gzip-1 73732436 bytes > 67108864
- M2 left L=76 rod: over budget: fine raw + gzip-1 75912052 bytes > 67108864
- M2 left L=78 rod: over budget: fine raw + gzip-1 77806808 bytes > 67108864
- M2 left L=80 rod: over budget: fine raw + gzip-1 79716527 bytes > 67108864
- M2 left L=82 rod: over budget: fine raw + gzip-1 81889798 bytes > 67108864
- M2 left L=84 rod: over budget: fine raw + gzip-1 83793597 bytes > 67108864
- M2 left L=86 rod: over budget: fine raw + gzip-1 85702181 bytes > 67108864
- M2 left L=88 rod: over budget: fine raw + gzip-1 87880471 bytes > 67108864
- M2 left L=90 rod: over budget: fine raw + gzip-1 89777512 bytes > 67108864
- M2 left L=92 rod: over budget: fine raw + gzip-1 91686163 bytes > 67108864
- M2 left L=94 rod: over budget: fine raw + gzip-1 93860408 bytes > 67108864
- M2 left L=96 rod: over budget: fine raw + gzip-1 95756363 bytes > 67108864
- M2 left L=98 rod: over budget: fine raw + gzip-1 97665062 bytes > 67108864
- M2 left L=100 rod: over budget: fine raw + gzip-1 99842474 bytes > 67108864
- M2.5 right L=56.25 rod: over budget: fine raw + gzip-1 67693933 bytes > 67108864
- M2.5 right L=58.5 rod: over budget: fine raw + gzip-1 70665586 bytes > 67108864
- M2.5 right L=60.75 rod: over budget: fine raw + gzip-1 73308793 bytes > 67108864
- M2.5 right L=63 rod: over budget: fine raw + gzip-1 75832402 bytes > 67108864
- M2.5 right L=65.25 rod: over budget: fine raw + gzip-1 78800756 bytes > 67108864
- M2.5 right L=67.5 rod: over budget: fine raw + gzip-1 81444126 bytes > 67108864
- M2.5 right L=69.75 rod: over budget: fine raw + gzip-1 83966988 bytes > 67108864
- M2.5 right L=72 rod: over budget: fine raw + gzip-1 86935536 bytes > 67108864
- M2.5 right L=74.25 rod: over budget: fine raw + gzip-1 89582055 bytes > 67108864
- M2.5 right L=76.5 rod: over budget: fine raw + gzip-1 92104138 bytes > 67108864
- M2.5 right L=78.75 rod: over budget: fine raw + gzip-1 95073568 bytes > 67108864
- M2.5 right L=81 rod: over budget: fine raw + gzip-1 97719400 bytes > 67108864
- M2.5 right L=83.25 rod: over budget: fine raw + gzip-1 100244243 bytes > 67108864
- M2.5 right L=85.5 rod: over budget: fine raw + gzip-1 103211281 bytes > 67108864
- M2.5 right L=87.75 rod: over budget: fine raw + gzip-1 105861541 bytes > 67108864
- M2.5 right L=90 rod: over budget: fine raw + gzip-1 108383870 bytes > 67108864
- M2.5 right L=92.25 rod: over budget: fine raw + gzip-1 111352951 bytes > 67108864
- M2.5 right L=94.5 rod: over budget: fine raw + gzip-1 113997455 bytes > 67108864
- M2.5 right L=96.75 rod: over budget: fine raw + gzip-1 116520039 bytes > 67108864
- M2.5 right L=99 rod: over budget: fine raw + gzip-1 119492519 bytes > 67108864
- M2.5 right L=101.25 rod: over budget: fine raw + gzip-1 122140448 bytes > 67108864
- M2.5 right L=103.5 rod: over budget: fine raw + gzip-1 124666885 bytes > 67108864
- M2.5 right L=105.75 rod: over budget: fine raw + gzip-1 127634121 bytes > 67108864
- M2.5 right L=108 rod: over budget: fine raw + gzip-1 130281689 bytes > 67108864
- M2.5 right L=110.25 rod: over budget: fine raw + gzip-1 132806454 bytes > 67108864
- M2.5 right L=112.5 rod: over budget: fine raw + gzip-1 135779813 bytes > 67108864
- M2.5 left L=69.75 rod: over budget: fine raw + gzip-1 67216486 bytes > 67108864
- M2.5 left L=72 rod: over budget: fine raw + gzip-1 69624718 bytes > 67108864
- M2.5 left L=74.25 rod: over budget: fine raw + gzip-1 71699124 bytes > 67108864
- M2.5 left L=76.5 rod: over budget: fine raw + gzip-1 73712858 bytes > 67108864
- M2.5 left L=78.75 rod: over budget: fine raw + gzip-1 76110777 bytes > 67108864
- M2.5 left L=81 rod: over budget: fine raw + gzip-1 78182282 bytes > 67108864
- M2.5 left L=83.25 rod: over budget: fine raw + gzip-1 80195226 bytes > 67108864
- M2.5 left L=85.5 rod: over budget: fine raw + gzip-1 82597284 bytes > 67108864
- M2.5 left L=87.75 rod: over budget: fine raw + gzip-1 84672924 bytes > 67108864
- M2.5 left L=90 rod: over budget: fine raw + gzip-1 86688264 bytes > 67108864
- M2.5 left L=92.25 rod: over budget: fine raw + gzip-1 89099544 bytes > 67108864
- M2.5 left L=94.5 rod: over budget: fine raw + gzip-1 91171257 bytes > 67108864
- M2.5 left L=96.75 rod: over budget: fine raw + gzip-1 93180234 bytes > 67108864
- M2.5 left L=99 rod: over budget: fine raw + gzip-1 95583887 bytes > 67108864
- M2.5 left L=101.25 rod: over budget: fine raw + gzip-1 97658831 bytes > 67108864
- M2.5 left L=103.5 rod: over budget: fine raw + gzip-1 99673108 bytes > 67108864
- M2.5 left L=105.75 rod: over budget: fine raw + gzip-1 102080840 bytes > 67108864
- M2.5 left L=108 rod: over budget: fine raw + gzip-1 104160236 bytes > 67108864
- M2.5 left L=110.25 rod: over budget: fine raw + gzip-1 106177798 bytes > 67108864
- M2.5 left L=112.5 rod: over budget: fine raw + gzip-1 108579289 bytes > 67108864
- M3 right L=62.5 rod: over budget: fine raw + gzip-1 68804149 bytes > 67108864
- M3 right L=65 rod: over budget: fine raw + gzip-1 71836811 bytes > 67108864
- M3 right L=67.5 rod: over budget: fine raw + gzip-1 74496964 bytes > 67108864
- M3 right L=70 rod: over budget: fine raw + gzip-1 77080000 bytes > 67108864
- M3 right L=72.5 rod: over budget: fine raw + gzip-1 80111795 bytes > 67108864
- M3 right L=75 rod: over budget: fine raw + gzip-1 82776371 bytes > 67108864
- M3 right L=77.5 rod: over budget: fine raw + gzip-1 85362670 bytes > 67108864
- M3 right L=80 rod: over budget: fine raw + gzip-1 88393237 bytes > 67108864
- M3 right L=82.5 rod: over budget: fine raw + gzip-1 91054869 bytes > 67108864
- M3 right L=85 rod: over budget: fine raw + gzip-1 93638483 bytes > 67108864
- M3 right L=87.5 rod: over budget: fine raw + gzip-1 96673321 bytes > 67108864
- M3 right L=90 rod: over budget: fine raw + gzip-1 99329861 bytes > 67108864
- M3 right L=92.5 rod: over budget: fine raw + gzip-1 101912874 bytes > 67108864
- M3 right L=95 rod: over budget: fine raw + gzip-1 104946994 bytes > 67108864
- M3 right L=97.5 rod: over budget: fine raw + gzip-1 107604567 bytes > 67108864
- M3 right L=100 rod: over budget: fine raw + gzip-1 110190543 bytes > 67108864
- M3 right L=102.5 rod: over budget: fine raw + gzip-1 113222716 bytes > 67108864
- M3 right L=105 rod: over budget: fine raw + gzip-1 115880920 bytes > 67108864
- M3 right L=107.5 rod: over budget: fine raw + gzip-1 118463973 bytes > 67108864
- M3 right L=110 rod: over budget: fine raw + gzip-1 121493500 bytes > 67108864
- M3 right L=112.5 rod: over budget: fine raw + gzip-1 124155510 bytes > 67108864
- M3 right L=115 rod: over budget: fine raw + gzip-1 126737939 bytes > 67108864
- M3 right L=117.5 rod: over budget: fine raw + gzip-1 129770710 bytes > 67108864
- M3 right L=120 rod: over budget: fine raw + gzip-1 132428986 bytes > 67108864
- M3 right L=122.5 rod: over budget: fine raw + gzip-1 135009674 bytes > 67108864
- M3 right L=125 rod: over budget: fine raw + gzip-1 138038762 bytes > 67108864
- M3 left L=77.5 rod: over budget: fine raw + gzip-1 69077522 bytes > 67108864
- M3 left L=80 rod: over budget: fine raw + gzip-1 71559732 bytes > 67108864
- M3 left L=82.5 rod: over budget: fine raw + gzip-1 73674558 bytes > 67108864
- M3 left L=85 rod: over budget: fine raw + gzip-1 75768395 bytes > 67108864
- M3 left L=87.5 rod: over budget: fine raw + gzip-1 78257225 bytes > 67108864
- M3 left L=90 rod: over budget: fine raw + gzip-1 80378309 bytes > 67108864
- M3 left L=92.5 rod: over budget: fine raw + gzip-1 82476578 bytes > 67108864
- M3 left L=95 rod: over budget: fine raw + gzip-1 84960880 bytes > 67108864
- M3 left L=97.5 rod: over budget: fine raw + gzip-1 87078611 bytes > 67108864
- M3 left L=100 rod: over budget: fine raw + gzip-1 89171228 bytes > 67108864
- M3 left L=102.5 rod: over budget: fine raw + gzip-1 91652493 bytes > 67108864
- M3 left L=105 rod: over budget: fine raw + gzip-1 93767228 bytes > 67108864
- M3 left L=107.5 rod: over budget: fine raw + gzip-1 95860750 bytes > 67108864
- M3 left L=110 rod: over budget: fine raw + gzip-1 98348658 bytes > 67108864
- M3 left L=112.5 rod: over budget: fine raw + gzip-1 100463436 bytes > 67108864
- M3 left L=115 rod: over budget: fine raw + gzip-1 102559980 bytes > 67108864
- M3 left L=117.5 rod: over budget: fine raw + gzip-1 105037966 bytes > 67108864
- M3 left L=120 rod: over budget: fine raw + gzip-1 107159830 bytes > 67108864
- M3 left L=122.5 rod: over budget: fine raw + gzip-1 109253187 bytes > 67108864
- M3 left L=125 rod: over budget: fine raw + gzip-1 111738074 bytes > 67108864
- M3.5 right L=72 rod: over budget: fine raw + gzip-1 67708292 bytes > 67108864
- M3.5 right L=75 rod: over budget: fine raw + gzip-1 70563737 bytes > 67108864
- M3.5 right L=78 rod: over budget: fine raw + gzip-1 73436375 bytes > 67108864
- M3.5 right L=81 rod: over budget: fine raw + gzip-1 76161945 bytes > 67108864
- M3.5 right L=84 rod: over budget: fine raw + gzip-1 79018852 bytes > 67108864
- M3.5 right L=87 rod: over budget: fine raw + gzip-1 81887181 bytes > 67108864
- M3.5 right L=90 rod: over budget: fine raw + gzip-1 84613659 bytes > 67108864
- M3.5 right L=93 rod: over budget: fine raw + gzip-1 87468001 bytes > 67108864
- M3.5 right L=96 rod: over budget: fine raw + gzip-1 90340321 bytes > 67108864
- M3.5 right L=99 rod: over budget: fine raw + gzip-1 93064191 bytes > 67108864
- M3.5 right L=102 rod: over budget: fine raw + gzip-1 95917431 bytes > 67108864
- M3.5 right L=105 rod: over budget: fine raw + gzip-1 98790336 bytes > 67108864
- M3.5 right L=108 rod: over budget: fine raw + gzip-1 101516093 bytes > 67108864
- M3.5 right L=111 rod: over budget: fine raw + gzip-1 104374356 bytes > 67108864
- M3.5 right L=114 rod: over budget: fine raw + gzip-1 107244585 bytes > 67108864
- M3.5 right L=117 rod: over budget: fine raw + gzip-1 109966737 bytes > 67108864
- M3.5 right L=120 rod: over budget: fine raw + gzip-1 112822144 bytes > 67108864
- M3.5 right L=123 rod: over budget: fine raw + gzip-1 115690254 bytes > 67108864
- M3.5 right L=126 rod: over budget: fine raw + gzip-1 118413978 bytes > 67108864
- M3.5 right L=129 rod: over budget: fine raw + gzip-1 121272742 bytes > 67108864
- M3.5 right L=132 rod: over budget: fine raw + gzip-1 124138521 bytes > 67108864
- M3.5 right L=135 rod: over budget: fine raw + gzip-1 126868659 bytes > 67108864
- M3.5 right L=138 rod: over budget: fine raw + gzip-1 129725899 bytes > 67108864
- M3.5 right L=141 rod: over budget: fine raw + gzip-1 132589778 bytes > 67108864
- M3.5 right L=144 rod: over budget: fine raw + gzip-1 135320632 bytes > 67108864
- M3.5 right L=147 rod: over budget: fine raw + gzip-1 138179304 bytes > 67108864
- M3.5 right L=150 rod: over budget: fine raw + gzip-1 141045322 bytes > 67108864
- M3.5 left L=90 rod: over budget: fine raw + gzip-1 69152656 bytes > 67108864
- M3.5 left L=93 rod: over budget: fine raw + gzip-1 71417352 bytes > 67108864
- M3.5 left L=96 rod: over budget: fine raw + gzip-1 73859563 bytes > 67108864
- M3.5 left L=99 rod: over budget: fine raw + gzip-1 76051692 bytes > 67108864
- M3.5 left L=102 rod: over budget: fine raw + gzip-1 78316770 bytes > 67108864
- M3.5 left L=105 rod: over budget: fine raw + gzip-1 80762197 bytes > 67108864
- M3.5 left L=108 rod: over budget: fine raw + gzip-1 82957602 bytes > 67108864
- M3.5 left L=111 rod: over budget: fine raw + gzip-1 85221667 bytes > 67108864
- M3.5 left L=114 rod: over budget: fine raw + gzip-1 87669123 bytes > 67108864
- M3.5 left L=117 rod: over budget: fine raw + gzip-1 89863831 bytes > 67108864
- M3.5 left L=120 rod: over budget: fine raw + gzip-1 92128220 bytes > 67108864
- M3.5 left L=123 rod: over budget: fine raw + gzip-1 94573873 bytes > 67108864
- M3.5 left L=126 rod: over budget: fine raw + gzip-1 96766686 bytes > 67108864
- M3.5 left L=129 rod: over budget: fine raw + gzip-1 99034638 bytes > 67108864
- M3.5 left L=132 rod: over budget: fine raw + gzip-1 101486812 bytes > 67108864
- M3.5 left L=135 rod: over budget: fine raw + gzip-1 103681946 bytes > 67108864
- M3.5 left L=138 rod: over budget: fine raw + gzip-1 105954859 bytes > 67108864
- M3.5 left L=141 rod: over budget: fine raw + gzip-1 108403698 bytes > 67108864
- M3.5 left L=144 rod: over budget: fine raw + gzip-1 110597607 bytes > 67108864
- M3.5 left L=147 rod: over budget: fine raw + gzip-1 112865616 bytes > 67108864
- M3.5 left L=150 rod: over budget: fine raw + gzip-1 115312509 bytes > 67108864
- M4 right L=70 rod: over budget: fine raw + gzip-1 68232344 bytes > 67108864
- M4 right L=73.5 rod: over budget: fine raw + gzip-1 71596605 bytes > 67108864
- M4 right L=77 rod: over budget: fine raw + gzip-1 74818344 bytes > 67108864
- M4 right L=80.5 rod: over budget: fine raw + gzip-1 78488899 bytes > 67108864
- M4 right L=84 rod: over budget: fine raw + gzip-1 81855862 bytes > 67108864
- M4 right L=87.5 rod: over budget: fine raw + gzip-1 85078470 bytes > 67108864
- M4 right L=91 rod: over budget: fine raw + gzip-1 88744158 bytes > 67108864
- M4 right L=94.5 rod: over budget: fine raw + gzip-1 92108130 bytes > 67108864
- M4 right L=98 rod: over budget: fine raw + gzip-1 95328280 bytes > 67108864
- M4 right L=101.5 rod: over budget: fine raw + gzip-1 99000094 bytes > 67108864
- M4 right L=105 rod: over budget: fine raw + gzip-1 102365224 bytes > 67108864
- M4 right L=108.5 rod: over budget: fine raw + gzip-1 105582835 bytes > 67108864
- M4 right L=112 rod: over budget: fine raw + gzip-1 109260525 bytes > 67108864
- M4 right L=115.5 rod: over budget: fine raw + gzip-1 112625893 bytes > 67108864
- M4 right L=119 rod: over budget: fine raw + gzip-1 115851046 bytes > 67108864
- M4 right L=122.5 rod: over budget: fine raw + gzip-1 119521965 bytes > 67108864
- M4 right L=126 rod: over budget: fine raw + gzip-1 122883851 bytes > 67108864
- M4 right L=129.5 rod: over budget: fine raw + gzip-1 126099463 bytes > 67108864
- M4 right L=133 rod: over budget: fine raw + gzip-1 129760283 bytes > 67108864
- M4 right L=136.5 rod: over budget: fine raw + gzip-1 133121476 bytes > 67108864
- M4 right L=140 rod: over budget: fine raw + gzip-1 136343474 bytes > 67108864
- M4 right L=143.5 rod: over budget: fine raw + gzip-1 140004090 bytes > 67108864
- M4 right L=147 rod: over budget: fine raw + gzip-1 143356382 bytes > 67108864
- M4 right L=150.5 rod: over budget: fine raw + gzip-1 146578209 bytes > 67108864
- M4 right L=154 rod: over budget: fine raw + gzip-1 150242105 bytes > 67108864
- M4 right L=157.5 rod: over budget: fine raw + gzip-1 153590978 bytes > 67108864
- M4 right L=161 rod: over budget: fine raw + gzip-1 156811877 bytes > 67108864
- M4 right L=164.5 rod: over budget: fine raw + gzip-1 160475777 bytes > 67108864
- M4 right L=168 rod: over budget: fine raw + gzip-1 163829436 bytes > 67108864
- M4 right L=171.5 rod: over budget: fine raw + gzip-1 167049693 bytes > 67108864
- M4 right L=175 rod: over budget: fine raw + gzip-1 170709745 bytes > 67108864
- M4 left L=94.5 rod: over budget: fine raw + gzip-1 67880051 bytes > 67108864
- M4 left L=98 rod: over budget: fine raw + gzip-1 70265532 bytes > 67108864
- M4 left L=101.5 rod: over budget: fine raw + gzip-1 72986449 bytes > 67108864
- M4 left L=105 rod: over budget: fine raw + gzip-1 75403702 bytes > 67108864
- M4 left L=108.5 rod: over budget: fine raw + gzip-1 77790312 bytes > 67108864
- M4 left L=112 rod: over budget: fine raw + gzip-1 80516564 bytes > 67108864
- M4 left L=115.5 rod: over budget: fine raw + gzip-1 82933391 bytes > 67108864
- M4 left L=119 rod: over budget: fine raw + gzip-1 85317794 bytes > 67108864
- M4 left L=122.5 rod: over budget: fine raw + gzip-1 88041559 bytes > 67108864
- M4 left L=126 rod: over budget: fine raw + gzip-1 90457416 bytes > 67108864
- M4 left L=129.5 rod: over budget: fine raw + gzip-1 92832144 bytes > 67108864
- M4 left L=133 rod: over budget: fine raw + gzip-1 95575519 bytes > 67108864
- M4 left L=136.5 rod: over budget: fine raw + gzip-1 98006682 bytes > 67108864
- M4 left L=140 rod: over budget: fine raw + gzip-1 100381404 bytes > 67108864
- M4 left L=143.5 rod: over budget: fine raw + gzip-1 103132059 bytes > 67108864
- M4 left L=147 rod: over budget: fine raw + gzip-1 105556649 bytes > 67108864
- M4 left L=150.5 rod: over budget: fine raw + gzip-1 107933361 bytes > 67108864
- M4 left L=154 rod: over budget: fine raw + gzip-1 110680550 bytes > 67108864
- M4 left L=157.5 rod: over budget: fine raw + gzip-1 113107594 bytes > 67108864
- M4 left L=161 rod: over budget: fine raw + gzip-1 115488965 bytes > 67108864
- M4 left L=164.5 rod: over budget: fine raw + gzip-1 118232802 bytes > 67108864
- M4 left L=168 rod: over budget: fine raw + gzip-1 120662437 bytes > 67108864
- M4 left L=171.5 rod: over budget: fine raw + gzip-1 123037802 bytes > 67108864
- M4 left L=175 rod: over budget: fine raw + gzip-1 125788476 bytes > 67108864
- M5 right L=80 rod: over budget: fine raw + gzip-1 69649908 bytes > 67108864
- M5 right L=84 rod: over budget: fine raw + gzip-1 73043035 bytes > 67108864
- M5 right L=88 rod: over budget: fine raw + gzip-1 76817922 bytes > 67108864
- M5 right L=92 rod: over budget: fine raw + gzip-1 80077211 bytes > 67108864
- M5 right L=96 rod: over budget: fine raw + gzip-1 83470766 bytes > 67108864
- M5 right L=100 rod: over budget: fine raw + gzip-1 87241919 bytes > 67108864
- M5 right L=104 rod: over budget: fine raw + gzip-1 90496836 bytes > 67108864
- M5 right L=108 rod: over budget: fine raw + gzip-1 93891864 bytes > 67108864
- M5 right L=112 rod: over budget: fine raw + gzip-1 97668147 bytes > 67108864
- M5 right L=116 rod: over budget: fine raw + gzip-1 100926428 bytes > 67108864
- M5 right L=120 rod: over budget: fine raw + gzip-1 104320176 bytes > 67108864
- M5 right L=124 rod: over budget: fine raw + gzip-1 108095274 bytes > 67108864
- M5 right L=128 rod: over budget: fine raw + gzip-1 111352506 bytes > 67108864
- M5 right L=132 rod: over budget: fine raw + gzip-1 114756566 bytes > 67108864
- M5 right L=136 rod: over budget: fine raw + gzip-1 118522319 bytes > 67108864
- M5 right L=140 rod: over budget: fine raw + gzip-1 121785285 bytes > 67108864
- M5 right L=144 rod: over budget: fine raw + gzip-1 125183719 bytes > 67108864
- M5 right L=148 rod: over budget: fine raw + gzip-1 128953520 bytes > 67108864
- M5 right L=152 rod: over budget: fine raw + gzip-1 132218173 bytes > 67108864
- M5 right L=156 rod: over budget: fine raw + gzip-1 135620111 bytes > 67108864
- M5 right L=160 rod: over budget: fine raw + gzip-1 139385527 bytes > 67108864
- M5 right L=164 rod: over budget: fine raw + gzip-1 142644051 bytes > 67108864
- M5 right L=168 rod: over budget: fine raw + gzip-1 146047483 bytes > 67108864
- M5 right L=172 rod: over budget: fine raw + gzip-1 149811790 bytes > 67108864
- M5 right L=176 rod: over budget: fine raw + gzip-1 153073409 bytes > 67108864
- M5 right L=180 rod: over budget: fine raw + gzip-1 156473534 bytes > 67108864
- M5 right L=184 rod: over budget: fine raw + gzip-1 160237012 bytes > 67108864
- M5 right L=188 rod: over budget: fine raw + gzip-1 163500014 bytes > 67108864
- M5 right L=192 rod: over budget: fine raw + gzip-1 166904754 bytes > 67108864
- M5 right L=196 rod: over budget: fine raw + gzip-1 170670810 bytes > 67108864
- M5 right L=200 rod: over budget: fine raw + gzip-1 173929849 bytes > 67108864
- M5 left L=108 rod: over budget: fine raw + gzip-1 69109433 bytes > 67108864
- M5 left L=112 rod: over budget: fine raw + gzip-1 72077398 bytes > 67108864
- M5 left L=116 rod: over budget: fine raw + gzip-1 74356930 bytes > 67108864
- M5 left L=120 rod: over budget: fine raw + gzip-1 76797315 bytes > 67108864
- M5 left L=124 rod: over budget: fine raw + gzip-1 79761995 bytes > 67108864
- M5 left L=128 rod: over budget: fine raw + gzip-1 82045128 bytes > 67108864
- M5 left L=132 rod: over budget: fine raw + gzip-1 84475639 bytes > 67108864
- M5 left L=136 rod: over budget: fine raw + gzip-1 87427028 bytes > 67108864
- M5 left L=140 rod: over budget: fine raw + gzip-1 89692952 bytes > 67108864
- M5 left L=144 rod: over budget: fine raw + gzip-1 92116975 bytes > 67108864
- M5 left L=148 rod: over budget: fine raw + gzip-1 95072926 bytes > 67108864
- M5 left L=152 rod: over budget: fine raw + gzip-1 97332203 bytes > 67108864
- M5 left L=156 rod: over budget: fine raw + gzip-1 99756270 bytes > 67108864
- M5 left L=160 rod: over budget: fine raw + gzip-1 102710051 bytes > 67108864
- M5 left L=164 rod: over budget: fine raw + gzip-1 104976212 bytes > 67108864
- M5 left L=168 rod: over budget: fine raw + gzip-1 107399043 bytes > 67108864
- M5 left L=172 rod: over budget: fine raw + gzip-1 110349772 bytes > 67108864
- M5 left L=176 rod: over budget: fine raw + gzip-1 112614612 bytes > 67108864
- M5 left L=180 rod: over budget: fine raw + gzip-1 115040132 bytes > 67108864
- M5 left L=184 rod: over budget: fine raw + gzip-1 117991872 bytes > 67108864
- M5 left L=188 rod: over budget: fine raw + gzip-1 120249561 bytes > 67108864
- M5 left L=192 rod: over budget: fine raw + gzip-1 122677983 bytes > 67108864
- M5 left L=196 rod: over budget: fine raw + gzip-1 125633024 bytes > 67108864
- M5 left L=200 rod: over budget: fine raw + gzip-1 127898472 bytes > 67108864
- M6 right L=95 rod: over budget: fine raw + gzip-1 70542573 bytes > 67108864
- M6 right L=100 rod: over budget: fine raw + gzip-1 73700701 bytes > 67108864
- M6 right L=105 rod: over budget: fine raw + gzip-1 77290194 bytes > 67108864
- M6 right L=110 rod: over budget: fine raw + gzip-1 81574265 bytes > 67108864
- M6 right L=115 rod: over budget: fine raw + gzip-1 84727511 bytes > 67108864
- M6 right L=120 rod: over budget: fine raw + gzip-1 88319272 bytes > 67108864
- M6 right L=125 rod: over budget: fine raw + gzip-1 92601555 bytes > 67108864
- M6 right L=130 rod: over budget: fine raw + gzip-1 95767719 bytes > 67108864
- M6 right L=135 rod: over budget: fine raw + gzip-1 99332716 bytes > 67108864
- M6 right L=140 rod: over budget: fine raw + gzip-1 103603821 bytes > 67108864
- M6 right L=145 rod: over budget: fine raw + gzip-1 106754226 bytes > 67108864
- M6 right L=150 rod: over budget: fine raw + gzip-1 110328831 bytes > 67108864
- M6 right L=155 rod: over budget: fine raw + gzip-1 114600671 bytes > 67108864
- M6 right L=160 rod: over budget: fine raw + gzip-1 117758537 bytes > 67108864
- M6 right L=165 rod: over budget: fine raw + gzip-1 121325319 bytes > 67108864
- M6 right L=170 rod: over budget: fine raw + gzip-1 125601103 bytes > 67108864
- M6 right L=175 rod: over budget: fine raw + gzip-1 128752677 bytes > 67108864
- M6 right L=180 rod: over budget: fine raw + gzip-1 132326106 bytes > 67108864
- M6 right L=185 rod: over budget: fine raw + gzip-1 136604181 bytes > 67108864
- M6 right L=190 rod: over budget: fine raw + gzip-1 139759259 bytes > 67108864
- M6 right L=195 rod: over budget: fine raw + gzip-1 143331272 bytes > 67108864
- M6 right L=200 rod: over budget: fine raw + gzip-1 147606455 bytes > 67108864
- M6 right L=205 rod: over budget: fine raw + gzip-1 150754160 bytes > 67108864
- M6 right L=210 rod: over budget: fine raw + gzip-1 154323145 bytes > 67108864
- M6 right L=215 rod: over budget: fine raw + gzip-1 158595112 bytes > 67108864
- M6 right L=220 rod: over budget: fine raw + gzip-1 161747698 bytes > 67108864
- M6 right L=225 rod: over budget: fine raw + gzip-1 165326190 bytes > 67108864
- M6 right L=230 rod: over budget: fine raw + gzip-1 169603096 bytes > 67108864
- M6 right L=235 rod: over budget: fine raw + gzip-1 172759332 bytes > 67108864
- M6 right L=240 rod: over budget: fine raw + gzip-1 176326814 bytes > 67108864
- M6 right L=245 rod: over budget: fine raw + gzip-1 180596944 bytes > 67108864
- M6 right L=250 rod: over budget: fine raw + gzip-1 183750700 bytes > 67108864
- M6 left L=125 rod: over budget: fine raw + gzip-1 69503354 bytes > 67108864
- M6 left L=130 rod: over budget: fine raw + gzip-1 71963378 bytes > 67108864
- M6 left L=135 rod: over budget: fine raw + gzip-1 74582441 bytes > 67108864
- M6 left L=140 rod: over budget: fine raw + gzip-1 77777139 bytes > 67108864
- M6 left L=145 rod: over budget: fine raw + gzip-1 80260412 bytes > 67108864
- M6 left L=150 rod: over budget: fine raw + gzip-1 82876995 bytes > 67108864
- M6 left L=155 rod: over budget: fine raw + gzip-1 86076084 bytes > 67108864
- M6 left L=160 rod: over budget: fine raw + gzip-1 88555722 bytes > 67108864
- M6 left L=165 rod: over budget: fine raw + gzip-1 91174858 bytes > 67108864
- M6 left L=170 rod: over budget: fine raw + gzip-1 94373649 bytes > 67108864
- M6 left L=175 rod: over budget: fine raw + gzip-1 96851916 bytes > 67108864
- M6 left L=180 rod: over budget: fine raw + gzip-1 99475098 bytes > 67108864
- M6 left L=185 rod: over budget: fine raw + gzip-1 102670241 bytes > 67108864
- M6 left L=190 rod: over budget: fine raw + gzip-1 105153845 bytes > 67108864
- M6 left L=195 rod: over budget: fine raw + gzip-1 107773715 bytes > 67108864
- M6 left L=200 rod: over budget: fine raw + gzip-1 110972130 bytes > 67108864
- M6 left L=205 rod: over budget: fine raw + gzip-1 113452672 bytes > 67108864
- M6 left L=210 rod: over budget: fine raw + gzip-1 116066734 bytes > 67108864
- M6 left L=215 rod: over budget: fine raw + gzip-1 119270578 bytes > 67108864
- M6 left L=220 rod: over budget: fine raw + gzip-1 121742196 bytes > 67108864
- M6 left L=225 rod: over budget: fine raw + gzip-1 124363193 bytes > 67108864
- M6 left L=230 rod: over budget: fine raw + gzip-1 127560381 bytes > 67108864
- M6 left L=235 rod: over budget: fine raw + gzip-1 130036882 bytes > 67108864
- M6 left L=240 rod: over budget: fine raw + gzip-1 132655138 bytes > 67108864
- M6 left L=245 rod: over budget: fine raw + gzip-1 135855360 bytes > 67108864
- M6 left L=250 rod: over budget: fine raw + gzip-1 138336419 bytes > 67108864
- M7 right L=90 rod: over budget: fine raw + gzip-1 69152475 bytes > 67108864
- M7 right L=95 rod: over budget: fine raw + gzip-1 73596804 bytes > 67108864
- M7 right L=100 rod: over budget: fine raw + gzip-1 77205832 bytes > 67108864
- M7 right L=105 rod: over budget: fine raw + gzip-1 80674566 bytes > 67108864
- M7 right L=110 rod: over budget: fine raw + gzip-1 85117151 bytes > 67108864
- M7 right L=115 rod: over budget: fine raw + gzip-1 88727208 bytes > 67108864
- M7 right L=120 rod: over budget: fine raw + gzip-1 92196168 bytes > 67108864
- M7 right L=125 rod: over budget: fine raw + gzip-1 96639182 bytes > 67108864
- M7 right L=130 rod: over budget: fine raw + gzip-1 100248527 bytes > 67108864
- M7 right L=135 rod: over budget: fine raw + gzip-1 103713307 bytes > 67108864
- M7 right L=140 rod: over budget: fine raw + gzip-1 108159603 bytes > 67108864
- M7 right L=145 rod: over budget: fine raw + gzip-1 111761387 bytes > 67108864
- M7 right L=150 rod: over budget: fine raw + gzip-1 115223162 bytes > 67108864
- M7 right L=155 rod: over budget: fine raw + gzip-1 119665272 bytes > 67108864
- M7 right L=160 rod: over budget: fine raw + gzip-1 123265208 bytes > 67108864
- M7 right L=165 rod: over budget: fine raw + gzip-1 126729882 bytes > 67108864
- M7 right L=170 rod: over budget: fine raw + gzip-1 131171399 bytes > 67108864
- M7 right L=175 rod: over budget: fine raw + gzip-1 134778757 bytes > 67108864
- M7 right L=180 rod: over budget: fine raw + gzip-1 138246382 bytes > 67108864
- M7 right L=185 rod: over budget: fine raw + gzip-1 142692849 bytes > 67108864
- M7 right L=190 rod: over budget: fine raw + gzip-1 146294743 bytes > 67108864
- M7 right L=195 rod: over budget: fine raw + gzip-1 149758858 bytes > 67108864
- M7 right L=200 rod: over budget: fine raw + gzip-1 154202876 bytes > 67108864
- M7 right L=205 rod: over budget: fine raw + gzip-1 157807148 bytes > 67108864
- M7 right L=210 rod: over budget: fine raw + gzip-1 161267664 bytes > 67108864
- M7 right L=215 rod: over budget: fine raw + gzip-1 165710822 bytes > 67108864
- M7 right L=220 rod: over budget: fine raw + gzip-1 169310800 bytes > 67108864
- M7 right L=225 rod: over budget: fine raw + gzip-1 172772795 bytes > 67108864
- M7 right L=230 rod: over budget: fine raw + gzip-1 177217469 bytes > 67108864
- M7 right L=235 rod: over budget: fine raw + gzip-1 180812238 bytes > 67108864
- M7 right L=240 rod: over budget: fine raw + gzip-1 184276570 bytes > 67108864
- M7 right L=245 rod: over budget: fine raw + gzip-1 188721540 bytes > 67108864
- M7 right L=250 rod: over budget: fine raw + gzip-1 192324208 bytes > 67108864
- M7 left L=115 rod: over budget: fine raw + gzip-1 67818314 bytes > 67108864
- M7 left L=120 rod: over budget: fine raw + gzip-1 70326620 bytes > 67108864
- M7 left L=125 rod: over budget: fine raw + gzip-1 73699415 bytes > 67108864
- M7 left L=130 rod: over budget: fine raw + gzip-1 76604143 bytes > 67108864
- M7 left L=135 rod: over budget: fine raw + gzip-1 79111770 bytes > 67108864
- M7 left L=140 rod: over budget: fine raw + gzip-1 82479506 bytes > 67108864
- M7 left L=145 rod: over budget: fine raw + gzip-1 85386207 bytes > 67108864
- M7 left L=150 rod: over budget: fine raw + gzip-1 87892415 bytes > 67108864
- M7 left L=155 rod: over budget: fine raw + gzip-1 91263592 bytes > 67108864
- M7 left L=160 rod: over budget: fine raw + gzip-1 94172151 bytes > 67108864
- M7 left L=165 rod: over budget: fine raw + gzip-1 96673278 bytes > 67108864
- M7 left L=170 rod: over budget: fine raw + gzip-1 100045874 bytes > 67108864
- M7 left L=175 rod: over budget: fine raw + gzip-1 102952987 bytes > 67108864
- M7 left L=180 rod: over budget: fine raw + gzip-1 105455733 bytes > 67108864
- M7 left L=185 rod: over budget: fine raw + gzip-1 108826943 bytes > 67108864
- M7 left L=190 rod: over budget: fine raw + gzip-1 111728755 bytes > 67108864
- M7 left L=195 rod: over budget: fine raw + gzip-1 114232164 bytes > 67108864
- M7 left L=200 rod: over budget: fine raw + gzip-1 117600126 bytes > 67108864
- M7 left L=205 rod: over budget: fine raw + gzip-1 120505131 bytes > 67108864
- M7 left L=210 rod: over budget: fine raw + gzip-1 123012070 bytes > 67108864
- M7 left L=215 rod: over budget: fine raw + gzip-1 126382857 bytes > 67108864
- M7 left L=220 rod: over budget: fine raw + gzip-1 129291239 bytes > 67108864
- M7 left L=225 rod: over budget: fine raw + gzip-1 131795621 bytes > 67108864
- M7 left L=230 rod: over budget: fine raw + gzip-1 135166581 bytes > 67108864
- M7 left L=235 rod: over budget: fine raw + gzip-1 138070868 bytes > 67108864
- M7 left L=240 rod: over budget: fine raw + gzip-1 140573375 bytes > 67108864
- M7 left L=245 rod: over budget: fine raw + gzip-1 143943438 bytes > 67108864
- M7 left L=250 rod: over budget: fine raw + gzip-1 146846965 bytes > 67108864
- M8 right L=81.25 rod: over budget: fine raw + gzip-1 80459682 bytes > 67108864
- M8 right L=87.5 rod: over budget: fine raw + gzip-1 87070535 bytes > 67108864
- M8 right L=93.75 rod: over budget: fine raw + gzip-1 93095880 bytes > 67108864
- M8 right L=100 rod: over budget: fine raw + gzip-1 99064744 bytes > 67108864
- M8 right L=106.25 rod: over budget: fine raw + gzip-1 105668489 bytes > 67108864
- M8 right L=112.5 rod: over budget: fine raw + gzip-1 111699716 bytes > 67108864
- M8 right L=118.75 rod: over budget: fine raw + gzip-1 117674312 bytes > 67108864
- M8 right L=125 rod: over budget: fine raw + gzip-1 124277989 bytes > 67108864
- M8 right L=131.25 rod: over budget: fine raw + gzip-1 130318555 bytes > 67108864
- M8 right L=137.5 rod: over budget: fine raw + gzip-1 136288344 bytes > 67108864
- M8 right L=143.75 rod: over budget: fine raw + gzip-1 142895978 bytes > 67108864
- M8 right L=150 rod: over budget: fine raw + gzip-1 148933228 bytes > 67108864
- M8 right L=156.25 rod: over budget: fine raw + gzip-1 154902152 bytes > 67108864
- M8 right L=162.5 rod: over budget: fine raw + gzip-1 161512794 bytes > 67108864
- M8 right L=168.75 rod: over budget: fine raw + gzip-1 167545611 bytes > 67108864
- M8 right L=175 rod: over budget: fine raw + gzip-1 173515921 bytes > 67108864
- M8 right L=181.25 rod: over budget: fine raw + gzip-1 180123765 bytes > 67108864
- M8 right L=187.5 rod: over budget: fine raw + gzip-1 186154501 bytes > 67108864
- M8 right L=193.75 rod: over budget: fine raw + gzip-1 192120367 bytes > 67108864
- M8 right L=200 rod: over budget: fine raw + gzip-1 198732348 bytes > 67108864
- M8 right L=206.25 rod: over budget: fine raw + gzip-1 204761826 bytes > 67108864
- M8 right L=212.5 rod: over budget: fine raw + gzip-1 210735018 bytes > 67108864
- M8 right L=218.75 rod: over budget: fine raw + gzip-1 217339494 bytes > 67108864
- M8 right L=225 rod: over budget: fine raw + gzip-1 223371838 bytes > 67108864
- M8 right L=231.25 rod: over budget: fine raw + gzip-1 229341971 bytes > 67108864
- M8 right L=237.5 rod: over budget: fine raw + gzip-1 235943432 bytes > 67108864
- M8 right L=243.75 rod: over budget: fine raw + gzip-1 241980306 bytes > 67108864
- M8 right L=250 rod: over budget: fine raw + gzip-1 247953321 bytes > 67108864
- M8 right L=256.25 rod: over budget: fine raw + gzip-1 254568765 bytes > 67108864
- M8 right L=262.5 rod: over budget: fine raw + gzip-1 260578760 bytes > 67108864
- M8 right L=268.75 rod: over budget: fine raw + gzip-1 266543482 bytes > 67108864
- M8 right L=275 rod: over budget: fine raw + gzip-1 273144675 bytes > 67108864
- M8 right L=281.25 rod: over budget: fine raw + gzip-1 279165681 bytes > 67108864
- M8 right L=287.5 rod: over budget: fine raw + gzip-1 285131895 bytes > 67108864
- M8 right L=293.75 rod: over budget: fine raw + gzip-1 291726409 bytes > 67108864
- M8 right L=300 rod: over budget: fine raw + gzip-1 297752912 bytes > 67108864
- M8 right L=306.25 rod: over budget: fine raw + gzip-1 303717483 bytes > 67108864
- M8 right L=312.5 rod: over budget: fine raw + gzip-1 310319264 bytes > 67108864
- M8 left L=87.5 rod: over budget: fine raw + gzip-1 71921834 bytes > 67108864
- M8 left L=93.75 rod: over budget: fine raw + gzip-1 76898279 bytes > 67108864
- M8 left L=100 rod: over budget: fine raw + gzip-1 81674088 bytes > 67108864
- M8 left L=106.25 rod: over budget: fine raw + gzip-1 87281058 bytes > 67108864
- M8 left L=112.5 rod: over budget: fine raw + gzip-1 92258597 bytes > 67108864
- M8 left L=118.75 rod: over budget: fine raw + gzip-1 97034376 bytes > 67108864
- M8 left L=125 rod: over budget: fine raw + gzip-1 102644189 bytes > 67108864
- M8 left L=131.25 rod: over budget: fine raw + gzip-1 107621291 bytes > 67108864
- M8 left L=137.5 rod: over budget: fine raw + gzip-1 112395217 bytes > 67108864
- M8 left L=143.75 rod: over budget: fine raw + gzip-1 117994205 bytes > 67108864
- M8 left L=150 rod: over budget: fine raw + gzip-1 122970681 bytes > 67108864
- M8 left L=156.25 rod: over budget: fine raw + gzip-1 127741714 bytes > 67108864
- M8 left L=162.5 rod: over budget: fine raw + gzip-1 133354902 bytes > 67108864
- M8 left L=168.75 rod: over budget: fine raw + gzip-1 138330748 bytes > 67108864
- M8 left L=175 rod: over budget: fine raw + gzip-1 143107734 bytes > 67108864
- M8 left L=181.25 rod: over budget: fine raw + gzip-1 148706591 bytes > 67108864
- M8 left L=187.5 rod: over budget: fine raw + gzip-1 153684714 bytes > 67108864
- M8 left L=193.75 rod: over budget: fine raw + gzip-1 158459128 bytes > 67108864
- M8 left L=200 rod: over budget: fine raw + gzip-1 164061902 bytes > 67108864
- M8 left L=206.25 rod: over budget: fine raw + gzip-1 169041668 bytes > 67108864
- M8 left L=212.5 rod: over budget: fine raw + gzip-1 173811416 bytes > 67108864
- M8 left L=218.75 rod: over budget: fine raw + gzip-1 179415653 bytes > 67108864
- M8 left L=225 rod: over budget: fine raw + gzip-1 184395158 bytes > 67108864
- M8 left L=231.25 rod: over budget: fine raw + gzip-1 189168865 bytes > 67108864
- M8 left L=237.5 rod: over budget: fine raw + gzip-1 194781412 bytes > 67108864
- M8 left L=243.75 rod: over budget: fine raw + gzip-1 199757775 bytes > 67108864
- M8 left L=250 rod: over budget: fine raw + gzip-1 204531684 bytes > 67108864
- M8 left L=256.25 rod: over budget: fine raw + gzip-1 210136865 bytes > 67108864
- M8 left L=262.5 rod: over budget: fine raw + gzip-1 215166527 bytes > 67108864
- M8 left L=268.75 rod: over budget: fine raw + gzip-1 219975189 bytes > 67108864
- M8 left L=275 rod: over budget: fine raw + gzip-1 225619766 bytes > 67108864
- M8 left L=281.25 rod: over budget: fine raw + gzip-1 230639730 bytes > 67108864
- M8 left L=287.5 rod: over budget: fine raw + gzip-1 235440620 bytes > 67108864
- M8 left L=293.75 rod: over budget: fine raw + gzip-1 241085928 bytes > 67108864
- M8 left L=300 rod: over budget: fine raw + gzip-1 246108147 bytes > 67108864
- M8 left L=306.25 rod: over budget: fine raw + gzip-1 250910693 bytes > 67108864
- M8 left L=312.5 rod: over budget: fine raw + gzip-1 256552004 bytes > 67108864
- M10 right L=105 rod: over budget: fine raw + gzip-1 124529057 bytes > 67108864
- M10 right L=112.5 rod: over budget: fine raw + gzip-1 133387510 bytes > 67108864
- M10 right L=120 rod: over budget: fine raw + gzip-1 142096885 bytes > 67108864
- M10 right L=127.5 rod: over budget: fine raw + gzip-1 151197460 bytes > 67108864
- M10 right L=135 rod: over budget: fine raw + gzip-1 160050458 bytes > 67108864
- M10 right L=142.5 rod: over budget: fine raw + gzip-1 168750652 bytes > 67108864
- M10 right L=150 rod: over budget: fine raw + gzip-1 177863798 bytes > 67108864
- M10 right L=157.5 rod: over budget: fine raw + gzip-1 186712319 bytes > 67108864
- M10 right L=165 rod: over budget: fine raw + gzip-1 195413141 bytes > 67108864
- M10 right L=172.5 rod: over budget: fine raw + gzip-1 204523907 bytes > 67108864
- M10 right L=180 rod: over budget: fine raw + gzip-1 213372198 bytes > 67108864
- M10 right L=187.5 rod: over budget: fine raw + gzip-1 222075869 bytes > 67108864
- M10 right L=195 rod: over budget: fine raw + gzip-1 231183017 bytes > 67108864
- M10 right L=202.5 rod: over budget: fine raw + gzip-1 240034752 bytes > 67108864
- M10 right L=210 rod: over budget: fine raw + gzip-1 248729451 bytes > 67108864
- M10 right L=217.5 rod: over budget: fine raw + gzip-1 257837667 bytes > 67108864
- M10 right L=225 rod: over budget: fine raw + gzip-1 266690695 bytes > 67108864
- M10 right L=232.5 rod: over budget: fine raw + gzip-1 275390874 bytes > 67108864
- M10 right L=240 rod: over budget: fine raw + gzip-1 284496838 bytes > 67108864
- M10 right L=247.5 rod: over budget: fine raw + gzip-1 293344677 bytes > 67108864
- M10 right L=255 rod: over budget: fine raw + gzip-1 302037700 bytes > 67108864
- M10 right L=262.5 rod: over budget: fine raw + gzip-1 311138778 bytes > 67108864
- M10 right L=270 rod: over budget: fine raw + gzip-1 320004247 bytes > 67108864
- M10 right L=277.5 rod: over budget: fine raw + gzip-1 328704904 bytes > 67108864
- M10 right L=285 rod: over budget: fine raw + gzip-1 337817695 bytes > 67108864
- M10 right L=292.5 rod: over budget: fine raw + gzip-1 346676883 bytes > 67108864
- M10 right L=300 rod: over budget: fine raw + gzip-1 355374615 bytes > 67108864
- M10 right L=307.5 rod: over budget: fine raw + gzip-1 364483746 bytes > 67108864
- M10 right L=315 rod: over budget: fine raw + gzip-1 373342039 bytes > 67108864
- M10 right L=322.5 rod: over budget: fine raw + gzip-1 382044822 bytes > 67108864
- M10 right L=330 rod: over budget: fine raw + gzip-1 391152026 bytes > 67108864
- M10 right L=337.5 rod: over budget: fine raw + gzip-1 400009727 bytes > 67108864
- M10 right L=345 rod: over budget: fine raw + gzip-1 408704994 bytes > 67108864
- M10 right L=352.5 rod: over budget: fine raw + gzip-1 417823256 bytes > 67108864
- M10 right L=360 rod: over budget: fine raw + gzip-1 426683496 bytes > 67108864
- M10 right L=367.5 rod: over budget: fine raw + gzip-1 435383247 bytes > 67108864
- M10 right L=375 rod: over budget: fine raw + gzip-1 444489267 bytes > 67108864
- M10 left L=105 rod: over budget: fine raw + gzip-1 96889010 bytes > 67108864
- M10 left L=112.5 rod: over budget: fine raw + gzip-1 103676916 bytes > 67108864
- M10 left L=120 rod: over budget: fine raw + gzip-1 110243138 bytes > 67108864
- M10 left L=127.5 rod: over budget: fine raw + gzip-1 117621952 bytes > 67108864
- M10 left L=135 rod: over budget: fine raw + gzip-1 124413930 bytes > 67108864
- M10 left L=142.5 rod: over budget: fine raw + gzip-1 130981977 bytes > 67108864
- M10 left L=150 rod: over budget: fine raw + gzip-1 138350770 bytes > 67108864
- M10 left L=157.5 rod: over budget: fine raw + gzip-1 145140282 bytes > 67108864
- M10 left L=165 rod: over budget: fine raw + gzip-1 151706264 bytes > 67108864
- M10 left L=172.5 rod: over budget: fine raw + gzip-1 159075982 bytes > 67108864
- M10 left L=180 rod: over budget: fine raw + gzip-1 165863020 bytes > 67108864
- M10 left L=187.5 rod: over budget: fine raw + gzip-1 172425846 bytes > 67108864
- M10 left L=195 rod: over budget: fine raw + gzip-1 179798121 bytes > 67108864
- M10 left L=202.5 rod: over budget: fine raw + gzip-1 186588208 bytes > 67108864
- M10 left L=210 rod: over budget: fine raw + gzip-1 193148557 bytes > 67108864
- M10 left L=217.5 rod: over budget: fine raw + gzip-1 200533857 bytes > 67108864
- M10 left L=225 rod: over budget: fine raw + gzip-1 207315431 bytes > 67108864
- M10 left L=232.5 rod: over budget: fine raw + gzip-1 213883423 bytes > 67108864
- M10 left L=240 rod: over budget: fine raw + gzip-1 221250537 bytes > 67108864
- M10 left L=247.5 rod: over budget: fine raw + gzip-1 228040113 bytes > 67108864
- M10 left L=255 rod: over budget: fine raw + gzip-1 234597655 bytes > 67108864
- M10 left L=262.5 rod: over budget: fine raw + gzip-1 241964382 bytes > 67108864
- M10 left L=270 rod: over budget: fine raw + gzip-1 248721378 bytes > 67108864
- M10 left L=277.5 rod: over budget: fine raw + gzip-1 255280519 bytes > 67108864
- M10 left L=285 rod: over budget: fine raw + gzip-1 262642521 bytes > 67108864
- M10 left L=292.5 rod: over budget: fine raw + gzip-1 269422074 bytes > 67108864
- M10 left L=300 rod: over budget: fine raw + gzip-1 275979867 bytes > 67108864
- M10 left L=307.5 rod: over budget: fine raw + gzip-1 283337744 bytes > 67108864
- M10 left L=315 rod: over budget: fine raw + gzip-1 290113330 bytes > 67108864
- M10 left L=322.5 rod: over budget: fine raw + gzip-1 296677233 bytes > 67108864
- M10 left L=330 rod: over budget: fine raw + gzip-1 304023083 bytes > 67108864
- M10 left L=337.5 rod: over budget: fine raw + gzip-1 310804556 bytes > 67108864
- M10 left L=345 rod: over budget: fine raw + gzip-1 317360459 bytes > 67108864
- M10 left L=352.5 rod: over budget: fine raw + gzip-1 324739667 bytes > 67108864
- M10 left L=360 rod: over budget: fine raw + gzip-1 331490277 bytes > 67108864
- M10 left L=367.5 rod: over budget: fine raw + gzip-1 338054330 bytes > 67108864
- M10 left L=375 rod: over budget: fine raw + gzip-1 345427675 bytes > 67108864
- M12 right L=122.5 rod: over budget: fine raw + gzip-1 134800928 bytes > 67108864
- M12 right L=131.25 rod: over budget: fine raw + gzip-1 144113772 bytes > 67108864
- M12 right L=140 rod: over budget: fine raw + gzip-1 153766882 bytes > 67108864
- M12 right L=148.75 rod: over budget: fine raw + gzip-1 163617501 bytes > 67108864
- M12 right L=157.5 rod: over budget: fine raw + gzip-1 172915310 bytes > 67108864
- M12 right L=166.25 rod: over budget: fine raw + gzip-1 182571799 bytes > 67108864
- M12 right L=175 rod: over budget: fine raw + gzip-1 192418736 bytes > 67108864
- M12 right L=183.75 rod: over budget: fine raw + gzip-1 201707883 bytes > 67108864
- M12 right L=192.5 rod: over budget: fine raw + gzip-1 211356429 bytes > 67108864
- M12 right L=201.25 rod: over budget: fine raw + gzip-1 221193657 bytes > 67108864
- M12 right L=210 rod: over budget: fine raw + gzip-1 230493848 bytes > 67108864
- M12 right L=218.75 rod: over budget: fine raw + gzip-1 240148175 bytes > 67108864
- M12 right L=227.5 rod: over budget: fine raw + gzip-1 249987578 bytes > 67108864
- M12 right L=236.25 rod: over budget: fine raw + gzip-1 259277140 bytes > 67108864
- M12 right L=245 rod: over budget: fine raw + gzip-1 268925848 bytes > 67108864
- M12 right L=253.75 rod: over budget: fine raw + gzip-1 278771738 bytes > 67108864
- M12 right L=262.5 rod: over budget: fine raw + gzip-1 288078595 bytes > 67108864
- M12 right L=271.25 rod: over budget: fine raw + gzip-1 297732777 bytes > 67108864
- M12 right L=280 rod: over budget: fine raw + gzip-1 307598835 bytes > 67108864
- M12 right L=288.75 rod: over budget: fine raw + gzip-1 316904621 bytes > 67108864
- M12 right L=297.5 rod: over budget: fine raw + gzip-1 326558101 bytes > 67108864
- M12 right L=306.25 rod: over budget: fine raw + gzip-1 336423177 bytes > 67108864
- M12 right L=315 rod: over budget: fine raw + gzip-1 345733429 bytes > 67108864
- M12 right L=323.75 rod: over budget: fine raw + gzip-1 355388652 bytes > 67108864
- M12 right L=332.5 rod: over budget: fine raw + gzip-1 365250893 bytes > 67108864
- M12 right L=341.25 rod: over budget: fine raw + gzip-1 374566295 bytes > 67108864
- M12 right L=350 rod: over budget: fine raw + gzip-1 384219964 bytes > 67108864
- M12 right L=358.75 rod: over budget: fine raw + gzip-1 394084563 bytes > 67108864
- M12 right L=367.5 rod: over budget: fine raw + gzip-1 403401801 bytes > 67108864
- M12 right L=376.25 rod: over budget: fine raw + gzip-1 413064088 bytes > 67108864
- M12 right L=385 rod: over budget: fine raw + gzip-1 422922472 bytes > 67108864
- M12 right L=393.75 rod: over budget: fine raw + gzip-1 432237515 bytes > 67108864
- M12 right L=402.5 rod: over budget: fine raw + gzip-1 441899499 bytes > 67108864
- M12 right L=411.25 rod: over budget: fine raw + gzip-1 451770357 bytes > 67108864
- M12 right L=420 rod: over budget: fine raw + gzip-1 461086605 bytes > 67108864
- M12 right L=428.75 rod: over budget: fine raw + gzip-1 470740595 bytes > 67108864
- M12 right L=437.5 rod: over budget: fine raw + gzip-1 480601483 bytes > 67108864
- M12 left L=122.5 rod: over budget: fine raw + gzip-1 107015383 bytes > 67108864
- M12 left L=131.25 rod: over budget: fine raw + gzip-1 114391342 bytes > 67108864
- M12 left L=140 rod: over budget: fine raw + gzip-1 121733493 bytes > 67108864
- M12 left L=148.75 rod: over budget: fine raw + gzip-1 129879051 bytes > 67108864
- M12 left L=157.5 rod: over budget: fine raw + gzip-1 137261017 bytes > 67108864
- M12 left L=166.25 rod: over budget: fine raw + gzip-1 144603711 bytes > 67108864
- M12 left L=175 rod: over budget: fine raw + gzip-1 152740186 bytes > 67108864
- M12 left L=183.75 rod: over budget: fine raw + gzip-1 160121750 bytes > 67108864
- M12 left L=192.5 rod: over budget: fine raw + gzip-1 167461871 bytes > 67108864
- M12 left L=201.25 rod: over budget: fine raw + gzip-1 175612686 bytes > 67108864
- M12 left L=210 rod: over budget: fine raw + gzip-1 182988059 bytes > 67108864
- M12 left L=218.75 rod: over budget: fine raw + gzip-1 190322843 bytes > 67108864
- M12 left L=227.5 rod: over budget: fine raw + gzip-1 198472106 bytes > 67108864
- M12 left L=236.25 rod: over budget: fine raw + gzip-1 205850148 bytes > 67108864
- M12 left L=245 rod: over budget: fine raw + gzip-1 213199140 bytes > 67108864
- M12 left L=253.75 rod: over budget: fine raw + gzip-1 221344138 bytes > 67108864
- M12 left L=262.5 rod: over budget: fine raw + gzip-1 228728935 bytes > 67108864
- M12 left L=271.25 rod: over budget: fine raw + gzip-1 236074243 bytes > 67108864
- M12 left L=280 rod: over budget: fine raw + gzip-1 244205682 bytes > 67108864
- M12 left L=288.75 rod: over budget: fine raw + gzip-1 251569449 bytes > 67108864
- M12 left L=297.5 rod: over budget: fine raw + gzip-1 258904408 bytes > 67108864
- M12 left L=306.25 rod: over budget: fine raw + gzip-1 267030671 bytes > 67108864
- M12 left L=315 rod: over budget: fine raw + gzip-1 274383606 bytes > 67108864
- M12 left L=323.75 rod: over budget: fine raw + gzip-1 281720592 bytes > 67108864
- M12 left L=332.5 rod: over budget: fine raw + gzip-1 289852203 bytes > 67108864
- M12 left L=341.25 rod: over budget: fine raw + gzip-1 297214356 bytes > 67108864
- M12 left L=350 rod: over budget: fine raw + gzip-1 304551903 bytes > 67108864
- M12 left L=358.75 rod: over budget: fine raw + gzip-1 312675925 bytes > 67108864
- M12 left L=367.5 rod: over budget: fine raw + gzip-1 320036415 bytes > 67108864
- M12 left L=376.25 rod: over budget: fine raw + gzip-1 327367152 bytes > 67108864
- M12 left L=385 rod: over budget: fine raw + gzip-1 335484986 bytes > 67108864
- M12 left L=393.75 rod: over budget: fine raw + gzip-1 342832497 bytes > 67108864
- M12 left L=402.5 rod: over budget: fine raw + gzip-1 350166788 bytes > 67108864
- M12 left L=411.25 rod: over budget: fine raw + gzip-1 358290184 bytes > 67108864
- M12 left L=420 rod: over budget: fine raw + gzip-1 365655607 bytes > 67108864
- M12 left L=428.75 rod: over budget: fine raw + gzip-1 372994758 bytes > 67108864
- M12 left L=437.5 rod: over budget: fine raw + gzip-1 381125943 bytes > 67108864
- M14 right L=150 rod: over budget: fine raw + gzip-1 171864326 bytes > 67108864
- M14 right L=160 rod: over budget: fine raw + gzip-1 182790414 bytes > 67108864
- M14 right L=170 rod: over budget: fine raw + gzip-1 194939130 bytes > 67108864
- M14 right L=180 rod: over budget: fine raw + gzip-1 206211178 bytes > 67108864
- M14 right L=190 rod: over budget: fine raw + gzip-1 217136949 bytes > 67108864
- M14 right L=200 rod: over budget: fine raw + gzip-1 229281587 bytes > 67108864
- M14 right L=210 rod: over budget: fine raw + gzip-1 240551817 bytes > 67108864
- M14 right L=220 rod: over budget: fine raw + gzip-1 251473595 bytes > 67108864
- M14 right L=230 rod: over budget: fine raw + gzip-1 263618938 bytes > 67108864
- M14 right L=240 rod: over budget: fine raw + gzip-1 274889529 bytes > 67108864
- M14 right L=250 rod: over budget: fine raw + gzip-1 285815776 bytes > 67108864
- M14 right L=260 rod: over budget: fine raw + gzip-1 297968608 bytes > 67108864
- M14 right L=270 rod: over budget: fine raw + gzip-1 309221714 bytes > 67108864
- M14 right L=280 rod: over budget: fine raw + gzip-1 320130955 bytes > 67108864
- M14 right L=290 rod: over budget: fine raw + gzip-1 332276358 bytes > 67108864
- M14 right L=300 rod: over budget: fine raw + gzip-1 343530541 bytes > 67108864
- M14 right L=310 rod: over budget: fine raw + gzip-1 354433842 bytes > 67108864
- M14 right L=320 rod: over budget: fine raw + gzip-1 366580515 bytes > 67108864
- M14 right L=330 rod: over budget: fine raw + gzip-1 377831221 bytes > 67108864
- M14 right L=340 rod: over budget: fine raw + gzip-1 388735691 bytes > 67108864
- M14 right L=350 rod: over budget: fine raw + gzip-1 400893034 bytes > 67108864
- M14 right L=360 rod: over budget: fine raw + gzip-1 412144651 bytes > 67108864
- M14 right L=370 rod: over budget: fine raw + gzip-1 423051961 bytes > 67108864
- M14 right L=380 rod: over budget: fine raw + gzip-1 435198015 bytes > 67108864
- M14 right L=390 rod: over budget: fine raw + gzip-1 446436930 bytes > 67108864
- M14 right L=400 rod: over budget: fine raw + gzip-1 457346523 bytes > 67108864
- M14 right L=410 rod: over budget: fine raw + gzip-1 469500819 bytes > 67108864
- M14 right L=420 rod: over budget: fine raw + gzip-1 480743967 bytes > 67108864
- M14 right L=430 rod: over budget: fine raw + gzip-1 491648350 bytes > 67108864
- M14 right L=440 rod: over budget: fine raw + gzip-1 503796966 bytes > 67108864
- M14 right L=450 rod: over budget: fine raw + gzip-1 515036206 bytes > 67108864
- M14 right L=460 rod: over budget: fine raw + gzip-1 525938916 bytes > 67108864
- M14 right L=470 rod: over budget: fine raw + gzip-1 538098151 bytes > 67108864
- M14 right L=480 rod: over budget: fine raw + gzip-1 549337383 bytes > 67108864
- M14 right L=490 rod: over budget: fine raw + gzip-1 560241174 bytes > 67108864
- M14 right L=500 rod: over budget: fine raw + gzip-1 572394494 bytes > 67108864
- M14 left L=150 rod: over budget: fine raw + gzip-1 128936050 bytes > 67108864
- M14 left L=160 rod: over budget: fine raw + gzip-1 137048739 bytes > 67108864
- M14 left L=170 rod: over budget: fine raw + gzip-1 146348099 bytes > 67108864
- M14 left L=180 rod: over budget: fine raw + gzip-1 154692916 bytes > 67108864
- M14 left L=190 rod: over budget: fine raw + gzip-1 162805024 bytes > 67108864
- M14 left L=200 rod: over budget: fine raw + gzip-1 172109936 bytes > 67108864
- M14 left L=210 rod: over budget: fine raw + gzip-1 180451710 bytes > 67108864
- M14 left L=220 rod: over budget: fine raw + gzip-1 188566140 bytes > 67108864
- M14 left L=230 rod: over budget: fine raw + gzip-1 197865466 bytes > 67108864
- M14 left L=240 rod: over budget: fine raw + gzip-1 206207085 bytes > 67108864
- M14 left L=250 rod: over budget: fine raw + gzip-1 214318904 bytes > 67108864
- M14 left L=260 rod: over budget: fine raw + gzip-1 223626666 bytes > 67108864
- M14 left L=270 rod: over budget: fine raw + gzip-1 231959122 bytes > 67108864
- M14 left L=280 rod: over budget: fine raw + gzip-1 240070907 bytes > 67108864
- M14 left L=290 rod: over budget: fine raw + gzip-1 249386323 bytes > 67108864
- M14 left L=300 rod: over budget: fine raw + gzip-1 257719287 bytes > 67108864
- M14 left L=310 rod: over budget: fine raw + gzip-1 265833585 bytes > 67108864
- M14 left L=320 rod: over budget: fine raw + gzip-1 275140618 bytes > 67108864
- M14 left L=330 rod: over budget: fine raw + gzip-1 283478153 bytes > 67108864
- M14 left L=340 rod: over budget: fine raw + gzip-1 291590175 bytes > 67108864
- M14 left L=350 rod: over budget: fine raw + gzip-1 300889774 bytes > 67108864
- M14 left L=360 rod: over budget: fine raw + gzip-1 309226100 bytes > 67108864
- M14 left L=370 rod: over budget: fine raw + gzip-1 317334444 bytes > 67108864
- M14 left L=380 rod: over budget: fine raw + gzip-1 326640158 bytes > 67108864
- M14 left L=390 rod: over budget: fine raw + gzip-1 334974958 bytes > 67108864
- M14 left L=400 rod: over budget: fine raw + gzip-1 343087014 bytes > 67108864
- M14 left L=410 rod: over budget: fine raw + gzip-1 352392369 bytes > 67108864
- M14 left L=420 rod: over budget: fine raw + gzip-1 360728230 bytes > 67108864
- M14 left L=430 rod: over budget: fine raw + gzip-1 368839425 bytes > 67108864
- M14 left L=440 rod: over budget: fine raw + gzip-1 378158044 bytes > 67108864
- M14 left L=450 rod: over budget: fine raw + gzip-1 386497819 bytes > 67108864
- M14 left L=460 rod: over budget: fine raw + gzip-1 394613366 bytes > 67108864
- M14 left L=470 rod: over budget: fine raw + gzip-1 403922258 bytes > 67108864
- M14 left L=480 rod: over budget: fine raw + gzip-1 412253804 bytes > 67108864
- M14 left L=490 rod: over budget: fine raw + gzip-1 420374773 bytes > 67108864
- M14 left L=500 rod: over budget: fine raw + gzip-1 429681974 bytes > 67108864
- M16 right L=170 rod: over budget: fine raw + gzip-1 214035630 bytes > 67108864
- M16 right L=180 rod: over budget: fine raw + gzip-1 226394093 bytes > 67108864
- M16 right L=190 rod: over budget: fine raw + gzip-1 238018003 bytes > 67108864
- M16 right L=200 rod: over budget: fine raw + gzip-1 251753923 bytes > 67108864
- M16 right L=210 rod: over budget: fine raw + gzip-1 264100899 bytes > 67108864
- M16 right L=220 rod: over budget: fine raw + gzip-1 275727227 bytes > 67108864
- M16 right L=230 rod: over budget: fine raw + gzip-1 289459212 bytes > 67108864
- M16 right L=240 rod: over budget: fine raw + gzip-1 301812685 bytes > 67108864
- M16 right L=250 rod: over budget: fine raw + gzip-1 313435964 bytes > 67108864
- M16 right L=260 rod: over budget: fine raw + gzip-1 327171003 bytes > 67108864
- M16 right L=270 rod: over budget: fine raw + gzip-1 339522140 bytes > 67108864
- M16 right L=280 rod: over budget: fine raw + gzip-1 351141732 bytes > 67108864
- M16 right L=290 rod: over budget: fine raw + gzip-1 364866691 bytes > 67108864
- M16 right L=300 rod: over budget: fine raw + gzip-1 377219891 bytes > 67108864
- M16 right L=310 rod: over budget: fine raw + gzip-1 388835138 bytes > 67108864
- M16 right L=320 rod: over budget: fine raw + gzip-1 402565711 bytes > 67108864
- M16 right L=330 rod: over budget: fine raw + gzip-1 414920521 bytes > 67108864
- M16 right L=340 rod: over budget: fine raw + gzip-1 426538116 bytes > 67108864
- M16 right L=350 rod: over budget: fine raw + gzip-1 440266885 bytes > 67108864
- M16 right L=360 rod: over budget: fine raw + gzip-1 452616805 bytes > 67108864
- M16 right L=370 rod: over budget: fine raw + gzip-1 464231772 bytes > 67108864
- M16 right L=380 rod: over budget: fine raw + gzip-1 477960520 bytes > 67108864
- M16 right L=390 rod: over budget: fine raw + gzip-1 490319043 bytes > 67108864
- M16 right L=400 rod: over budget: fine raw + gzip-1 501937870 bytes > 67108864
- M16 right L=410 rod: over budget: fine raw + gzip-1 515658730 bytes > 67108864
- M16 right L=420 rod: over budget: fine raw + gzip-1 528013851 bytes > 67108864
- M16 right L=430 rod: over budget: fine raw + gzip-1 539631696 bytes > 67108864
- M16 right L=440 rod: over budget: fine raw + gzip-1 553352792 bytes > 67108864
- M16 right L=450 rod: over budget: fine raw + gzip-1 565715618 bytes > 67108864
- M16 right L=460 rod: over budget: fine raw + gzip-1 577333011 bytes > 67108864
- M16 right L=470 rod: over budget: fine raw + gzip-1 591060250 bytes > 67108864
- M16 right L=480 rod: over budget: fine raw + gzip-1 603414928 bytes > 67108864
- M16 right L=490 rod: over budget: fine raw + gzip-1 615033501 bytes > 67108864
- M16 right L=500 rod: over budget: fine raw + gzip-1 628759460 bytes > 67108864
- M16 left L=170 rod: over budget: fine raw + gzip-1 152458379 bytes > 67108864
- M16 left L=180 rod: over budget: fine raw + gzip-1 161101925 bytes > 67108864
- M16 left L=190 rod: over budget: fine raw + gzip-1 169472568 bytes > 67108864
- M16 left L=200 rod: over budget: fine raw + gzip-1 179323107 bytes > 67108864
- M16 left L=210 rod: over budget: fine raw + gzip-1 187957834 bytes > 67108864
- M16 left L=220 rod: over budget: fine raw + gzip-1 196328999 bytes > 67108864
- M16 left L=230 rod: over budget: fine raw + gzip-1 206172526 bytes > 67108864
- M16 left L=240 rod: over budget: fine raw + gzip-1 214814244 bytes > 67108864
- M16 left L=250 rod: over budget: fine raw + gzip-1 223189721 bytes > 67108864
- M16 left L=260 rod: over budget: fine raw + gzip-1 233022390 bytes > 67108864
- M16 left L=270 rod: over budget: fine raw + gzip-1 241628656 bytes > 67108864
- M16 left L=280 rod: over budget: fine raw + gzip-1 249975083 bytes > 67108864
- M16 left L=290 rod: over budget: fine raw + gzip-1 259798763 bytes > 67108864
- M16 left L=300 rod: over budget: fine raw + gzip-1 268396781 bytes > 67108864
- M16 left L=310 rod: over budget: fine raw + gzip-1 276741756 bytes > 67108864
- M16 left L=320 rod: over budget: fine raw + gzip-1 286557250 bytes > 67108864
- M16 left L=330 rod: over budget: fine raw + gzip-1 295159814 bytes > 67108864
- M16 left L=340 rod: over budget: fine raw + gzip-1 303506052 bytes > 67108864
- M16 left L=350 rod: over budget: fine raw + gzip-1 313324312 bytes > 67108864
- M16 left L=360 rod: over budget: fine raw + gzip-1 321934538 bytes > 67108864
- M16 left L=370 rod: over budget: fine raw + gzip-1 330280340 bytes > 67108864
- M16 left L=380 rod: over budget: fine raw + gzip-1 340101277 bytes > 67108864
- M16 left L=390 rod: over budget: fine raw + gzip-1 348698915 bytes > 67108864
- M16 left L=400 rod: over budget: fine raw + gzip-1 357045377 bytes > 67108864
- M16 left L=410 rod: over budget: fine raw + gzip-1 366860795 bytes > 67108864
- M16 left L=420 rod: over budget: fine raw + gzip-1 375465385 bytes > 67108864
- M16 left L=430 rod: over budget: fine raw + gzip-1 383806333 bytes > 67108864
- M16 left L=440 rod: over budget: fine raw + gzip-1 393632038 bytes > 67108864
- M16 left L=450 rod: over budget: fine raw + gzip-1 402236957 bytes > 67108864
- M16 left L=460 rod: over budget: fine raw + gzip-1 410588379 bytes > 67108864
- M16 left L=470 rod: over budget: fine raw + gzip-1 420403520 bytes > 67108864
- M16 left L=480 rod: over budget: fine raw + gzip-1 429007461 bytes > 67108864
- M16 left L=490 rod: over budget: fine raw + gzip-1 437354054 bytes > 67108864
- M16 left L=500 rod: over budget: fine raw + gzip-1 447170292 bytes > 67108864
- M18 right L=187.5 rod: over budget: fine raw + gzip-1 188197116 bytes > 67108864
- M18 right L=200 rod: over budget: fine raw + gzip-1 201001562 bytes > 67108864
- M18 right L=212.5 rod: over budget: fine raw + gzip-1 213523119 bytes > 67108864
- M18 right L=225 rod: over budget: fine raw + gzip-1 225846515 bytes > 67108864
- M18 right L=237.5 rod: over budget: fine raw + gzip-1 238651415 bytes > 67108864
- M18 right L=250 rod: over budget: fine raw + gzip-1 251171795 bytes > 67108864
- M18 right L=262.5 rod: over budget: fine raw + gzip-1 263473205 bytes > 67108864
- M18 right L=275 rod: over budget: fine raw + gzip-1 276259233 bytes > 67108864
- M18 right L=287.5 rod: over budget: fine raw + gzip-1 288745496 bytes > 67108864
- M18 right L=300 rod: over budget: fine raw + gzip-1 301024511 bytes > 67108864
- M18 right L=312.5 rod: over budget: fine raw + gzip-1 313811434 bytes > 67108864
- M18 right L=325 rod: over budget: fine raw + gzip-1 326292340 bytes > 67108864
- M18 right L=337.5 rod: over budget: fine raw + gzip-1 338591048 bytes > 67108864
- M18 right L=350 rod: over budget: fine raw + gzip-1 351377897 bytes > 67108864
- M18 right L=362.5 rod: over budget: fine raw + gzip-1 363854504 bytes > 67108864
- M18 right L=375 rod: over budget: fine raw + gzip-1 376138835 bytes > 67108864
- M18 right L=387.5 rod: over budget: fine raw + gzip-1 388918407 bytes > 67108864
- M18 right L=400 rod: over budget: fine raw + gzip-1 401401468 bytes > 67108864
- M18 right L=412.5 rod: over budget: fine raw + gzip-1 413680807 bytes > 67108864
- M18 right L=425 rod: over budget: fine raw + gzip-1 426465864 bytes > 67108864
- M18 right L=437.5 rod: over budget: fine raw + gzip-1 438948648 bytes > 67108864
- M18 right L=450 rod: over budget: fine raw + gzip-1 451234346 bytes > 67108864
- M18 right L=462.5 rod: over budget: fine raw + gzip-1 464014972 bytes > 67108864
- M18 right L=475 rod: over budget: fine raw + gzip-1 476493985 bytes > 67108864
- M18 right L=487.5 rod: over budget: fine raw + gzip-1 488786703 bytes > 67108864
- M18 right L=500 rod: over budget: fine raw + gzip-1 501581889 bytes > 67108864
- M18 right L=512.5 rod: over budget: fine raw + gzip-1 514062435 bytes > 67108864
- M18 right L=525 rod: over budget: fine raw + gzip-1 526370635 bytes > 67108864
- M18 right L=537.5 rod: over budget: fine raw + gzip-1 539157539 bytes > 67108864
- M18 right L=550 rod: over budget: fine raw + gzip-1 551649830 bytes > 67108864
- M18 right L=562.5 rod: over budget: fine raw + gzip-1 563941755 bytes > 67108864
- M18 right L=575 rod: over budget: fine raw + gzip-1 576730908 bytes > 67108864
- M18 right L=587.5 rod: over budget: fine raw + gzip-1 589218707 bytes > 67108864
- M18 right L=600 rod: over budget: fine raw + gzip-1 601513381 bytes > 67108864
- M18 right L=612.5 rod: over budget: fine raw + gzip-1 614297140 bytes > 67108864
- M18 right L=625 rod: over budget: fine raw + gzip-1 626783954 bytes > 67108864
- M18 left L=187.5 rod: over budget: fine raw + gzip-1 136237508 bytes > 67108864
- M18 left L=200 rod: over budget: fine raw + gzip-1 145930522 bytes > 67108864
- M18 left L=212.5 rod: over budget: fine raw + gzip-1 154713134 bytes > 67108864
- M18 left L=225 rod: over budget: fine raw + gzip-1 163464790 bytes > 67108864
- M18 left L=237.5 rod: over budget: fine raw + gzip-1 173164079 bytes > 67108864
- M18 left L=250 rod: over budget: fine raw + gzip-1 181930966 bytes > 67108864
- M18 left L=262.5 rod: over budget: fine raw + gzip-1 190672271 bytes > 67108864
- M18 left L=275 rod: over budget: fine raw + gzip-1 200365241 bytes > 67108864
- M18 left L=287.5 rod: over budget: fine raw + gzip-1 209136934 bytes > 67108864
- M18 left L=300 rod: over budget: fine raw + gzip-1 217884473 bytes > 67108864
- M18 left L=312.5 rod: over budget: fine raw + gzip-1 227572550 bytes > 67108864
- M18 left L=325 rod: over budget: fine raw + gzip-1 236348210 bytes > 67108864
- M18 left L=337.5 rod: over budget: fine raw + gzip-1 245094998 bytes > 67108864
- M18 left L=350 rod: over budget: fine raw + gzip-1 254796410 bytes > 67108864
- M18 left L=362.5 rod: over budget: fine raw + gzip-1 263556383 bytes > 67108864
- M18 left L=375 rod: over budget: fine raw + gzip-1 272310450 bytes > 67108864
- M18 left L=387.5 rod: over budget: fine raw + gzip-1 281995878 bytes > 67108864
- M18 left L=400 rod: over budget: fine raw + gzip-1 290770365 bytes > 67108864
- M18 left L=412.5 rod: over budget: fine raw + gzip-1 299519107 bytes > 67108864
- M18 left L=425 rod: over budget: fine raw + gzip-1 309208475 bytes > 67108864
- M18 left L=437.5 rod: over budget: fine raw + gzip-1 317982544 bytes > 67108864
- M18 left L=450 rod: over budget: fine raw + gzip-1 326725423 bytes > 67108864
- M18 left L=462.5 rod: over budget: fine raw + gzip-1 336418223 bytes > 67108864
- M18 left L=475 rod: over budget: fine raw + gzip-1 345185577 bytes > 67108864
- M18 left L=487.5 rod: over budget: fine raw + gzip-1 353922391 bytes > 67108864
- M18 left L=500 rod: over budget: fine raw + gzip-1 363612093 bytes > 67108864
- M18 left L=512.5 rod: over budget: fine raw + gzip-1 372388499 bytes > 67108864
- M18 left L=525 rod: over budget: fine raw + gzip-1 381127814 bytes > 67108864
- M18 left L=537.5 rod: over budget: fine raw + gzip-1 390824491 bytes > 67108864
- M18 left L=550 rod: over budget: fine raw + gzip-1 399590922 bytes > 67108864
- M18 left L=562.5 rod: over budget: fine raw + gzip-1 408341471 bytes > 67108864
- M18 left L=575 rod: over budget: fine raw + gzip-1 418025206 bytes > 67108864
- M18 left L=587.5 rod: over budget: fine raw + gzip-1 426805490 bytes > 67108864
- M18 left L=600 rod: over budget: fine raw + gzip-1 435545758 bytes > 67108864
- M18 left L=612.5 rod: over budget: fine raw + gzip-1 445227797 bytes > 67108864
- M18 left L=625 rod: over budget: fine raw + gzip-1 453994812 bytes > 67108864
- M20 right L=212.5 rod: over budget: fine raw + gzip-1 222163707 bytes > 67108864
- M20 right L=225 rod: over budget: fine raw + gzip-1 235020567 bytes > 67108864
- M20 right L=237.5 rod: over budget: fine raw + gzip-1 250316989 bytes > 67108864
- M20 right L=250 rod: over budget: fine raw + gzip-1 261356889 bytes > 67108864
- M20 right L=262.5 rod: over budget: fine raw + gzip-1 274223471 bytes > 67108864
- M20 right L=275 rod: over budget: fine raw + gzip-1 289514219 bytes > 67108864
- M20 right L=287.5 rod: over budget: fine raw + gzip-1 300549865 bytes > 67108864
- M20 right L=300 rod: over budget: fine raw + gzip-1 313416267 bytes > 67108864
- M20 right L=312.5 rod: over budget: fine raw + gzip-1 328704158 bytes > 67108864
- M20 right L=325 rod: over budget: fine raw + gzip-1 339741705 bytes > 67108864
- M20 right L=337.5 rod: over budget: fine raw + gzip-1 352608873 bytes > 67108864
- M20 right L=350 rod: over budget: fine raw + gzip-1 367877373 bytes > 67108864
- M20 right L=362.5 rod: over budget: fine raw + gzip-1 378918225 bytes > 67108864
- M20 right L=375 rod: over budget: fine raw + gzip-1 391783402 bytes > 67108864
- M20 right L=387.5 rod: over budget: fine raw + gzip-1 407057244 bytes > 67108864
- M20 right L=400 rod: over budget: fine raw + gzip-1 418109328 bytes > 67108864
- M20 right L=412.5 rod: over budget: fine raw + gzip-1 430975476 bytes > 67108864
- M20 right L=425 rod: over budget: fine raw + gzip-1 446270501 bytes > 67108864
- M20 right L=437.5 rod: over budget: fine raw + gzip-1 457318885 bytes > 67108864
- M20 right L=450 rod: over budget: fine raw + gzip-1 470172410 bytes > 67108864
- M20 right L=462.5 rod: over budget: fine raw + gzip-1 485469727 bytes > 67108864
- M20 right L=475 rod: over budget: fine raw + gzip-1 496499807 bytes > 67108864
- M20 right L=487.5 rod: over budget: fine raw + gzip-1 509351336 bytes > 67108864
- M20 right L=500 rod: over budget: fine raw + gzip-1 524632056 bytes > 67108864
- M20 right L=512.5 rod: over budget: fine raw + gzip-1 535671558 bytes > 67108864
- M20 right L=525 rod: over budget: fine raw + gzip-1 548497165 bytes > 67108864
- M20 right L=537.5 rod: over budget: fine raw + gzip-1 563753799 bytes > 67108864
- M20 right L=550 rod: over budget: fine raw + gzip-1 574782686 bytes > 67108864
- M20 right L=562.5 rod: over budget: fine raw + gzip-1 587643459 bytes > 67108864
- M20 right L=575 rod: over budget: fine raw + gzip-1 602928273 bytes > 67108864
- M20 right L=587.5 rod: over budget: fine raw + gzip-1 613963457 bytes > 67108864
- M20 right L=600 rod: over budget: fine raw + gzip-1 626801479 bytes > 67108864
- M20 right L=612.5 rod: over budget: fine raw + gzip-1 642090220 bytes > 67108864
- M20 right L=625 rod: over budget: fine raw + gzip-1 653109977 bytes > 67108864
- M20 left L=212.5 rod: over budget: fine raw + gzip-1 155662731 bytes > 67108864
- M20 left L=225 rod: over budget: fine raw + gzip-1 164426926 bytes > 67108864
- M20 left L=237.5 rod: over budget: fine raw + gzip-1 175356208 bytes > 67108864
- M20 left L=250 rod: over budget: fine raw + gzip-1 183059685 bytes > 67108864
- M20 left L=262.5 rod: over budget: fine raw + gzip-1 191819607 bytes > 67108864
- M20 left L=275 rod: over budget: fine raw + gzip-1 202730644 bytes > 67108864
- M20 left L=287.5 rod: over budget: fine raw + gzip-1 210443744 bytes > 67108864
- M20 left L=300 rod: over budget: fine raw + gzip-1 219189626 bytes > 67108864
- M20 left L=312.5 rod: over budget: fine raw + gzip-1 230105366 bytes > 67108864
- M20 left L=325 rod: over budget: fine raw + gzip-1 237804911 bytes > 67108864
- M20 left L=337.5 rod: over budget: fine raw + gzip-1 246555854 bytes > 67108864
- M20 left L=350 rod: over budget: fine raw + gzip-1 257468507 bytes > 67108864
- M20 left L=362.5 rod: over budget: fine raw + gzip-1 265173945 bytes > 67108864
- M20 left L=375 rod: over budget: fine raw + gzip-1 273920890 bytes > 67108864
- M20 left L=387.5 rod: over budget: fine raw + gzip-1 284835798 bytes > 67108864
- M20 left L=400 rod: over budget: fine raw + gzip-1 292538794 bytes > 67108864
- M20 left L=412.5 rod: over budget: fine raw + gzip-1 301291036 bytes > 67108864
- M20 left L=425 rod: over budget: fine raw + gzip-1 312204916 bytes > 67108864
- M20 left L=437.5 rod: over budget: fine raw + gzip-1 319907497 bytes > 67108864
- M20 left L=450 rod: over budget: fine raw + gzip-1 328660218 bytes > 67108864
- M20 left L=462.5 rod: over budget: fine raw + gzip-1 339572766 bytes > 67108864
- M20 left L=475 rod: over budget: fine raw + gzip-1 347287474 bytes > 67108864
- M20 left L=487.5 rod: over budget: fine raw + gzip-1 356034251 bytes > 67108864
- M20 left L=500 rod: over budget: fine raw + gzip-1 366947836 bytes > 67108864
- M20 left L=512.5 rod: over budget: fine raw + gzip-1 374656826 bytes > 67108864
- M20 left L=525 rod: over budget: fine raw + gzip-1 383423577 bytes > 67108864
- M20 left L=537.5 rod: over budget: fine raw + gzip-1 394323289 bytes > 67108864
- M20 left L=550 rod: over budget: fine raw + gzip-1 402031151 bytes > 67108864
- M20 left L=562.5 rod: over budget: fine raw + gzip-1 410769709 bytes > 67108864
- M20 left L=575 rod: over budget: fine raw + gzip-1 421669730 bytes > 67108864
- M20 left L=587.5 rod: over budget: fine raw + gzip-1 429367553 bytes > 67108864
- M20 left L=600 rod: over budget: fine raw + gzip-1 438103502 bytes > 67108864
- M20 left L=612.5 rod: over budget: fine raw + gzip-1 449006501 bytes > 67108864
- M20 left L=625 rod: over budget: fine raw + gzip-1 456706469 bytes > 67108864
- frontier M2 right: no stop up to 250 turns; last measured 250 turns
- frontier M2 left: no stop up to 250 turns; last measured 250 turns
- frontier M2.5 right: no stop up to 250 turns; last measured 250 turns
- frontier M2.5 left: no stop up to 250 turns; last measured 250 turns
- frontier M3 right: no stop up to 250 turns; last measured 250 turns
- frontier M3 left: no stop up to 250 turns; last measured 250 turns
- frontier M3.5 right: no stop up to 250 turns; last measured 250 turns
- frontier M3.5 left: no stop up to 250 turns; last measured 250 turns
- frontier M4 right: no stop up to 250 turns; last measured 250 turns
- frontier M4 left: no stop up to 250 turns; last measured 250 turns
- frontier M5 right: no stop up to 250 turns; last measured 250 turns
- frontier M5 left: no stop up to 250 turns; last measured 250 turns
- frontier M6 right: no stop up to 250 turns; last measured 250 turns
- frontier M6 left: no stop up to 250 turns; last measured 250 turns
- frontier M7 right: no stop up to 250 turns; last measured 250 turns
- frontier M7 left: no stop up to 250 turns; last measured 250 turns
- frontier M8 right: no stop up to 250 turns; last measured 250 turns
- frontier M8 left: no stop up to 250 turns; last measured 250 turns
- frontier M10 right: no stop up to 250 turns; last measured 250 turns
- frontier M10 left: no stop up to 250 turns; last measured 250 turns
- frontier M12 right: no stop up to 250 turns; last measured 250 turns
- frontier M12 left: no stop up to 250 turns; last measured 250 turns
- frontier M14 right: no stop up to 250 turns; last measured 250 turns
- frontier M14 left: no stop up to 250 turns; last measured 250 turns
- frontier M16 right: no stop up to 250 turns; last measured 250 turns
- frontier M16 left: no stop up to 250 turns; last measured 250 turns
- frontier M18 right: no stop up to 250 turns; last measured 250 turns
- frontier M18 left: no stop up to 250 turns; last measured 250 turns
- frontier M20 right: no stop up to 250 turns; last measured 250 turns
- frontier M20 left: no stop up to 250 turns; last measured 250 turns
- load1 16.96 read 2026-10-08T19:18:18+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The output covers 136 to 160 rows per size for M2 to M20, every row class ok, with the "Checks skipped" column non-zero for every size. The quiet gate did not release (non-decisive after 900 s, 31 readings), so the seconds columns are recorded but are not established timings. The over-budget rows are listed in the output. What construction cap or stop this block yields is in the campaign entry below.


### 2026-10-08-a-ladder

Run window (UTC): 2026-10-08T19:18:20+00:00 (first gate reading) to 2026-10-08T19:32:22+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: decisive at 2026-10-08T19:31:21+00:00. Gate readings: 27; first load1 16.96 read 2026-10-08T19:18:20+00:00; last load1 1.33 read 2026-10-08T19:31:21+00:00. Every reading is in the output below.
End reading: load1 5.81 read 2026-10-08T19:32:22+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-ladder.jsonl` — 17 lines, sha256 5ab37e15d8ab45f72f31f3dc907cc2bfa2dddc33b35d06e104352202d582e5c2. Markdown output: `bench/results/thread-spike/2026-10-08-a-ladder.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-ladder

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: ladder
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 16.96 read 2026-10-08T19:18:20+00:00
- load1 11.32 read 2026-10-08T19:18:50+00:00
- load1 7.96 read 2026-10-08T19:19:20+00:00
- load1 5.74 read 2026-10-08T19:19:50+00:00
- load1 4.07 read 2026-10-08T19:20:20+00:00
- load1 3.46 read 2026-10-08T19:20:50+00:00
- load1 3.50 read 2026-10-08T19:21:20+00:00
- load1 2.57 read 2026-10-08T19:21:50+00:00
- load1 2.18 read 2026-10-08T19:22:21+00:00
- load1 1.93 read 2026-10-08T19:22:51+00:00
- load1 1.90 read 2026-10-08T19:23:21+00:00
- load1 2.04 read 2026-10-08T19:23:51+00:00
- load1 1.84 read 2026-10-08T19:24:21+00:00
- load1 1.76 read 2026-10-08T19:24:51+00:00
- load1 2.00 read 2026-10-08T19:25:21+00:00
- load1 2.00 read 2026-10-08T19:25:51+00:00
- load1 1.89 read 2026-10-08T19:26:21+00:00
- load1 1.59 read 2026-10-08T19:26:51+00:00
- load1 1.72 read 2026-10-08T19:27:21+00:00
- load1 2.48 read 2026-10-08T19:27:51+00:00
- load1 2.25 read 2026-10-08T19:28:21+00:00
- load1 2.19 read 2026-10-08T19:28:51+00:00
- load1 1.92 read 2026-10-08T19:29:21+00:00
- load1 1.55 read 2026-10-08T19:29:51+00:00
- load1 1.40 read 2026-10-08T19:30:21+00:00
- load1 1.19 read 2026-10-08T19:30:51+00:00
- load1 1.33 read 2026-10-08T19:31:21+00:00
- release: decisive at 2026-10-08T19:31:21+00:00

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 2 | 2 | 0 | 0 | 0 | 0 | -5.057e-06 | -1.251e-05 | 305432 | 15271684 | 22296145 | n/a | n/a | 0 |
| M2.5 | 2 | 2 | 0 | 0 | 0 | 0 | -5.119e-06 | -1.159e-05 | 411140 | 20557084 | 30196865 | n/a | n/a | 0 |
| M3 | 2 | 2 | 0 | 0 | 0 | 0 | -5.712e-06 | -1.307e-05 | 450704 | 22535284 | 33169558 | n/a | n/a | 0 |
| M6 | 2 | 2 | 0 | 0 | 0 | 0 | -4.922e-07 | -1.558e-06 | 604344 | 30217284 | 44188214 | n/a | n/a | 0 |
| M8 | 2 | 2 | 0 | 0 | 0 | 0 | -4.684e-07 | -1.521e-06 | 1075998 | 53799984 | 79618132 | n/a | n/a | 1 |
| M10 | 2 | 2 | 0 | 0 | 0 | 0 | -4.548e-07 | -1.552e-06 | 1617392 | 80869684 | 118560997 | n/a | n/a | 1 |
| M16 | 2 | 2 | 0 | 0 | 0 | 0 | +4.614e-07 | -5.715e-07 | 2751566 | 137578384 | 200304425 | n/a | n/a | 1 |
| M20 | 2 | 2 | 0 | 0 | 0 | 0 | +4.614e-07 | -5.715e-07 | 2898882 | 144944184 | 211134421 | n/a | n/a | 1 |

- M8 right L=80 rod: over budget: fine raw + gzip-1 79618132 bytes > 67108864
- M10 right L=100 rod: over budget: fine raw + gzip-1 118560997 bytes > 67108864
- M16 right L=160 rod: over budget: fine raw + gzip-1 200304425 bytes > 67108864
- M20 right L=200 rod: over budget: fine raw + gzip-1 211134421 bytes > 67108864
- load1 5.81 read 2026-10-08T19:32:22+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The output covers 2 rows per size for the eight sizes M2, M2.5, M3, M6, M8, M10, M16 and M20, every row class ok, with the quiet gate released as decisive. The "Max build + slower export s" and "Max STEP bytes" columns read n/a for this block. It lists four rods over the byte budget (M8, M10, M16, M20). The block has 16 rows, so it says nothing about sizes it did not run.


### 2026-10-08-a-trim

Run window (UTC): 2026-10-08T19:32:25+00:00 (first gate reading) to 2026-10-08T19:38:51+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: decisive at 2026-10-08T19:36:55+00:00. Gate readings: 10; first load1 5.43 read 2026-10-08T19:32:25+00:00; last load1 1.33 read 2026-10-08T19:36:55+00:00. Every reading is in the output below.
End reading: load1 1.35 read 2026-10-08T19:38:51+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-trim.jsonl` — 31 lines, sha256 967b3a6bc72ca423af08e24fde94da83a6d510f16cc058bb6afaca81ee17c185. Markdown output: `bench/results/thread-spike/2026-10-08-a-trim.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-trim

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: trim
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 5.43 read 2026-10-08T19:32:25+00:00
- load1 4.33 read 2026-10-08T19:32:55+00:00
- load1 3.00 read 2026-10-08T19:33:25+00:00
- load1 3.49 read 2026-10-08T19:33:55+00:00
- load1 2.59 read 2026-10-08T19:34:25+00:00
- load1 2.24 read 2026-10-08T19:34:55+00:00
- load1 1.87 read 2026-10-08T19:35:25+00:00
- load1 1.46 read 2026-10-08T19:35:55+00:00
- load1 1.44 read 2026-10-08T19:36:25+00:00
- load1 1.33 read 2026-10-08T19:36:55+00:00
- release: decisive at 2026-10-08T19:36:55+00:00

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 310660 | 15533084 | 22665097 | 0.55 | 2672684 | 0 |
| M2.5 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 412682 | 20634184 | 30295252 | 0.59 | 3005466 | 0 |
| M3 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 452446 | 22622384 | 33290194 | 0.71 | 3262870 | 0 |
| M3.5 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 450624 | 22531284 | 33134980 | 0.71 | 3199718 | 0 |
| M4 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 532590 | 26629584 | 38968379 | 0.72 | 3494580 | 0 |
| M5 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 601758 | 30087984 | 44016969 | 0.90 | 3786540 | 0 |
| M6 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 608308 | 30415484 | 44476514 | 0.89 | 3651443 | 0 |
| M7 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 736190 | 36809584 | 54001296 | 0.97 | 4260863 | 0 |
| M8 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 1072962 | 53648184 | 79394453 | 1.13 | 3935714 | 1 |
| M10 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 1613994 | 80699784 | 118296272 | 1.56 | 3736332 | 2 |
| M12 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 1805228 | 90261484 | 132268646 | 1.89 | 4234645 | 2 |
| M14 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 2194088 | 109704484 | 160186486 | 2.25 | 4374068 | 2 |
| M16 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 2768418 | 138420984 | 201597321 | 2.71 | 4983558 | 2 |
| M18 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 2476444 | 123822284 | 180605381 | 2.40 | 4535139 | 2 |
| M20 | 2 | 2 | 0 | 0 | 0 | 0 | n/a | n/a | 2894830 | 144741584 | 210873385 | 2.67 | 5050734 | 2 |

- M8 right L=80 trim: over budget: fine raw + gzip-1 79394453 bytes > 67108864
- M10 right L=100 trim: over budget: fine raw + gzip-1 118296272 bytes > 67108864
- M10 left L=100 trim: over budget: fine raw + gzip-1 91954010 bytes > 67108864
- M12 right L=120 trim: over budget: fine raw + gzip-1 132268646 bytes > 67108864
- M12 left L=120 trim: over budget: fine raw + gzip-1 105113872 bytes > 67108864
- M14 right L=140 trim: over budget: fine raw + gzip-1 160186486 bytes > 67108864
- M14 left L=140 trim: over budget: fine raw + gzip-1 120265160 bytes > 67108864
- M16 right L=160 trim: over budget: fine raw + gzip-1 201597321 bytes > 67108864
- M16 left L=160 trim: over budget: fine raw + gzip-1 143619575 bytes > 67108864
- M18 right L=180 trim: over budget: fine raw + gzip-1 180605381 bytes > 67108864
- M18 left L=180 trim: over budget: fine raw + gzip-1 131016046 bytes > 67108864
- M20 right L=200 trim: over budget: fine raw + gzip-1 210873385 bytes > 67108864
- M20 left L=200 trim: over budget: fine raw + gzip-1 148569983 bytes > 67108864

### Tip trim cost (D-08)

| Size | Hand | Length mm | Class | Trim s | Request s (build + trim + slower export) | Fine triangles | STEP bytes |
|---|---|---|---|---|---|---|---|
| M2 | right | 20 | ok | 0.21 | 0.55 | 310660 | 2672684 |
| M2 | left | 20 | ok | 0.19 | 0.51 | 278332 | 2672228 |
| M2.5 | right | 25 | ok | 0.20 | 0.59 | 412682 | 2971967 |
| M2.5 | left | 25 | ok | 0.22 | 0.57 | 330746 | 3005466 |
| M3 | right | 30 | ok | 0.23 | 0.71 | 452446 | 3260380 |
| M3 | left | 30 | ok | 0.24 | 0.66 | 365390 | 3262870 |
| M3.5 | right | 35 | ok | 0.22 | 0.71 | 450624 | 3180075 |
| M3.5 | left | 35 | ok | 0.24 | 0.69 | 367860 | 3199718 |
| M4 | right | 40 | ok | 0.20 | 0.72 | 532590 | 3493913 |
| M4 | left | 40 | ok | 0.21 | 0.67 | 389820 | 3494580 |
| M5 | right | 50 | ok | 0.26 | 0.90 | 601758 | 3784631 |
| M5 | left | 50 | ok | 0.27 | 0.82 | 441464 | 3786540 |
| M6 | right | 60 | ok | 0.27 | 0.89 | 608308 | 3651443 |
| M6 | left | 60 | ok | 0.27 | 0.81 | 453904 | 3651209 |
| M7 | right | 70 | ok | 0.28 | 0.97 | 736190 | 4257790 |
| M7 | left | 70 | ok | 0.29 | 0.89 | 558460 | 4260863 |
| M8 | right | 80 | ok | 0.26 | 1.13 | 1072962 | 3933673 |
| M8 | left | 80 | ok | 0.27 | 1.05 | 873052 | 3935714 |
| M10 | right | 100 | ok | 0.28 | 1.56 | 1613994 | 3736332 |
| M10 | left | 100 | ok | 0.29 | 1.41 | 1247152 | 3715911 |
| M12 | right | 120 | ok | 0.31 | 1.89 | 1805228 | 4212788 |
| M12 | left | 120 | ok | 0.31 | 1.68 | 1427396 | 4234645 |
| M14 | right | 140 | ok | 0.30 | 2.25 | 2194088 | 4368959 |
| M14 | left | 140 | ok | 0.30 | 2.00 | 1634744 | 4374068 |
| M16 | right | 160 | ok | 0.36 | 2.71 | 2768418 | 4983558 |
| M16 | left | 160 | ok | 0.36 | 2.39 | 1951234 | 4970441 |
| M18 | right | 180 | ok | 0.36 | 2.40 | 2476444 | 4527783 |
| M18 | left | 180 | ok | 0.37 | 2.04 | 1778886 | 4535139 |
| M20 | right | 200 | ok | 0.36 | 2.67 | 2894830 | 5050734 |
| M20 | left | 200 | ok | 0.36 | 2.32 | 2014508 | 5043593 |

The cone angle is 30 degrees from the end face at the minor radius, UNVERIFIED (ISO 4753 is unread): these rows are cost evidence for Phase 4, not geometry truth, and never enter the pass bar.

- load1 1.35 read 2026-10-08T19:38:51+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The output covers 2 rows per size for the fifteen sizes M2 to M20, every row class ok, with the quiet gate released as decisive; the "Tip trim cost (D-08)" table lists trim and request seconds per row. The output itself states that the 30 degree cone angle is UNVERIFIED (ISO 4753 is unread) and that these rows are cost evidence for Phase 4, not geometry truth, and never enter the pass bar. It lists 13 rows over the byte budget, M8 and M10 to M20.


### 2026-10-08-a-controls

Run window (UTC): 2026-10-08T19:38:55+00:00 (first gate reading) to 2026-10-08T19:41:48+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: decisive at 2026-10-08T19:39:55+00:00. Gate readings: 3; first load1 1.35 read 2026-10-08T19:38:55+00:00; last load1 1.09 read 2026-10-08T19:39:55+00:00. Every reading is in the output below.
End reading: load1 1.45 read 2026-10-08T19:41:48+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-controls.jsonl` — 86 lines, sha256 723564de2ccce0783288d29bf7315585c3e40b5aa5263acad8baaa458cfd68de. Markdown output: `bench/results/thread-spike/2026-10-08-a-controls.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-controls

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: controls
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 1.35 read 2026-10-08T19:38:55+00:00
- load1 1.24 read 2026-10-08T19:39:25+00:00
- load1 1.09 read 2026-10-08T19:39:55+00:00
- release: decisive at 2026-10-08T19:39:55+00:00

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 10 | 4 | 6 | 0 | 0 | 0 | -2.000e+00 | -2.002e+00 | n/a | n/a | n/a | n/a | n/a | 0 |
| M2.5 | 11 | 4 | 6 | 1 | 0 | 0 | -2.000e+00 | -2.002e+00 | n/a | n/a | n/a | n/a | n/a | 0 |
| M3 | 11 | 4 | 4 | 3 | 0 | 0 | -2.000e+00 | -2.002e+00 | n/a | n/a | n/a | n/a | n/a | 0 |
| M6 | 10 | 4 | 4 | 2 | 0 | 0 | -2.000e+00 | -2.001e+00 | n/a | n/a | n/a | n/a | n/a | 0 |
| M8 | 11 | 4 | 5 | 2 | 0 | 0 | -2.000e+00 | -2.000e+00 | n/a | n/a | n/a | n/a | n/a | 0 |
| M10 | 11 | 4 | 6 | 1 | 0 | 0 | -2.000e+00 | -2.000e+00 | n/a | n/a | n/a | n/a | n/a | 0 |
| M16 | 10 | 4 | 4 | 2 | 0 | 0 | -2.000e+00 | -2.000e+00 | n/a | n/a | n/a | n/a | n/a | 0 |
| M20 | 11 | 4 | 6 | 1 | 0 | 0 | -2.000e+00 | -2.000e+00 | n/a | n/a | n/a | n/a | n/a | 0 |

- M2 right L=4 naive: silent_wrong: precise rel err -7.098e-01 outside +/-1e-4
- M2 right L=10 naive: silent_wrong: precise rel err -7.388e-01 outside +/-1e-4
- M2 right L=20 naive: silent_wrong: precise rel err -7.485e-01 outside +/-1e-4
- M2 right L=64 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M2 right L=4 ruled: silent_wrong: precise rel err -1.870e-02 outside +/-1e-4
- M2 right L=20 ruled: silent_wrong: precise rel err -4.287e-03 outside +/-1e-4
- M2.5 right L=4.5 naive: silent_wrong: precise rel err -7.410e-01 outside +/-1e-4
- M2.5 right L=10 naive: silent_wrong: precise rel err -7.631e-01 outside +/-1e-4
- M2.5 right L=20 naive: failure: ValueError: Null TopoDS_Shape object
- M2.5 right L=25 naive: silent_wrong: solids=2; precise rel err +3.573e-02 outside +/-1e-4
- M2.5 right L=72 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M2.5 right L=4.5 ruled: silent_wrong: precise rel err -1.659e-02 outside +/-1e-4
- M2.5 right L=25 ruled: silent_wrong: precise rel err -3.431e-03 outside +/-1e-4
- M3 right L=5 naive: failure: ValueError: Null TopoDS_Shape object
- M3 right L=10 naive: silent_wrong: precise rel err -7.815e-01 outside +/-1e-4
- M3 right L=20 naive: failure: ValueError: Null TopoDS_Shape object
- M3 right L=30 naive: failure: ValueError: Null TopoDS_Shape object
- M3 right L=80 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M3 right L=5 ruled: silent_wrong: precise rel err -1.520e-02 outside +/-1e-4
- M3 right L=30 ruled: silent_wrong: precise rel err -2.908e-03 outside +/-1e-4
- M6 right L=10 naive: silent_wrong: precise rel err -7.616e-01 outside +/-1e-4
- M6 right L=20 naive: failure: ValueError: Null TopoDS_Shape object
- M6 right L=60 naive: failure: ValueError: Null TopoDS_Shape object
- M6 right L=160 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M6 right L=10 ruled: silent_wrong: precise rel err -1.499e-02 outside +/-1e-4
- M6 right L=60 ruled: silent_wrong: precise rel err -2.688e-03 outside +/-1e-4
- M8 right L=10 naive: silent_wrong: precise rel err -7.683e-01 outside +/-1e-4
- M8 right L=12.5 naive: failure: ValueError: Null TopoDS_Shape object
- M8 right L=20 naive: failure: ValueError: Null TopoDS_Shape object
- M8 right L=80 naive: silent_wrong: precise rel err -8.088e-01 outside +/-1e-4
- M8 right L=200 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M8 right L=12.5 ruled: silent_wrong: precise rel err -1.393e-02 outside +/-1e-4
- M8 right L=80 ruled: silent_wrong: precise rel err -2.321e-03 outside +/-1e-4
- M10 right L=10 naive: silent_wrong: precise rel err -7.693e-01 outside +/-1e-4
- M10 right L=15 naive: failure: ValueError: Null TopoDS_Shape object
- M10 right L=20 naive: silent_wrong: precise rel err +2.662e-02 outside +/-1e-4
- M10 right L=100 naive: silent_wrong: precise rel err -8.172e-01 outside +/-1e-4
- M10 right L=240 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M10 right L=15 ruled: silent_wrong: precise rel err -1.330e-02 outside +/-1e-4
- M10 right L=100 ruled: silent_wrong: precise rel err -2.111e-03 outside +/-1e-4
- M16 right L=10 naive: silent_wrong: precise rel err -7.953e-01 outside +/-1e-4
- M16 right L=20 naive: failure: ValueError: Null TopoDS_Shape object
- M16 right L=160 naive: failure: Standard_Failure: BRepOffsetAPI_MakePipeShell::MakeSolid
- M16 right L=320 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M16 right L=20 ruled: silent_wrong: precise rel err -1.091e-02 outside +/-1e-4
- M16 right L=160 ruled: silent_wrong: precise rel err -1.436e-03 outside +/-1e-4
- M20 right L=10 naive: silent_wrong: precise rel err -7.807e-01 outside +/-1e-4
- M20 right L=20 naive: silent_wrong: precise rel err -8.172e-01 outside +/-1e-4
- M20 right L=25 naive: failure: ValueError: Null TopoDS_Shape object
- M20 right L=200 naive: silent_wrong: precise rel err -8.501e-01 outside +/-1e-4
- M20 right L=400 one_pipe: silent_wrong: precise rel err -2.000e+00 outside +/-1e-4
- M20 right L=25 ruled: silent_wrong: precise rel err -1.089e-02 outside +/-1e-4
- M20 right L=200 ruled: silent_wrong: precise rel err -1.420e-03 outside +/-1e-4

### Controls (D-06)

| Construction | Size | Length mm | Turns | Class | Solids | Valid | Precise ratio | Default ratio |
|---|---|---|---|---|---|---|---|---|
| naive sweep + fuse (negative control) | M2 | 4 | 10 | silent_wrong | 1 | yes | 0.290229 | 0.290298 |
| naive sweep + fuse (negative control) | M2 | 10 | 25 | silent_wrong | 1 | yes | 0.261206 | 0.261210 |
| naive sweep + fuse (negative control) | M2 | 20 | 50 | silent_wrong | 1 | yes | 0.251542 | 0.222915 |
| naive sweep + fuse (negative control) | M2.5 | 4.5 | 10 | silent_wrong | 1 | yes | 0.258961 | 0.259095 |
| naive sweep + fuse (negative control) | M2.5 | 10 | 22.2222 | silent_wrong | 1 | yes | 0.236871 | 0.236870 |
| naive sweep + fuse (negative control) | M2.5 | 20 | 44.4444 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M2.5 | 25 | 55.5556 | silent_wrong | 2 | yes | 1.035730 | 1.056853 |
| naive sweep + fuse (negative control) | M3 | 5 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M3 | 10 | 20 | silent_wrong | 1 | yes | 0.218512 | 0.218716 |
| naive sweep + fuse (negative control) | M3 | 20 | 40 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M3 | 30 | 60 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M6 | 10 | 10 | silent_wrong | 1 | yes | 0.238384 | 0.238232 |
| naive sweep + fuse (negative control) | M6 | 20 | 20 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M6 | 60 | 60 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 10 | 8 | silent_wrong | 1 | yes | 0.231722 | 0.231694 |
| naive sweep + fuse (negative control) | M8 | 12.5 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 20 | 16 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 80 | 64 | silent_wrong | 1 | yes | 0.191174 | 0.186273 |
| naive sweep + fuse (negative control) | M10 | 10 | 6.66667 | silent_wrong | 1 | yes | 0.230710 | 0.230710 |
| naive sweep + fuse (negative control) | M10 | 15 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M10 | 20 | 13.3333 | silent_wrong | 1 | yes | 1.026621 | 1.026622 |
| naive sweep + fuse (negative control) | M10 | 100 | 66.6667 | silent_wrong | 1 | yes | 0.182793 | 0.200653 |
| naive sweep + fuse (negative control) | M16 | 10 | 5 | silent_wrong | 1 | yes | 0.204723 | 0.204724 |
| naive sweep + fuse (negative control) | M16 | 20 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M16 | 160 | 80 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M20 | 10 | 4 | silent_wrong | 1 | yes | 0.219346 | 0.219347 |
| naive sweep + fuse (negative control) | M20 | 20 | 8 | silent_wrong | 1 | yes | 0.182789 | 0.182788 |
| naive sweep + fuse (negative control) | M20 | 25 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M20 | 200 | 80 | silent_wrong | 1 | yes | 0.149887 | 0.060069 |
| one-pipe twist | M2 | 20 | 50 | ok | 1 | yes | 0.999990 | 0.999021 |
| one-pipe twist | M2 | 40 | 100 | ok | 1 | yes | 0.999990 | 1.001131 |
| one-pipe twist | M2 | 64 | 160 | silent_wrong | 1 | yes | -1.000015 | -1.002367 |
| one-pipe twist | M2 | 80 | 200 | ok | 1 | yes | 0.999958 | 0.999035 |
| one-pipe twist | M2 | 100 | 250 | ok | 1 | yes | 0.999980 | 1.000803 |
| one-pipe twist | M2.5 | 25 | 55.5556 | ok | 1 | yes | 0.999996 | 1.000296 |
| one-pipe twist | M2.5 | 45 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M2.5 | 72 | 160 | silent_wrong | 1 | yes | -1.000008 | -1.002367 |
| one-pipe twist | M2.5 | 90 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M2.5 | 112.5 | 250 | ok | 1 | yes | 0.999994 | 0.999924 |
| one-pipe twist | M3 | 30 | 60 | ok | 1 | yes | 0.999984 | 1.000324 |
| one-pipe twist | M3 | 50 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M3 | 80 | 160 | silent_wrong | 1 | yes | -1.000007 | -1.002367 |
| one-pipe twist | M3 | 100 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M3 | 125 | 250 | ok | 1 | yes | 0.999993 | 0.999924 |
| one-pipe twist | M6 | 60 | 60 | ok | 1 | yes | 0.999994 | 0.999942 |
| one-pipe twist | M6 | 100 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M6 | 160 | 160 | silent_wrong | 1 | yes | -0.999995 | -1.001450 |
| one-pipe twist | M6 | 200 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M6 | 250 | 250 | ok | 1 | yes | 0.999993 | 0.999924 |
| one-pipe twist | M8 | 80 | 64 | ok | 1 | yes | 1.000010 | 0.999934 |
| one-pipe twist | M8 | 125 | 100 | ok | 1 | yes | 0.999998 | 1.000071 |
| one-pipe twist | M8 | 200 | 160 | silent_wrong | 1 | yes | -1.000006 | -0.999825 |
| one-pipe twist | M8 | 250 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M8 | 312.5 | 250 | ok | 1 | yes | 1.000000 | 0.999949 |
| one-pipe twist | M10 | 100 | 66.6667 | ok | 1 | yes | 1.000001 | 1.000171 |
| one-pipe twist | M10 | 150 | 100 | ok | 1 | yes | 0.999997 | 1.000064 |
| one-pipe twist | M10 | 240 | 160 | silent_wrong | 1 | yes | -1.000003 | -0.999897 |
| one-pipe twist | M10 | 300 | 200 | ok | 1 | yes | 0.999991 | 1.000156 |
| one-pipe twist | M10 | 375 | 250 | ok | 1 | yes | 1.000008 | 0.999949 |
| one-pipe twist | M16 | 160 | 80 | ok | 1 | yes | 0.999994 | 1.000130 |
| one-pipe twist | M16 | 200 | 100 | ok | 1 | yes | 0.999995 | 1.000055 |
| one-pipe twist | M16 | 320 | 160 | silent_wrong | 1 | yes | -1.000008 | -0.999897 |
| one-pipe twist | M16 | 400 | 200 | ok | 1 | yes | 0.999995 | 1.000114 |
| one-pipe twist | M16 | 500 | 250 | ok | 1 | yes | 0.999975 | 1.000072 |
| one-pipe twist | M20 | 200 | 80 | ok | 1 | yes | 0.999998 | 1.000013 |
| one-pipe twist | M20 | 250 | 100 | ok | 1 | yes | 0.999992 | 1.000014 |
| one-pipe twist | M20 | 400 | 160 | silent_wrong | 1 | yes | -0.999995 | -1.000023 |
| one-pipe twist | M20 | 500 | 200 | ok | 1 | yes | 0.999986 | 0.999853 |
| one-pipe twist | M20 | 625 | 250 | ok | 1 | yes | 0.999998 | 0.999993 |
| ruled-surface reference | M2 | 4 | 10 | silent_wrong | 1 | yes | 0.981297 | 0.874977 |
| ruled-surface reference | M2 | 20 | 50 | silent_wrong | 1 | yes | 0.995713 | 0.793632 |
| ruled-surface reference | M2.5 | 4.5 | 10 | silent_wrong | 1 | yes | 0.983412 | 0.876551 |
| ruled-surface reference | M2.5 | 25 | 55.5556 | silent_wrong | 1 | yes | 0.996569 | 1.015351 |
| ruled-surface reference | M3 | 5 | 10 | silent_wrong | 1 | yes | 0.984799 | 0.877611 |
| ruled-surface reference | M3 | 30 | 60 | silent_wrong | 1 | yes | 0.997092 | 0.623208 |
| ruled-surface reference | M6 | 10 | 10 | silent_wrong | 1 | yes | 0.985012 | 0.878017 |
| ruled-surface reference | M6 | 60 | 60 | silent_wrong | 1 | yes | 0.997312 | 0.595680 |
| ruled-surface reference | M8 | 12.5 | 10 | silent_wrong | 1 | yes | 0.986069 | 0.878869 |
| ruled-surface reference | M8 | 80 | 64 | silent_wrong | 1 | yes | 0.997679 | 0.976243 |
| ruled-surface reference | M10 | 15 | 10 | silent_wrong | 1 | yes | 0.986698 | 0.879391 |
| ruled-surface reference | M10 | 100 | 66.6667 | silent_wrong | 1 | yes | 0.997889 | 0.908570 |
| ruled-surface reference | M16 | 20 | 10 | silent_wrong | 1 | yes | 0.989094 | 0.881278 |
| ruled-surface reference | M16 | 160 | 80 | silent_wrong | 1 | yes | 0.998564 | 0.952563 |
| ruled-surface reference | M20 | 25 | 10 | silent_wrong | 1 | yes | 0.989110 | 0.881327 |
| ruled-surface reference | M20 | 200 | 80 | silent_wrong | 1 | yes | 0.998580 | 0.952577 |

Known-bad inputs for THRD-04 (naive rows with 1 solid, isValid True and a precise ratio below 0.5):
- naive_sweep_fuse(d=2.0, pitch=0.4, length=4.0): precise ratio 0.290229
- naive_sweep_fuse(d=2.0, pitch=0.4, length=10.0): precise ratio 0.261206
- naive_sweep_fuse(d=2.0, pitch=0.4, length=20.0): precise ratio 0.251542
- naive_sweep_fuse(d=2.5, pitch=0.45, length=4.5): precise ratio 0.258961
- naive_sweep_fuse(d=2.5, pitch=0.45, length=10.0): precise ratio 0.236871
- naive_sweep_fuse(d=3.0, pitch=0.5, length=10.0): precise ratio 0.218512
- naive_sweep_fuse(d=6.0, pitch=1.0, length=10.0): precise ratio 0.238384
- naive_sweep_fuse(d=8.0, pitch=1.25, length=10.0): precise ratio 0.231722
- naive_sweep_fuse(d=8.0, pitch=1.25, length=80.0): precise ratio 0.191174
- naive_sweep_fuse(d=10.0, pitch=1.5, length=10.0): precise ratio 0.230710
- naive_sweep_fuse(d=10.0, pitch=1.5, length=100.0): precise ratio 0.182793
- naive_sweep_fuse(d=16.0, pitch=2.0, length=10.0): precise ratio 0.204723
- naive_sweep_fuse(d=20.0, pitch=2.5, length=10.0): precise ratio 0.219346
- naive_sweep_fuse(d=20.0, pitch=2.5, length=20.0): precise ratio 0.182789
- naive_sweep_fuse(d=20.0, pitch=2.5, length=200.0): precise ratio 0.149887

The ruled-surface profile is not identical to the pinned profile, so its ratio to this closed form is not an accuracy claim.

- load1 1.45 read 2026-10-08T19:41:48+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The quiet gate released as decisive. The output has 85 control rows over the eight sizes M2, M2.5, M3, M6, M8, M10, M16 and M20, of which 4 per size are class ok and the rest are silent_wrong or failure (the failure rows read, for example, "ValueError: Null TopoDS_Shape object"); each non-ok row is listed with its construction (naive, one_pipe or ruled) and reason, and the "Controls (D-06)" section follows. The output does not state whether these outcomes match the protocol's predictions; that comparison is not made here.


### 2026-10-08-a-rss

Run window (UTC): 2026-10-08T19:41:50+00:00 (first gate reading) to 2026-10-08T19:56:12+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: decisive at 2026-10-08T19:42:50+00:00. Gate readings: 3; first load1 1.45 read 2026-10-08T19:41:50+00:00; last load1 1.07 read 2026-10-08T19:42:50+00:00. Every reading is in the output below.
End reading: load1 9.60 read 2026-10-08T19:56:12+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-rss.jsonl` — 91 lines, sha256 b23c2cb92965f90cf1903069a9b868e75195442ba65ebb234c5fde95abd78dd5. Markdown output: `bench/results/thread-spike/2026-10-08-a-rss.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-rss

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: rss
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 1.45 read 2026-10-08T19:41:50+00:00
- load1 1.22 read 2026-10-08T19:42:20+00:00
- load1 1.07 read 2026-10-08T19:42:50+00:00
- release: decisive at 2026-10-08T19:42:50+00:00

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 6 | 6 | 0 | 0 | 0 | 0 | -6.244e-06 | -1.303e-05 | 1527254 | 76362784 | 111427062 | n/a | n/a | 2 |
| M2.5 | 6 | 6 | 0 | 0 | 0 | 0 | -5.980e-06 | -1.301e-05 | 1849022 | 92451184 | 135779813 | n/a | n/a | 2 |
| M3 | 6 | 6 | 0 | 0 | 0 | 0 | -6.172e-06 | -1.307e-05 | 1876430 | 93821584 | 138038762 | n/a | n/a | 2 |
| M3.5 | 6 | 6 | 0 | 0 | 0 | 0 | -1.320e-06 | -2.834e-06 | 1918124 | 95906284 | 141045322 | n/a | n/a | 2 |
| M4 | 6 | 6 | 0 | 0 | 0 | 0 | -1.330e-06 | -1.579e-06 | 2334230 | 116711584 | 170709745 | n/a | n/a | 2 |
| M5 | 6 | 6 | 0 | 0 | 0 | 0 | -1.241e-06 | -1.553e-06 | 2379002 | 118950184 | 173929849 | n/a | n/a | 2 |
| M6 | 6 | 6 | 0 | 0 | 0 | 0 | -1.280e-06 | -1.558e-06 | 2514644 | 125732284 | 183750700 | n/a | n/a | 2 |
| M7 | 6 | 6 | 0 | 0 | 0 | 0 | -1.141e-06 | -1.584e-06 | 2623594 | 131179784 | 192324208 | n/a | n/a | 2 |
| M8 | 6 | 6 | 0 | 0 | 0 | 0 | -1.219e-06 | -1.559e-06 | 4197042 | 209852184 | 310319264 | n/a | n/a | 3 |
| M10 | 6 | 6 | 0 | 0 | 0 | 0 | -1.182e-06 | -1.569e-06 | 6067054 | 303352784 | 444489267 | n/a | n/a | 4 |
| M12 | 6 | 6 | 0 | 0 | 0 | 0 | -1.158e-06 | -1.651e-06 | 6564820 | 328241084 | 480601483 | n/a | n/a | 4 |
| M14 | 6 | 6 | 0 | 0 | 0 | 0 | -1.039e-06 | -1.169e-06 | 7843182 | 392159184 | 572394494 | n/a | n/a | 4 |
| M16 | 6 | 6 | 0 | 0 | 0 | 0 | -7.723e-07 | -6.038e-07 | 8642612 | 432130684 | 628759460 | n/a | n/a | 4 |
| M18 | 6 | 6 | 0 | 0 | 0 | 0 | -8.692e-07 | -5.844e-07 | 8600290 | 430014584 | 626783954 | n/a | n/a | 4 |
| M20 | 6 | 6 | 0 | 0 | 0 | 0 | -7.723e-07 | -6.038e-07 | 8972812 | 448640684 | 653109977 | n/a | n/a | 4 |

- M8 right L=80 rod: over budget: fine raw + gzip-1 79618132 bytes > 67108864
- M10 right L=100 rod: over budget: fine raw + gzip-1 118560997 bytes > 67108864
- M10 left L=100 rod: over budget: fine raw + gzip-1 92186917 bytes > 67108864
- M12 right L=120 rod: over budget: fine raw + gzip-1 132507506 bytes > 67108864
- M12 left L=120 rod: over budget: fine raw + gzip-1 105124644 bytes > 67108864
- M14 right L=140 rod: over budget: fine raw + gzip-1 160586533 bytes > 67108864
- M14 left L=140 rod: over budget: fine raw + gzip-1 120591902 bytes > 67108864
- M16 right L=160 rod: over budget: fine raw + gzip-1 200304425 bytes > 67108864
- M16 left L=160 rod: over budget: fine raw + gzip-1 142616156 bytes > 67108864
- M18 right L=180 rod: over budget: fine raw + gzip-1 180668320 bytes > 67108864
- M18 left L=180 rod: over budget: fine raw + gzip-1 130791074 bytes > 67108864
- M20 right L=200 rod: over budget: fine raw + gzip-1 211134421 bytes > 67108864
- M20 left L=200 rod: over budget: fine raw + gzip-1 147962487 bytes > 67108864
- M2 right L=100 rod: over budget: fine raw + gzip-1 111427062 bytes > 67108864
- M2 left L=100 rod: over budget: fine raw + gzip-1 99842474 bytes > 67108864
- M2.5 right L=112.5 rod: over budget: fine raw + gzip-1 135779813 bytes > 67108864
- M2.5 left L=112.5 rod: over budget: fine raw + gzip-1 108579289 bytes > 67108864
- M3 right L=125 rod: over budget: fine raw + gzip-1 138038762 bytes > 67108864
- M3 left L=125 rod: over budget: fine raw + gzip-1 111738074 bytes > 67108864
- M3.5 right L=150 rod: over budget: fine raw + gzip-1 141045322 bytes > 67108864
- M3.5 left L=150 rod: over budget: fine raw + gzip-1 115312509 bytes > 67108864
- M4 right L=175 rod: over budget: fine raw + gzip-1 170709745 bytes > 67108864
- M4 left L=175 rod: over budget: fine raw + gzip-1 125788476 bytes > 67108864
- M5 right L=200 rod: over budget: fine raw + gzip-1 173929849 bytes > 67108864
- M5 left L=200 rod: over budget: fine raw + gzip-1 127898472 bytes > 67108864
- M6 right L=250 rod: over budget: fine raw + gzip-1 183750700 bytes > 67108864
- M6 left L=250 rod: over budget: fine raw + gzip-1 138336419 bytes > 67108864
- M7 right L=250 rod: over budget: fine raw + gzip-1 192324208 bytes > 67108864
- M7 left L=250 rod: over budget: fine raw + gzip-1 146846965 bytes > 67108864
- M8 right L=312.5 rod: over budget: fine raw + gzip-1 310319264 bytes > 67108864
- M8 left L=312.5 rod: over budget: fine raw + gzip-1 256552004 bytes > 67108864
- M10 right L=375 rod: over budget: fine raw + gzip-1 444489267 bytes > 67108864
- M10 left L=375 rod: over budget: fine raw + gzip-1 345427675 bytes > 67108864
- M12 right L=437.5 rod: over budget: fine raw + gzip-1 480601483 bytes > 67108864
- M12 left L=437.5 rod: over budget: fine raw + gzip-1 381125943 bytes > 67108864
- M14 right L=500 rod: over budget: fine raw + gzip-1 572394494 bytes > 67108864
- M14 left L=500 rod: over budget: fine raw + gzip-1 429681974 bytes > 67108864
- M16 right L=500 rod: over budget: fine raw + gzip-1 628759460 bytes > 67108864
- M16 left L=500 rod: over budget: fine raw + gzip-1 447170292 bytes > 67108864
- M18 right L=625 rod: over budget: fine raw + gzip-1 626783954 bytes > 67108864
- M18 left L=625 rod: over budget: fine raw + gzip-1 453994812 bytes > 67108864
- M20 right L=625 rod: over budget: fine raw + gzip-1 653109977 bytes > 67108864
- M20 left L=625 rod: over budget: fine raw + gzip-1 456706469 bytes > 67108864

### Peak RSS and the L19 gzip table

| Size | Hand | Preset | Turns | Length mm | Row | Peak RSS | Class |
|---|---|---|---|---|---|---|---|
| M2 | right | preview | 50 | 20 | standard max | 511.5 MiB (fresh child, this row only) | ok |
| M2 | right | fine | 50 | 20 | standard max | 865.7 MiB (fresh child, this row only) | ok |
| M2 | right | fine | 250 | 100 | frontier terminal | 1138.2 MiB (fresh child, this row only) | ok |
| M2 | left | preview | 50 | 20 | standard max | 509.1 MiB (fresh child, this row only) | ok |
| M2 | left | fine | 50 | 20 | standard max | 853.4 MiB (fresh child, this row only) | ok |
| M2 | left | fine | 250 | 100 | frontier terminal | 1113.8 MiB (fresh child, this row only) | ok |
| M2.5 | right | preview | 55.5556 | 25 | standard max | 515.5 MiB (fresh child, this row only) | ok |
| M2.5 | right | fine | 55.5556 | 25 | standard max | 943.0 MiB (fresh child, this row only) | ok |
| M2.5 | right | fine | 250 | 112.5 | frontier terminal | 1174.0 MiB (fresh child, this row only) | ok |
| M2.5 | left | preview | 55.5556 | 25 | standard max | 514.3 MiB (fresh child, this row only) | ok |
| M2.5 | left | fine | 55.5556 | 25 | standard max | 904.3 MiB (fresh child, this row only) | ok |
| M2.5 | left | fine | 250 | 112.5 | frontier terminal | 1158.1 MiB (fresh child, this row only) | ok |
| M3 | right | preview | 60 | 30 | standard max | 524.9 MiB (fresh child, this row only) | ok |
| M3 | right | fine | 60 | 30 | standard max | 1020.9 MiB (fresh child, this row only) | ok |
| M3 | right | fine | 250 | 125 | frontier terminal | 1256.8 MiB (fresh child, this row only) | ok |
| M3 | left | preview | 60 | 30 | standard max | 517.3 MiB (fresh child, this row only) | ok |
| M3 | left | fine | 60 | 30 | standard max | 1017.7 MiB (fresh child, this row only) | ok |
| M3 | left | fine | 250 | 125 | frontier terminal | 1179.0 MiB (fresh child, this row only) | ok |
| M3.5 | right | preview | 58.3333 | 35 | standard max | 525.8 MiB (fresh child, this row only) | ok |
| M3.5 | right | fine | 58.3333 | 35 | standard max | 1102.9 MiB (fresh child, this row only) | ok |
| M3.5 | right | fine | 250 | 150 | frontier terminal | 1248.4 MiB (fresh child, this row only) | ok |
| M3.5 | left | preview | 58.3333 | 35 | standard max | 520.5 MiB (fresh child, this row only) | ok |
| M3.5 | left | fine | 58.3333 | 35 | standard max | 1062.5 MiB (fresh child, this row only) | ok |
| M3.5 | left | fine | 250 | 150 | frontier terminal | 1231.3 MiB (fresh child, this row only) | ok |
| M4 | right | preview | 57.1429 | 40 | standard max | 529.2 MiB (fresh child, this row only) | ok |
| M4 | right | fine | 57.1429 | 40 | standard max | 1121.0 MiB (fresh child, this row only) | ok |
| M4 | right | fine | 250 | 175 | frontier terminal | 1367.9 MiB (fresh child, this row only) | ok |
| M4 | left | preview | 57.1429 | 40 | standard max | 525.1 MiB (fresh child, this row only) | ok |
| M4 | left | fine | 57.1429 | 40 | standard max | 1114.6 MiB (fresh child, this row only) | ok |
| M4 | left | fine | 250 | 175 | frontier terminal | 1246.5 MiB (fresh child, this row only) | ok |
| M5 | right | preview | 62.5 | 50 | standard max | 550.3 MiB (fresh child, this row only) | ok |
| M5 | right | fine | 62.5 | 50 | standard max | 1142.7 MiB (fresh child, this row only) | ok |
| M5 | right | fine | 250 | 200 | frontier terminal | 1392.6 MiB (fresh child, this row only) | ok |
| M5 | left | preview | 62.5 | 50 | standard max | 538.3 MiB (fresh child, this row only) | ok |
| M5 | left | fine | 62.5 | 50 | standard max | 1072.2 MiB (fresh child, this row only) | ok |
| M5 | left | fine | 250 | 200 | frontier terminal | 1226.2 MiB (fresh child, this row only) | ok |
| M6 | right | preview | 60 | 60 | standard max | 545.7 MiB (fresh child, this row only) | ok |
| M6 | right | fine | 60 | 60 | standard max | 1171.0 MiB (fresh child, this row only) | ok |
| M6 | right | fine | 250 | 250 | frontier terminal | 1387.2 MiB (fresh child, this row only) | ok |
| M6 | left | preview | 60 | 60 | standard max | 538.6 MiB (fresh child, this row only) | ok |
| M6 | left | fine | 60 | 60 | standard max | 1094.3 MiB (fresh child, this row only) | ok |
| M6 | left | fine | 250 | 250 | frontier terminal | 1310.8 MiB (fresh child, this row only) | ok |
| M7 | right | preview | 70 | 70 | standard max | 553.3 MiB (fresh child, this row only) | ok |
| M7 | right | fine | 70 | 70 | standard max | 1182.3 MiB (fresh child, this row only) | ok |
| M7 | right | fine | 250 | 250 | frontier terminal | 1430.1 MiB (fresh child, this row only) | ok |
| M7 | left | preview | 70 | 70 | standard max | 545.2 MiB (fresh child, this row only) | ok |
| M7 | left | fine | 70 | 70 | standard max | 1141.1 MiB (fresh child, this row only) | ok |
| M7 | left | fine | 250 | 250 | frontier terminal | 1278.3 MiB (fresh child, this row only) | ok |
| M8 | right | preview | 64 | 80 | standard max | 560.0 MiB (fresh child, this row only) | ok |
| M8 | right | fine | 64 | 80 | standard max | 1305.7 MiB (fresh child, this row only) | ok |
| M8 | right | fine | 250 | 312.5 | frontier terminal | 1769.9 MiB (fresh child, this row only) | ok |
| M8 | left | preview | 64 | 80 | standard max | 550.6 MiB (fresh child, this row only) | ok |
| M8 | left | fine | 64 | 80 | standard max | 1239.5 MiB (fresh child, this row only) | ok |
| M8 | left | fine | 250 | 312.5 | frontier terminal | 1608.6 MiB (fresh child, this row only) | ok |
| M10 | right | preview | 66.6667 | 100 | standard max | 560.2 MiB (fresh child, this row only) | ok |
| M10 | right | fine | 66.6667 | 100 | standard max | 1463.4 MiB (fresh child, this row only) | ok |
| M10 | right | fine | 250 | 375 | frontier terminal | 2267.5 MiB (fresh child, this row only) | ok |
| M10 | left | preview | 66.6667 | 100 | standard max | 554.0 MiB (fresh child, this row only) | ok |
| M10 | left | fine | 66.6667 | 100 | standard max | 1407.6 MiB (fresh child, this row only) | ok |
| M10 | left | fine | 250 | 375 | frontier terminal | 1885.2 MiB (fresh child, this row only) | ok |
| M12 | right | preview | 68.5714 | 120 | standard max | 567.9 MiB (fresh child, this row only) | ok |
| M12 | right | fine | 68.5714 | 120 | standard max | 1688.5 MiB (fresh child, this row only) | ok |
| M12 | right | fine | 250 | 437.5 | frontier terminal | 2392.9 MiB (fresh child, this row only) | ok |
| M12 | left | preview | 68.5714 | 120 | standard max | 558.7 MiB (fresh child, this row only) | ok |
| M12 | left | fine | 68.5714 | 120 | standard max | 1602.6 MiB (fresh child, this row only) | ok |
| M12 | left | fine | 250 | 437.5 | frontier terminal | 2112.9 MiB (fresh child, this row only) | ok |
| M14 | right | preview | 70 | 140 | standard max | 581.5 MiB (fresh child, this row only) | ok |
| M14 | right | fine | 70 | 140 | standard max | 1872.4 MiB (fresh child, this row only) | ok |
| M14 | right | fine | 250 | 500 | frontier terminal | 2610.5 MiB (fresh child, this row only) | ok |
| M14 | left | preview | 70 | 140 | standard max | 571.0 MiB (fresh child, this row only) | ok |
| M14 | left | fine | 70 | 140 | standard max | 1748.7 MiB (fresh child, this row only) | ok |
| M14 | left | fine | 250 | 500 | frontier terminal | 2264.2 MiB (fresh child, this row only) | ok |
| M16 | right | preview | 80 | 160 | standard max | 643.0 MiB (fresh child, this row only) | ok |
| M16 | right | fine | 80 | 160 | standard max | 1916.6 MiB (fresh child, this row only) | ok |
| M16 | right | fine | 250 | 500 | frontier terminal | 2730.9 MiB (fresh child, this row only) | ok |
| M16 | left | preview | 80 | 160 | standard max | 639.8 MiB (fresh child, this row only) | ok |
| M16 | left | fine | 80 | 160 | standard max | 1784.3 MiB (fresh child, this row only) | ok |
| M16 | left | fine | 250 | 500 | frontier terminal | 2281.6 MiB (fresh child, this row only) | ok |
| M18 | right | preview | 72 | 180 | standard max | 673.5 MiB (fresh child, this row only) | ok |
| M18 | right | fine | 72 | 180 | standard max | 1795.1 MiB (fresh child, this row only) | ok |
| M18 | right | fine | 250 | 625 | frontier terminal | 2741.7 MiB (fresh child, this row only) | ok |
| M18 | left | preview | 72 | 180 | standard max | 676.5 MiB (fresh child, this row only) | ok |
| M18 | left | fine | 72 | 180 | standard max | 1651.4 MiB (fresh child, this row only) | ok |
| M18 | left | fine | 250 | 625 | frontier terminal | 2329.5 MiB (fresh child, this row only) | ok |
| M20 | right | preview | 80 | 200 | standard max | 711.0 MiB (fresh child, this row only) | ok |
| M20 | right | fine | 80 | 200 | standard max | 1854.9 MiB (fresh child, this row only) | ok |
| M20 | right | fine | 250 | 625 | frontier terminal | 2804.6 MiB (fresh child, this row only) | ok |
| M20 | left | preview | 80 | 200 | standard max | 682.4 MiB (fresh child, this row only) | ok |
| M20 | left | fine | 80 | 200 | standard max | 1785.3 MiB (fresh child, this row only) | ok |
| M20 | left | fine | 250 | 625 | frontier terminal | 2291.8 MiB (fresh child, this row only) | ok |

L19 gzip table (levels 1, 6 and 9 on the row's own STL, fresh child):

| Size | Level | Output bytes | Single-threaded median ms | 10-concurrent wall median ms |
|---|---|---|---|---|
| M2 | 1 | 7024461 | 101.7 | 122.6 |
| M2 | 6 | 6752985 | 183.6 | 222.1 |
| M2 | 9 | 6754143 | 206.7 | 254.4 |
| M2.5 | 1 | 9639781 | 143.4 | 169.0 |
| M2.5 | 6 | 9219593 | 242.3 | 293.5 |
| M2.5 | 9 | 9220536 | 264.4 | 323.7 |
| M3 | 1 | 10634274 | 160.2 | 186.7 |
| M3 | 6 | 10139845 | 288.7 | 353.4 |
| M3 | 9 | 10140314 | 329.3 | 403.5 |
| M3.5 | 1 | 10583521 | 162.1 | 186.8 |
| M3.5 | 6 | 10147763 | 275.7 | 330.1 |
| M3.5 | 9 | 10148944 | 300.0 | 360.2 |
| M4 | 1 | 12356444 | 189.8 | 218.2 |
| M4 | 6 | 11848427 | 323.9 | 381.7 |
| M4 | 9 | 11850333 | 348.5 | 413.0 |
| M5 | 1 | 13850880 | 210.1 | 240.3 |
| M5 | 6 | 13246686 | 364.3 | 426.0 |
| M5 | 9 | 13248972 | 397.4 | 467.7 |
| M6 | 1 | 13970930 | 211.8 | 242.4 |
| M6 | 6 | 13360183 | 374.0 | 436.5 |
| M6 | 9 | 13361643 | 417.4 | 490.4 |
| M7 | 1 | 17249144 | 260.4 | 297.4 |
| M7 | 6 | 16505179 | 459.8 | 539.1 |
| M7 | 9 | 16507342 | 521.9 | 618.4 |
| M8 | 1 | 25818148 | 387.9 | 447.9 |
| M8 | 6 | 24831288 | 652.8 | 766.7 |
| M8 | 9 | 24834915 | 721.2 | 847.9 |
| M10 | 1 | 37691313 | 563.3 | 649.6 |
| M10 | 6 | 35970130 | 1019.6 | 1191.7 |
| M10 | 9 | 35975052 | 1111.5 | 1298.9 |
| M12 | 1 | 42084822 | 632.5 | 733.0 |
| M12 | 6 | 40259958 | 1142.4 | 1335.4 |
| M12 | 9 | 40262125 | 1221.5 | 1438.2 |
| M14 | 1 | 50611949 | 765.1 | 885.9 |
| M14 | 6 | 48446123 | 1434.1 | 1684.6 |
| M14 | 9 | 48447578 | 1580.8 | 1877.8 |
| M16 | 1 | 62726041 | 942.2 | 1104.9 |
| M16 | 6 | 60072616 | 1795.3 | 2111.0 |
| M16 | 9 | 60071266 | 1985.2 | 2338.3 |
| M18 | 1 | 56785836 | 847.5 | 998.2 |
| M18 | 6 | 54535211 | 1533.7 | 1803.9 |
| M18 | 9 | 54539361 | 1646.8 | 1942.5 |
| M20 | 1 | 66190237 | 982.5 | 1161.8 |
| M20 | 6 | 63558367 | 1751.3 | 2064.0 |
| M20 | 9 | 63562242 | 1873.8 | 2198.8 |

- M2: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M2.5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M3: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M3.5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M4: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M6: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M7: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M8: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M10: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M12: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M14: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M16: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M18: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M20: selected gzip level 1 (spur L19's rule, `select_gzip_level`)

- load1 9.60 read 2026-10-08T19:56:12+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The quiet gate released as decisive. The output has 90 rows (six per size, M2 to M20), all class ok, and the "Peak RSS and the L19 gzip table" section lists a fresh-child peak RSS for each, for example 1138.2 MiB for M2 right fine at 250 turns, L = 100 mm. Each figure is one measurement on this host, and the output draws no limit from it.


### 2026-10-08-a-pair

Run window (UTC): 2026-10-08T19:56:15+00:00 (first gate reading) to 2026-10-08T23:30:27+00:00 (end reading). Platform: native arm64 (no container).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: decisive at 2026-10-08T20:01:15+00:00. Gate readings: 11; first load1 9.07 read 2026-10-08T19:56:15+00:00; last load1 1.17 read 2026-10-08T20:01:15+00:00. Every reading is in the output below.
End reading: load1 1.40 read 2026-10-08T23:30:27+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-pair.jsonl` — 273 lines, sha256 1644650ed5b418fc2b43bfa8fd875d371f0fc4940018f67b5b3241df6c84d9f3. Markdown output: `bench/results/thread-spike/2026-10-08-a-pair.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-pair

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: pair
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 9.07 read 2026-10-08T19:56:15+00:00
- load1 6.15 read 2026-10-08T19:56:45+00:00
- load1 4.28 read 2026-10-08T19:57:15+00:00
- load1 3.28 read 2026-10-08T19:57:45+00:00
- load1 2.54 read 2026-10-08T19:58:15+00:00
- load1 2.00 read 2026-10-08T19:58:45+00:00
- load1 1.55 read 2026-10-08T19:59:15+00:00
- load1 1.61 read 2026-10-08T19:59:45+00:00
- load1 1.38 read 2026-10-08T20:00:15+00:00
- load1 1.28 read 2026-10-08T20:00:45+00:00
- load1 1.17 read 2026-10-08T20:01:15+00:00
- release: decisive at 2026-10-08T20:01:15+00:00

Locked K = 3; every cell below is read at it. A cell is proven only if all 3 matched poses read empty (<= 1e-06 mm3) and all 3 controls read within 0.001 of the closed form (D-12, D-14).

#### M2 right hand (m = 1.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.428872/0.428877/0.428872 | 0.859203/0.859202/0.859203 | 0.859202 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0.647798/0/0.647798 | 0.647802 | 0/0/0 ; 1/0/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.455395/0.455395/0.455396 | 0.455399 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.284711/0 | 0.284715 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.138463/0.138464/0.138464 | 0.138468 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0/0.0244833/0 | 0.0244813 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M2 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.284715 mm3); control at theta +2.0944 reads empty (closed form 0.284715 mm3)
- M2 right c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 0.0244813 mm3); control at theta +2.0944 reads empty (closed form 0.0244813 mm3)

#### M2 left hand (m = 1.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.428872/0.428877/0.428872 | 0.859203/0.859202/0.859202 | 0.859202 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0.647798/0/0.647797 | 0.647802 | 0/0/0 ; 1/0/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.455396/0.455395/0.455395 | 0.455399 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.284711/0 | 0.284715 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.138464/0.138464/0.138463 | 0.138468 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0/0.0244833/0 | 0.0244813 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M2 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.284715 mm3); control at theta +2.0944 reads empty (closed form 0.284715 mm3)
- M2 left c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 0.0244813 mm3); control at theta +2.0944 reads empty (closed form 0.0244813 mm3)

#### M2.5 right hand (m = 2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.683622/0.6836/0.683576 | 1.49169/1.49171/1.49169 | 1.49169 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.15397/1.15398/1.15397 | 1.15397 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.845031/0.845045/0.845032 | 0.845035 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.567913/0 | 0.567908 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.325602/0.325609/0.325603 | 0.325612 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.121421/0.121424/0.121422 | 0.121426 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M2.5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2.5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2.5 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.567908 mm3); control at theta +2.0944 reads empty (closed form 0.567908 mm3)

#### M2.5 left hand (m = 2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.683576/0.6836/0.683622 | 1.49169/1.49171/1.49168 | 1.49169 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.15397/1.15399/1.15397 | 1.15397 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.845034/0.845046/0.84503 | 0.845035 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.567914/0 | 0.567908 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.325603/0.32561/0.325601 | 0.325612 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.121421/0.121424/0.12142 | 0.121426 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M2.5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2.5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2.5 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.567908 mm3); control at theta +2.0944 reads empty (closed form 0.567908 mm3)

#### M3 right hand (m = 2.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.997365/0.99734/0.997269 | 0/2.35538/2.35539 | 2.35543 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.86255/1.86258/1.86258 | 1.86262 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/1.40915/1.40915 | 1.4092 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0.998331/0.998359/0.99836 | 0.998409 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 0/0.633481/0 | 0.633531 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0.317787/0.317808/0.317809 | 0.317827 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M3 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 1.4092 mm3)
- M3 right c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 0.633531 mm3); control at theta +2.0944 reads empty (closed form 0.633531 mm3)

#### M3 left hand (m = 2.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.997269/0.99734/0.997365 | 2.35539/2.35538/0 | 2.35543 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.86258/1.86258/1.86255 | 1.86262 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 1.40915/1.40915/0 | 1.4092 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0.998359/0.998359/0.99833 | 0.998409 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 0/0.633481/0 | 0.633531 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0.317809/0.317808/0.317787 | 0.317827 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M3 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 1.4092 mm3)
- M3 left c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 0.633531 mm3); control at theta +2.0944 reads empty (closed form 0.633531 mm3)

#### M3.5 right hand (m = 2.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.35671/1.3567/1.3567 | 3.69532/3.69532/3.69531 | 3.69532 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 3.0328/3.03279/3.03279 | 3.0328 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 2.4141/2.4141/2.4141 | 2.4141 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 1.84241/1.8424/1.8424 | 1.8424 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 1.32088/1.32088/1.32088 | 1.32088 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.852706/0.852705/0.852704 | 0.852709 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3.5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3.5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M3.5 left hand (m = 2.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.3567/1.3567/1.35671 | 3.69531/3.69531/3.69532 | 3.69532 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000633645/0/0 | 3.03279/3.03279/3.0328 | 3.0328 | 25/0/0 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 2.4141/2.4141/2.4141 | 2.4141 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 1.8424/1.8424/1.84241 | 1.8424 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 1.32088/1.32088/1.32088 | 1.32088 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.852704/0.852704/0.852707 | 0.852709 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3.5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3.5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M4 right hand (m = 3.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.77124/1.77123/1.77123 | 5.46813/5.46812/5.46812 | 5.46812 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 5.79139e-06/0/-0.00279567 | 4.61056/4.61056/4.61056 | 4.61055 | 4/0/12 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/3.80135/3.80135 | 3.80135 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 3.04361/3.04361/3.04361 | 3.04361 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 2.34045/2.34045/2.34045 | 2.34044 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 1.69497/1.69497/1.69497 | 1.69497 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M4 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M4 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M4 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 3.80135 mm3)

#### M4 left hand (m = 3.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.77123/1.77123/1.77124 | 5.46812/5.46812/5.46812 | 5.46812 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0910952/0/-0.00132387 | 4.61056/4.61056/4.61056 | 4.61055 | 10/0/12 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 3.80135/3.80135/0 | 3.80135 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 3.04361/3.04361/3.04361 | 3.04361 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 2.34045/2.34045/2.34045 | 2.34044 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 1.69497/1.69497/1.69497 | 1.69497 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M4 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M4 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M4 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 3.80135 mm3)

#### M5 right hand (m = 4.7 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 3.29489/3.29482/3.29482 | 11.3681/11.3681/11.3681 | 11.3681 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -2.1969e-06/0/-0.0184956 | 9.76954/9.76954/9.76954 | 9.76953 | 5/0/15 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 8.25346/8.25346/0 | 8.25345 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 6.82381/6.82382/6.82381 | 6.8238 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 5.4846/5.48461/5.48461 | 5.4846 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 4.23983/4.23983/4.23983 | 4.23982 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M5 right c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 8.25345 mm3)

#### M5 left hand (m = 4.7 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 3.29482/3.29482/3.29489 | 11.3681/11.3681/11.3681 | 11.3681 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00240809/0/0.00325241 | 9.76954/9.76954/9.76954 | 9.76953 | 17/0/11 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/8.25346/8.25346 | 8.25345 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 6.82381/6.82381/6.82381 | 6.8238 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 5.48461/5.4846/5.4846 | 5.4846 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 4.23983/4.23983/4.23983 | 4.23982 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M5 left c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 8.25345 mm3)

#### M6 right hand (m = 5.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 4.36276/4.36266/4.36271 | 18.2374/18.2374/18.2373 | 18.2374 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00177739/0/-0.00603191 | 16.1428/16.1428/16.1427 | 16.1427 | 13/0/7 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 14.1335/14.1335/14.1334 | 14.1335 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 12.213/12.213/12.213 | 12.213 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 10.385/10.385/10.3849 | 10.385 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 8.65294/8.65294/8.65289 | 8.65288 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M6 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M6 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M6 left hand (m = 5.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 4.36271/4.36266/4.36276 | 18.2373/18.2374/18.2374 | 18.2374 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.00513391/0/-0.0115552 | 16.1427/16.1428/16.1428 | 16.1427 | 9/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 14.1334/14.1335/14.1335 | 14.1335 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 12.213/12.213/12.213 | 12.213 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 10.3849/10.385/10.385 | 10.385 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 8.65289/8.65294/8.65294 | 8.65288 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M6 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M6 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M7 right hand (m = 5.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 5.57807/5.5779/5.57786 | 23.3066/23.3066/23.3066 | 23.3066 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.319506/0/-0.492389 | 20.5983/20.5983/20.5983 | 20.5983 | 11/0/14 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/18.0073/18.0073 | 18.0073 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 15.5375/15.5374/15.5374 | 15.5375 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 13.1925/13.1924/13.1925 | 13.1925 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 10.9762/10.9761/10.9762 | 10.9762 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M7 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M7 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M7 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 18.0073 mm3)

#### M7 left hand (m = 5.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 5.57786/5.5779/5.57807 | 23.3066/23.3066/23.3066 | 23.3066 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.453107/0/-0.00801368 | 20.5983/20.5983/20.5983 | 20.5983 | 19/0/8 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 18.0073/18.0073/0 | 18.0073 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 15.5374/15.5375/15.5374 | 15.5375 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 13.1925/13.1925/13.1925 | 13.1925 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 10.9762/10.9762/10.9762 | 10.9762 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M7 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M7 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M7 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 18.0073 mm3)

#### M8 right hand (m = 6.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 7.67898/7.6787/7.67872 | 39.1066/39.1066/0 | 39.1065 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.00082956/0/0.00415998 | 35.4231/35.4231/35.4231 | 35.423 | 12/0/9 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 31.8635/31.8635/31.8635 | 31.8635 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 28.4315/28.4315/28.4315 | 28.4315 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 25.1309/25.1309/25.1309 | 25.1308 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 21.9652/21.9652/21.9652 | 21.9652 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M8 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M8 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M8 left hand (m = 6.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 7.67872/7.6787/7.67898 | 0/39.1065/39.1066 | 39.1065 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0393199/0/0.00759806 | 35.4231/35.4231/35.4231 | 35.423 | 11/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 31.8635/31.8635/31.8635 | 31.8635 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 28.4315/28.4315/28.4315 | 28.4315 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 25.1308/25.1308/25.1308 | 25.1308 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 21.9652/21.9652/21.9652 | 21.9652 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M8 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M8 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M10 right hand (m = 8.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 11.9241/11.9235/11.923 | 71.6178/71.6178/71.6181 | 71.618 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000873794/0/0.00116949 | 65.9036/65.9037/65.9039 | 65.9038 | 7/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/60.3527/60.353 | 60.3528 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0/54.9688/54.9691 | 54.9689 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 49.7557/49.7557/49.756 | 49.7558 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 44.7172/44.7173/44.7175 | 44.7174 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M10 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M10 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M10 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 60.3528 mm3)
- M10 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 54.9689 mm3)

#### M10 left hand (m = 8.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 11.923/11.9235/11.9241 | 71.6181/71.6179/71.6178 | 71.618 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0225569/0/0.00510398 | 65.9039/65.9037/65.9036 | 65.9038 | 9/0/11 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 60.353/60.3528/0 | 60.3528 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 54.969/54.9688/0 | 54.9689 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 49.756/49.7558/49.7556 | 49.7558 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 44.7175/44.7173/44.7172 | 44.7174 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M10 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M10 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M10 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 60.3528 mm3)
- M10 left c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 54.9689 mm3)

#### M12 right hand (m = 10.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 18.4657/18.4649/18.465 | 127.789/127.789/127.789 | 127.789 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00778178/0/0.0176886 | 118.947/118.947/0 | 118.947 | 8/0/8 ; 1/1/0 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 110.325/110.325/0 | 110.325 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 101.926/101.926/101.926 | 101.926 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 93.7549/93.7551/93.755 | 93.7548 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 85.8153/85.8155/85.8155 | 85.8153 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M12 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M12 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M12 right c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 110.325 mm3)

#### M12 left hand (m = 10.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 18.465/18.4649/18.4657 | 127.789/127.789/127.789 | 127.789 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0593007/0/-0.0279531 | 0/118.947/118.947 | 118.947 | 13/0/11 ; 0/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/110.325/110.325 | 110.325 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 101.926/101.926/101.926 | 101.926 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 93.7549/93.7549/93.7548 | 93.7548 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 85.8154/85.8154/85.8153 | 85.8153 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M12 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M12 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M12 left c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 110.325 mm3)

#### M14 right hand (m = 12.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 25.6006/25.5995/25.6008 | 200.577/200.576/200.576 | 200.576 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000104004/0/-9.33039e-05 | 188.328/188.328/188.327 | 188.328 | 6/0/6 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 176.348/176.347/176.346 | 176.347 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 164.639/164.639/0 | 164.639 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 153.208/153.207/153.207 | 153.207 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 142.057/142.057/142.056 | 142.057 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M14 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M14 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M14 right c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 164.639 mm3)

#### M14 left hand (m = 12.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 25.6008/25.5995/25.6006 | 200.576/200.576/200.577 | 200.576 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0249251/0/-0.0240166 | 188.327/188.328/188.328 | 188.328 | 10/0/8 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 176.346/176.347/176.347 | 176.347 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/164.639/164.639 | 164.639 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 153.207/153.207/153.208 | 153.207 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 142.056/142.057/142.057 | 142.057 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M14 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M14 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M14 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 164.639 mm3)

#### M16 right hand (m = 14.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 34.249/34.249/34.2488 | 268.248/268.248/268.248 | 268.249 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 251.727/251.727/251.727 | 251.728 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 235.584/235.583/235.583 | 235.585 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 219.822/219.822/219.822 | 219.823 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 204.447/204.447/204.447 | 204.448 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 189.465/189.464/189.464 | 189.466 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M16 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M16 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M16 left hand (m = 14.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 34.2488/34.249/34.249 | 268.248/268.248/268.248 | 268.249 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 251.727/251.727/251.727 | 251.728 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 235.583/235.583/235.584 | 235.585 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 219.822/219.822/219.822 | 219.823 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 204.447/204.447/204.447 | 204.448 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 189.464/189.464/189.465 | 189.466 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M16 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M16 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M18 right hand (m = 15.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 40.7729/40.7719/40.7716 | 0/394.049/394.049 | 394.05 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0/374.563/374.562 | 374.564 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/355.422/355.421 | 355.423 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0/336.63/336.63 | 336.632 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0/318.193/318.193 | 318.194 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0/300.113/300.113 | 300.115 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M18 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M18 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M18 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 355.423 mm3)
- M18 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 336.632 mm3)
- M18 right c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 318.194 mm3)
- M18 right c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 300.115 mm3)

#### M18 left hand (m = 15.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 40.7716/40.7719/40.7729 | 394.049/394.049/0 | 394.05 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 374.562/374.562/0 | 374.564 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 355.421/355.421/0 | 355.423 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 336.63/336.63/0 | 336.632 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 318.192/318.193/0 | 318.194 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 300.113/300.113/0 | 300.115 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M18 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M18 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M18 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 355.423 mm3)
- M18 left c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 336.632 mm3)
- M18 left c=0.15: inconclusive: control at theta +2.0944 reads empty (closed form 318.194 mm3)
- M18 left c=0.2: inconclusive: control at theta +2.0944 reads empty (closed form 300.115 mm3)

#### M20 right hand (m = 18 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 52.1062/52.1031/52.1072 | 503.428/503.428/503.429 | 503.429 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 478.369/478.369/478.37 | 478.369 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 453.768/453.768/453.769 | 453.768 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 429.63/429.63/429.632 | 429.631 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 405.961/405.962/405.963 | 405.962 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 382.766/382.766/382.767 | 382.766 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M20 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M20 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M20 left hand (m = 18 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 52.1072/52.1031/52.1062 | 503.429/503.428/503.428 | 503.429 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 478.37/478.368/478.368 | 478.369 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 453.769/453.768/453.768 | 453.768 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 429.631/429.63/429.63 | 429.631 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 405.963/405.961/405.961 | 405.962 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 382.767/382.766/382.766 | 382.766 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M20 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M20 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### Falsifiability (D-14)

- M2: falsifiable on both hands
- M2 right: excluded clearances 0.1, 0.2
- M2 left: excluded clearances 0.1, 0.2
- M2: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M2 right: sensitivity (c = -0.05) ok
- M2 left: sensitivity (c = -0.05) ok
- M2.5: falsifiable on both hands
- M2.5 right: excluded clearances 0.1
- M2.5 left: excluded clearances 0.1
- M2.5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M2.5 right: sensitivity (c = -0.05) ok
- M2.5 left: sensitivity (c = -0.05) ok
- M3: falsifiable on both hands
- M3 right: excluded clearances 0.05, 0.15
- M3 left: excluded clearances 0.05, 0.15
- M3: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M3 right: sensitivity (c = -0.05) ok
- M3 left: sensitivity (c = -0.05) ok
- M3.5: falsifiable on both hands
- M3.5 right: excluded clearances none
- M3.5 left: excluded clearances none
- M3.5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M3.5 right: sensitivity (c = -0.05) ok
- M3.5 left: sensitivity (c = -0.05) ok
- M4: falsifiable on both hands
- M4 right: excluded clearances 0.05
- M4 left: excluded clearances 0.05
- M4: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M4 right: sensitivity (c = -0.05) ok
- M4 left: sensitivity (c = -0.05) ok
- M5: falsifiable on both hands
- M5 right: excluded clearances 0.05
- M5 left: excluded clearances 0.05
- M5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M5 right: sensitivity (c = -0.05) ok
- M5 left: sensitivity (c = -0.05) ok
- M6: falsifiable on both hands
- M6 right: excluded clearances none
- M6 left: excluded clearances none
- M6: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M6 right: sensitivity (c = -0.05) ok
- M6 left: sensitivity (c = -0.05) ok
- M7: falsifiable on both hands
- M7 right: excluded clearances 0.05
- M7 left: excluded clearances 0.05
- M7: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M7 right: sensitivity (c = -0.05) ok
- M7 left: sensitivity (c = -0.05) ok
- M8: falsifiable on both hands
- M8 right: excluded clearances none
- M8 left: excluded clearances none
- M8: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M8 right: sensitivity (c = -0.05) ok
- M8 left: sensitivity (c = -0.05) ok
- M10: falsifiable on both hands
- M10 right: excluded clearances 0.05, 0.1
- M10 left: excluded clearances 0.05, 0.1
- M10: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M10 right: sensitivity (c = -0.05) ok
- M10 left: sensitivity (c = -0.05) ok
- M12: falsifiable on both hands
- M12 right: excluded clearances 0.05
- M12 left: excluded clearances 0.05
- M12: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M12 right: sensitivity (c = -0.05) ok
- M12 left: sensitivity (c = -0.05) ok
- M14: falsifiable on both hands
- M14 right: excluded clearances 0.1
- M14 left: excluded clearances 0.1
- M14: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M14 right: sensitivity (c = -0.05) ok
- M14 left: sensitivity (c = -0.05) ok
- M16: falsifiable on both hands
- M16 right: excluded clearances none
- M16 left: excluded clearances none
- M16: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M16 right: sensitivity (c = -0.05) ok
- M16 left: sensitivity (c = -0.05) ok
- not falsifiable for size M18 (right, left hand): the escape clause fires
- M18 right: excluded clearances 0.05, 0.1, 0.15, 0.2
- M18 left: excluded clearances 0.05, 0.1, 0.15, 0.2
- M18: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M18 right: sensitivity (c = -0.05) ok
- M18 left: sensitivity (c = -0.05) ok
- M20: falsifiable on both hands
- M20 right: excluded clearances none
- M20 left: excluded clearances none
- M20: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M20 right: sensitivity (c = -0.05) ok
- M20 left: sensitivity (c = -0.05) ok

#### Reference K (reported, not verdict inputs)

| Size | K | c = 0.05 | c = 0.1 | c = 0.15 | c = 0.2 |
|---|---|---|---|---|---|
| M2 | 5 | inconclusive | inconclusive | inconclusive | inconclusive |
| M2 | 10 | proven | inconclusive | inconclusive | inconclusive |
| M6 | 5 | inconclusive | inconclusive | inconclusive | inconclusive |
| M6 | 10 | proven | inconclusive | inconclusive | inconclusive |
| M10 | 5 | inconclusive | proven | proven | proven |
| M10 | 10 | inconclusive | inconclusive | inconclusive | inconclusive |
| M20 | 5 | proven | proven | proven | inconclusive |
| M20 | 10 | inconclusive | inconclusive | inconclusive | inconclusive |

#### Variant rules (reported, never the verdict)

Computed from the same recorded readings. The D-14 column is the verdict; the others are for Phase 5's revision and never feed it (owner ruling R1).

| Cell | D-14 verdict | two of three controls fire in band | seam pose excluded | same-pose c=-0.05 reading as the control |
|---|---|---|---|---|
| M2 right c=0.05 K=3 | proven | yes | yes | yes |
| M2 right c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2 right c=0.15 K=3 | proven | yes | yes | yes |
| M2 right c=0.2 K=3 | inconclusive | NO | NO | yes |
| M2 left c=0.05 K=3 | proven | yes | yes | yes |
| M2 left c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2 left c=0.15 K=3 | proven | yes | yes | yes |
| M2 left c=0.2 K=3 | inconclusive | NO | NO | yes |
| M2.5 right c=0.05 K=3 | proven | yes | yes | yes |
| M2.5 right c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2.5 right c=0.15 K=3 | proven | yes | yes | yes |
| M2.5 right c=0.2 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.05 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2.5 left c=0.15 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.2 K=3 | proven | yes | yes | yes |
| M3 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M3 right c=0.1 K=3 | proven | yes | yes | yes |
| M3 right c=0.15 K=3 | inconclusive | NO | NO | yes |
| M3 right c=0.2 K=3 | proven | yes | yes | yes |
| M3 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M3 left c=0.1 K=3 | proven | yes | yes | yes |
| M3 left c=0.15 K=3 | inconclusive | NO | NO | yes |
| M3 left c=0.2 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.05 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.1 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.15 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.2 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.05 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.1 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.15 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.2 K=3 | proven | yes | yes | yes |
| M4 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M4 right c=0.1 K=3 | proven | yes | yes | yes |
| M4 right c=0.15 K=3 | proven | yes | yes | yes |
| M4 right c=0.2 K=3 | proven | yes | yes | yes |
| M4 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M4 left c=0.1 K=3 | proven | yes | yes | yes |
| M4 left c=0.15 K=3 | proven | yes | yes | yes |
| M4 left c=0.2 K=3 | proven | yes | yes | yes |
| M5 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M5 right c=0.1 K=3 | proven | yes | yes | yes |
| M5 right c=0.15 K=3 | proven | yes | yes | yes |
| M5 right c=0.2 K=3 | proven | yes | yes | yes |
| M5 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M5 left c=0.1 K=3 | proven | yes | yes | yes |
| M5 left c=0.15 K=3 | proven | yes | yes | yes |
| M5 left c=0.2 K=3 | proven | yes | yes | yes |
| M6 right c=0.05 K=3 | proven | yes | yes | yes |
| M6 right c=0.1 K=3 | proven | yes | yes | yes |
| M6 right c=0.15 K=3 | proven | yes | yes | yes |
| M6 right c=0.2 K=3 | proven | yes | yes | yes |
| M6 left c=0.05 K=3 | proven | yes | yes | yes |
| M6 left c=0.1 K=3 | proven | yes | yes | yes |
| M6 left c=0.15 K=3 | proven | yes | yes | yes |
| M6 left c=0.2 K=3 | proven | yes | yes | yes |
| M7 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M7 right c=0.1 K=3 | proven | yes | yes | yes |
| M7 right c=0.15 K=3 | proven | yes | yes | yes |
| M7 right c=0.2 K=3 | proven | yes | yes | yes |
| M7 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M7 left c=0.1 K=3 | proven | yes | yes | yes |
| M7 left c=0.15 K=3 | proven | yes | yes | yes |
| M7 left c=0.2 K=3 | proven | yes | yes | yes |
| M8 right c=0.05 K=3 | proven | yes | yes | yes |
| M8 right c=0.1 K=3 | proven | yes | yes | yes |
| M8 right c=0.15 K=3 | proven | yes | yes | yes |
| M8 right c=0.2 K=3 | proven | yes | yes | yes |
| M8 left c=0.05 K=3 | proven | yes | yes | yes |
| M8 left c=0.1 K=3 | proven | yes | yes | yes |
| M8 left c=0.15 K=3 | proven | yes | yes | yes |
| M8 left c=0.2 K=3 | proven | yes | yes | yes |
| M10 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M10 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M10 right c=0.15 K=3 | proven | yes | yes | yes |
| M10 right c=0.2 K=3 | proven | yes | yes | yes |
| M10 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M10 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M10 left c=0.15 K=3 | proven | yes | yes | yes |
| M10 left c=0.2 K=3 | proven | yes | yes | yes |
| M12 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M12 right c=0.1 K=3 | proven | yes | yes | yes |
| M12 right c=0.15 K=3 | proven | yes | yes | yes |
| M12 right c=0.2 K=3 | proven | yes | yes | yes |
| M12 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M12 left c=0.1 K=3 | proven | yes | yes | yes |
| M12 left c=0.15 K=3 | proven | yes | yes | yes |
| M12 left c=0.2 K=3 | proven | yes | yes | yes |
| M14 right c=0.05 K=3 | proven | yes | yes | yes |
| M14 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M14 right c=0.15 K=3 | proven | yes | yes | yes |
| M14 right c=0.2 K=3 | proven | yes | yes | yes |
| M14 left c=0.05 K=3 | proven | yes | yes | yes |
| M14 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M14 left c=0.15 K=3 | proven | yes | yes | yes |
| M14 left c=0.2 K=3 | proven | yes | yes | yes |
| M16 right c=0.05 K=3 | proven | yes | yes | yes |
| M16 right c=0.1 K=3 | proven | yes | yes | yes |
| M16 right c=0.15 K=3 | proven | yes | yes | yes |
| M16 right c=0.2 K=3 | proven | yes | yes | yes |
| M16 left c=0.05 K=3 | proven | yes | yes | yes |
| M16 left c=0.1 K=3 | proven | yes | yes | yes |
| M16 left c=0.15 K=3 | proven | yes | yes | yes |
| M16 left c=0.2 K=3 | proven | yes | yes | yes |
| M18 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.15 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.2 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.15 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.2 K=3 | inconclusive | yes | NO | yes |
| M20 right c=0.05 K=3 | proven | yes | yes | yes |
| M20 right c=0.1 K=3 | proven | yes | yes | yes |
| M20 right c=0.15 K=3 | proven | yes | yes | yes |
| M20 right c=0.2 K=3 | proven | yes | yes | yes |
| M20 left c=0.05 K=3 | proven | yes | yes | yes |
| M20 left c=0.1 K=3 | proven | yes | yes | yes |
| M20 left c=0.15 K=3 | proven | yes | yes | yes |
| M20 left c=0.2 K=3 | proven | yes | yes | yes |

- load1 1.40 read 2026-10-08T23:30:27+00:00 (includes this run's own load)
```

**What this shows / what it does not.** The quiet gate released as decisive. The output has per-cell readings for sizes M2 to M20, both hands, at the locked K = 3, the "Falsifiability (D-14)" section, and the reference-K and variant-rule tables. For M18 (right and left hand) the output records "not falsifiable for size M18 (right, left hand): the escape clause fires", with every clearance from 0.05 to 0.2 excluded on both hands. Every cell heading carries "UNVERIFIED" beside its m. The block's effect on the verdict is not read here; the verdict is in the campaign entry below.


### 2026-10-08-a-container

Run window (UTC): 2026-10-08T23:30:33+00:00 (first gate reading) to 2026-10-09T01:11:06+00:00 (end reading). Platform: linux/amd64 under emulation (timings feed no bound).
HEAD `32cdeacce53cedc2fe3791d27104b599197f45e9`; protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`, protocol commit `fd40abc09947744b3e030446085e26a9e1a0c87f`.

Quiet gate: release: container run, non-decisive by construction (gate read at 2026-10-08T23:31:33+00:00). Gate readings: 3; first load1 1.36 read 2026-10-08T23:30:33+00:00; last load1 1.21 read 2026-10-08T23:31:33+00:00. Every reading is in the output below.
End reading: load1 1.67 read 2026-10-09T01:11:06+00:00 (it includes this run's own load).

Records: `bench/results/thread-spike/2026-10-08-a-container.jsonl` — 7161 lines, sha256 2b88dd843e05f97f0f992ca6a1abc8c1a0ab2bf01e49a8c818606b0d41a9be47. Markdown output: `bench/results/thread-spike/2026-10-08-a-container.md`.

Output verbatim:

```
## Thread spike run 2026-10-08-a-container

- Machine: 18 CPUs, arm64, 64.0 GiB RAM
- Python: 3.12.15
- Kernel: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1
- HEAD: `32cdeac`
- Protocol blob: `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e`
- Protocol commit: `fd40abc09947744b3e030446085e26a9e1a0c87f`
- Block: container
- K: 3 (selected by select_k from run 2026-10-08-a-ksweep)
- load1 1.36 read 2026-10-08T23:30:33+00:00
- load1 1.22 read 2026-10-08T23:31:03+00:00
- load1 1.21 read 2026-10-08T23:31:33+00:00
- Image: `screw:latest` sha256:7d992a89557b01bf2e35e0d368f8b68fd11e9c2774bbdfb45a26f1f7a31638f6 2026-10-08T16:52:13.591964824+06:00
- platform linux/amd64 under emulation on arm64: timings feed no bound
- release: container run, non-decisive by construction (gate read at 2026-10-08T23:31:33+00:00)

| Size | Rows | ok | silent_wrong | failure | timeout | worker_died | Max precise rel err | Max default rel err | Max fine triangles | Max fine bytes | Max raw + gzip-1 bytes | Max build + slower export s | Max STEP bytes | Checks skipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 240 | 240 | 0 | 0 | 0 | 0 | -8.147e-06 | -1.309e-05 | n/a | n/a | n/a | n/a | n/a | 0 |
| M2.5 | 312 | 312 | 0 | 0 | 0 | 0 | -7.586e-06 | -1.308e-05 | n/a | n/a | n/a | n/a | n/a | 0 |
| M3 | 240 | 240 | 0 | 0 | 0 | 0 | -7.301e-06 | -1.307e-05 | n/a | n/a | n/a | n/a | n/a | 0 |
| M3.5 | 328 | 328 | 0 | 0 | 0 | 0 | -6.920e-06 | -8.620e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M4 | 368 | 368 | 0 | 0 | 0 | 0 | -4.100e-06 | -8.805e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M5 | 400 | 400 | 0 | 0 | 0 | 0 | +1.708e-06 | -3.070e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M6 | 240 | 240 | 0 | 0 | 0 | 0 | +1.357e-06 | +1.806e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M7 | 280 | 280 | 0 | 0 | 0 | 0 | +1.299e-06 | +1.732e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M8 | 512 | 512 | 0 | 0 | 0 | 0 | +1.369e-06 | -2.572e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M10 | 532 | 532 | 0 | 0 | 0 | 0 | +1.232e-06 | -1.911e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M12 | 684 | 684 | 0 | 0 | 0 | 0 | +1.230e-06 | -2.311e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M14 | 560 | 560 | 0 | 0 | 0 | 0 | +1.020e-06 | -2.472e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M16 | 640 | 640 | 0 | 0 | 0 | 0 | +1.014e-06 | -2.491e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M18 | 864 | 864 | 0 | 0 | 0 | 0 | +1.019e-06 | -1.519e-06 | n/a | n/a | n/a | n/a | n/a | 0 |
| M20 | 960 | 960 | 0 | 0 | 0 | 0 | +1.014e-06 | -1.529e-06 | n/a | n/a | n/a | n/a | n/a | 0 |

### Container validity (D-05)

7160 rows in `screw:latest` under linux/amd64: ok 7160, silent_wrong 0, failure 0, timeout 0, worker_died 0.
Every timing in this run is emulation: validity, solid count and volume are the measurement, and a timing here feeds no bound (D-05).

- load1 1.67 read 2026-10-09T01:11:06+00:00 (includes this run's own load)
```

**What this shows / what it does not.** This block is non-decisive by construction: the output states it ran in `screw:latest` on linux/amd64 under emulation on arm64 and that its timings feed no bound. What it measures is validity: 7160 rows, ok 7160, silent_wrong 0, failure 0, timeout 0, worker_died 0 (the "Container validity (D-05)" section). It carries no triangle, byte or seconds figures (n/a columns), so it says nothing about the budgets.


### 2026-10-08-a-campaign

The campaign log, `bench/results/thread-spike/2026-10-08-a-campaign.md` (1088 lines), unedited, ending with the verdict output and "campaign finished". It is not a block run and has no JSONL; the blocks it reads are the nine entries above.

sha256 of the file: 5b061da655ea8951bf34ab7513a8442baa67f6e57c32b71284ade747bd6066c7.

Output verbatim:

```
## Thread spike campaign 2026-10-08-a

- ksweep: ran as `2026-10-08-a-ksweep`
- grid: ran as `2026-10-08-a-grid`
- frontier: ran as `2026-10-08-a-frontier`
- ladder: ran as `2026-10-08-a-ladder`
- trim: ran as `2026-10-08-a-trim`
- controls: ran as `2026-10-08-a-controls`
- rss: ran as `2026-10-08-a-rss`
- pair: ran as `2026-10-08-a-pair`
- container: ran as `2026-10-08-a-container`

## Thread spike verdict: campaign 2026-10-08-a

- Blocks read: ksweep (run `2026-10-08-a-ksweep`, non-decisive), grid (run `2026-10-08-a-grid`, non-decisive), frontier (run `2026-10-08-a-frontier`, non-decisive), ladder (run `2026-10-08-a-ladder`, decisive), pair (run `2026-10-08-a-pair`, decisive), container (run `2026-10-08-a-container`, non-decisive), controls (run `2026-10-08-a-controls`, decisive), trim (run `2026-10-08-a-trim`, decisive), rss (run `2026-10-08-a-rss`, decisive)

### K

selected K: 3 (select_k over run `2026-10-08-a-ksweep`)

| K | Rows | Non-ok rows | Fine triangles at the standard max | STEP bytes at the standard max | Qualifies |
|---|---|---|---|---|---|
| 3 | 64 | 0 | 17600302 | 59043400 | yes |
| 5 | 64 | 0 | 18245886 | 56721599 | yes |
| 10 | 64 | 0 | 20504224 | 54245913 | yes |

### Volume estimator

estimator: precise; max abs error 8.147e-06; T_gate 9e-05

### Pass bar

pass bar: held
- mesh checks skipped: 1025 of 7160 meshes unchecked (a skipped check is not a pass for its mesh)

### Escape clause

escape clause: FIRED
- pair: not falsifiable for size M18 (right, left hand)

### Turn caps

| Size | Construction cap (turns) | Construction stop | Bytes cap (mm) | Bytes cap (turns) | Seconds cap (mm) |
|---|---|---|---|---|---|
| M2 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M2.5 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M3 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M3.5 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M4 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M5 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M6 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M7 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M8 | 250 | left: no stop up to 250 turns | 67.5 | 54 | not established (non-decisive gate) |
| M10 | 250 | left: no stop up to 250 turns | 56 | 37.3333 | not established (non-decisive gate) |
| M12 | 250 | left: no stop up to 250 turns | 60 | 34.2857 | not established (non-decisive gate) |
| M14 | 250 | left: no stop up to 250 turns | 58 | 29 | not established (non-decisive gate) |
| M16 | 250 | left: no stop up to 250 turns | 52 | 26 | not established (non-decisive gate) |
| M18 | 250 | left: no stop up to 250 turns | 65 | 26 | not established (non-decisive gate) |
| M20 | 250 | left: no stop up to 250 turns | 64 | 25.6 | not established (non-decisive gate) |

- construction cap from run `2026-10-08-a-frontier`; bytes and seconds caps from run `2026-10-08-a-grid`
- M2: first row over the seconds budget: seconds not established (non-decisive gate)
- M2.5: first row over the seconds budget: seconds not established (non-decisive gate)
- M3: first row over the seconds budget: seconds not established (non-decisive gate)
- M3.5: first row over the seconds budget: seconds not established (non-decisive gate)
- M4: first row over the seconds budget: seconds not established (non-decisive gate)
- M5: first row over the seconds budget: seconds not established (non-decisive gate)
- M6: first row over the seconds budget: seconds not established (non-decisive gate)
- M7: first row over the seconds budget: seconds not established (non-decisive gate)
- M8: first row over the bytes budget: M8 right L=68 rod
- M8: first row over the seconds budget: seconds not established (non-decisive gate)
- M10: first row over the bytes budget: M10 right L=57 rod
- M10: first row over the seconds budget: seconds not established (non-decisive gate)
- M12: first row over the bytes budget: M12 right L=61 rod
- M12: first row over the seconds budget: seconds not established (non-decisive gate)
- M14: first row over the bytes budget: M14 right L=59 rod
- M14: first row over the seconds budget: seconds not established (non-decisive gate)
- M16: first row over the bytes budget: M16 right L=53 rod
- M16: first row over the seconds budget: seconds not established (non-decisive gate)
- M18: first row over the bytes budget: M18 right L=66 rod
- M18: first row over the seconds budget: seconds not established (non-decisive gate)
- M20: first row over the bytes budget: M20 right L=65 rod
- M20: first row over the seconds budget: seconds not established (non-decisive gate)

### Controls (D-06)

| Construction | Size | Length mm | Turns | Class | Solids | Valid | Precise ratio | Default ratio |
|---|---|---|---|---|---|---|---|---|
| naive sweep + fuse (negative control) | M2 | 4 | 10 | silent_wrong | 1 | yes | 0.290229 | 0.290298 |
| naive sweep + fuse (negative control) | M2 | 10 | 25 | silent_wrong | 1 | yes | 0.261206 | 0.261210 |
| naive sweep + fuse (negative control) | M2 | 20 | 50 | silent_wrong | 1 | yes | 0.251542 | 0.222915 |
| naive sweep + fuse (negative control) | M2.5 | 4.5 | 10 | silent_wrong | 1 | yes | 0.258961 | 0.259095 |
| naive sweep + fuse (negative control) | M2.5 | 10 | 22.2222 | silent_wrong | 1 | yes | 0.236871 | 0.236870 |
| naive sweep + fuse (negative control) | M2.5 | 20 | 44.4444 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M2.5 | 25 | 55.5556 | silent_wrong | 2 | yes | 1.035730 | 1.056853 |
| naive sweep + fuse (negative control) | M3 | 5 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M3 | 10 | 20 | silent_wrong | 1 | yes | 0.218512 | 0.218716 |
| naive sweep + fuse (negative control) | M3 | 20 | 40 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M3 | 30 | 60 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M6 | 10 | 10 | silent_wrong | 1 | yes | 0.238384 | 0.238232 |
| naive sweep + fuse (negative control) | M6 | 20 | 20 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M6 | 60 | 60 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 10 | 8 | silent_wrong | 1 | yes | 0.231722 | 0.231694 |
| naive sweep + fuse (negative control) | M8 | 12.5 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 20 | 16 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 80 | 64 | silent_wrong | 1 | yes | 0.191174 | 0.186273 |
| naive sweep + fuse (negative control) | M10 | 10 | 6.66667 | silent_wrong | 1 | yes | 0.230710 | 0.230710 |
| naive sweep + fuse (negative control) | M10 | 15 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M10 | 20 | 13.3333 | silent_wrong | 1 | yes | 1.026621 | 1.026622 |
| naive sweep + fuse (negative control) | M10 | 100 | 66.6667 | silent_wrong | 1 | yes | 0.182793 | 0.200653 |
| naive sweep + fuse (negative control) | M16 | 10 | 5 | silent_wrong | 1 | yes | 0.204723 | 0.204724 |
| naive sweep + fuse (negative control) | M16 | 20 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M16 | 160 | 80 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M20 | 10 | 4 | silent_wrong | 1 | yes | 0.219346 | 0.219347 |
| naive sweep + fuse (negative control) | M20 | 20 | 8 | silent_wrong | 1 | yes | 0.182789 | 0.182788 |
| naive sweep + fuse (negative control) | M20 | 25 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M20 | 200 | 80 | silent_wrong | 1 | yes | 0.149887 | 0.060069 |
| one-pipe twist | M2 | 20 | 50 | ok | 1 | yes | 0.999990 | 0.999021 |
| one-pipe twist | M2 | 40 | 100 | ok | 1 | yes | 0.999990 | 1.001131 |
| one-pipe twist | M2 | 64 | 160 | silent_wrong | 1 | yes | -1.000015 | -1.002367 |
| one-pipe twist | M2 | 80 | 200 | ok | 1 | yes | 0.999958 | 0.999035 |
| one-pipe twist | M2 | 100 | 250 | ok | 1 | yes | 0.999980 | 1.000803 |
| one-pipe twist | M2.5 | 25 | 55.5556 | ok | 1 | yes | 0.999996 | 1.000296 |
| one-pipe twist | M2.5 | 45 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M2.5 | 72 | 160 | silent_wrong | 1 | yes | -1.000008 | -1.002367 |
| one-pipe twist | M2.5 | 90 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M2.5 | 112.5 | 250 | ok | 1 | yes | 0.999994 | 0.999924 |
| one-pipe twist | M3 | 30 | 60 | ok | 1 | yes | 0.999984 | 1.000324 |
| one-pipe twist | M3 | 50 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M3 | 80 | 160 | silent_wrong | 1 | yes | -1.000007 | -1.002367 |
| one-pipe twist | M3 | 100 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M3 | 125 | 250 | ok | 1 | yes | 0.999993 | 0.999924 |
| one-pipe twist | M6 | 60 | 60 | ok | 1 | yes | 0.999994 | 0.999942 |
| one-pipe twist | M6 | 100 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M6 | 160 | 160 | silent_wrong | 1 | yes | -0.999995 | -1.001450 |
| one-pipe twist | M6 | 200 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M6 | 250 | 250 | ok | 1 | yes | 0.999993 | 0.999924 |
| one-pipe twist | M8 | 80 | 64 | ok | 1 | yes | 1.000010 | 0.999934 |
| one-pipe twist | M8 | 125 | 100 | ok | 1 | yes | 0.999998 | 1.000071 |
| one-pipe twist | M8 | 200 | 160 | silent_wrong | 1 | yes | -1.000006 | -0.999825 |
| one-pipe twist | M8 | 250 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M8 | 312.5 | 250 | ok | 1 | yes | 1.000000 | 0.999949 |
| one-pipe twist | M10 | 100 | 66.6667 | ok | 1 | yes | 1.000001 | 1.000171 |
| one-pipe twist | M10 | 150 | 100 | ok | 1 | yes | 0.999997 | 1.000064 |
| one-pipe twist | M10 | 240 | 160 | silent_wrong | 1 | yes | -1.000003 | -0.999897 |
| one-pipe twist | M10 | 300 | 200 | ok | 1 | yes | 0.999991 | 1.000156 |
| one-pipe twist | M10 | 375 | 250 | ok | 1 | yes | 1.000008 | 0.999949 |
| one-pipe twist | M16 | 160 | 80 | ok | 1 | yes | 0.999994 | 1.000130 |
| one-pipe twist | M16 | 200 | 100 | ok | 1 | yes | 0.999995 | 1.000055 |
| one-pipe twist | M16 | 320 | 160 | silent_wrong | 1 | yes | -1.000008 | -0.999897 |
| one-pipe twist | M16 | 400 | 200 | ok | 1 | yes | 0.999995 | 1.000114 |
| one-pipe twist | M16 | 500 | 250 | ok | 1 | yes | 0.999975 | 1.000072 |
| one-pipe twist | M20 | 200 | 80 | ok | 1 | yes | 0.999998 | 1.000013 |
| one-pipe twist | M20 | 250 | 100 | ok | 1 | yes | 0.999992 | 1.000014 |
| one-pipe twist | M20 | 400 | 160 | silent_wrong | 1 | yes | -0.999995 | -1.000023 |
| one-pipe twist | M20 | 500 | 200 | ok | 1 | yes | 0.999986 | 0.999853 |
| one-pipe twist | M20 | 625 | 250 | ok | 1 | yes | 0.999998 | 0.999993 |
| ruled-surface reference | M2 | 4 | 10 | silent_wrong | 1 | yes | 0.981297 | 0.874977 |
| ruled-surface reference | M2 | 20 | 50 | silent_wrong | 1 | yes | 0.995713 | 0.793632 |
| ruled-surface reference | M2.5 | 4.5 | 10 | silent_wrong | 1 | yes | 0.983412 | 0.876551 |
| ruled-surface reference | M2.5 | 25 | 55.5556 | silent_wrong | 1 | yes | 0.996569 | 1.015351 |
| ruled-surface reference | M3 | 5 | 10 | silent_wrong | 1 | yes | 0.984799 | 0.877611 |
| ruled-surface reference | M3 | 30 | 60 | silent_wrong | 1 | yes | 0.997092 | 0.623208 |
| ruled-surface reference | M6 | 10 | 10 | silent_wrong | 1 | yes | 0.985012 | 0.878017 |
| ruled-surface reference | M6 | 60 | 60 | silent_wrong | 1 | yes | 0.997312 | 0.595680 |
| ruled-surface reference | M8 | 12.5 | 10 | silent_wrong | 1 | yes | 0.986069 | 0.878869 |
| ruled-surface reference | M8 | 80 | 64 | silent_wrong | 1 | yes | 0.997679 | 0.976243 |
| ruled-surface reference | M10 | 15 | 10 | silent_wrong | 1 | yes | 0.986698 | 0.879391 |
| ruled-surface reference | M10 | 100 | 66.6667 | silent_wrong | 1 | yes | 0.997889 | 0.908570 |
| ruled-surface reference | M16 | 20 | 10 | silent_wrong | 1 | yes | 0.989094 | 0.881278 |
| ruled-surface reference | M16 | 160 | 80 | silent_wrong | 1 | yes | 0.998564 | 0.952563 |
| ruled-surface reference | M20 | 25 | 10 | silent_wrong | 1 | yes | 0.989110 | 0.881327 |
| ruled-surface reference | M20 | 200 | 80 | silent_wrong | 1 | yes | 0.998580 | 0.952577 |

Known-bad inputs for THRD-04 (naive rows with 1 solid, isValid True and a precise ratio below 0.5):
- naive_sweep_fuse(d=2.0, pitch=0.4, length=4.0): precise ratio 0.290229
- naive_sweep_fuse(d=2.0, pitch=0.4, length=10.0): precise ratio 0.261206
- naive_sweep_fuse(d=2.0, pitch=0.4, length=20.0): precise ratio 0.251542
- naive_sweep_fuse(d=2.5, pitch=0.45, length=4.5): precise ratio 0.258961
- naive_sweep_fuse(d=2.5, pitch=0.45, length=10.0): precise ratio 0.236871
- naive_sweep_fuse(d=3.0, pitch=0.5, length=10.0): precise ratio 0.218512
- naive_sweep_fuse(d=6.0, pitch=1.0, length=10.0): precise ratio 0.238384
- naive_sweep_fuse(d=8.0, pitch=1.25, length=10.0): precise ratio 0.231722
- naive_sweep_fuse(d=8.0, pitch=1.25, length=80.0): precise ratio 0.191174
- naive_sweep_fuse(d=10.0, pitch=1.5, length=10.0): precise ratio 0.230710
- naive_sweep_fuse(d=10.0, pitch=1.5, length=100.0): precise ratio 0.182793
- naive_sweep_fuse(d=16.0, pitch=2.0, length=10.0): precise ratio 0.204723
- naive_sweep_fuse(d=20.0, pitch=2.5, length=10.0): precise ratio 0.219346
- naive_sweep_fuse(d=20.0, pitch=2.5, length=20.0): precise ratio 0.182789
- naive_sweep_fuse(d=20.0, pitch=2.5, length=200.0): precise ratio 0.149887

The ruled-surface profile is not identical to the pinned profile, so its ratio to this closed form is not an accuracy claim.

### Tip trim cost (D-08)

| Size | Hand | Length mm | Class | Trim s | Request s (build + trim + slower export) | Fine triangles | STEP bytes |
|---|---|---|---|---|---|---|---|
| M2 | right | 20 | ok | 0.21 | 0.55 | 310660 | 2672684 |
| M2 | left | 20 | ok | 0.19 | 0.51 | 278332 | 2672228 |
| M2.5 | right | 25 | ok | 0.20 | 0.59 | 412682 | 2971967 |
| M2.5 | left | 25 | ok | 0.22 | 0.57 | 330746 | 3005466 |
| M3 | right | 30 | ok | 0.23 | 0.71 | 452446 | 3260380 |
| M3 | left | 30 | ok | 0.24 | 0.66 | 365390 | 3262870 |
| M3.5 | right | 35 | ok | 0.22 | 0.71 | 450624 | 3180075 |
| M3.5 | left | 35 | ok | 0.24 | 0.69 | 367860 | 3199718 |
| M4 | right | 40 | ok | 0.20 | 0.72 | 532590 | 3493913 |
| M4 | left | 40 | ok | 0.21 | 0.67 | 389820 | 3494580 |
| M5 | right | 50 | ok | 0.26 | 0.90 | 601758 | 3784631 |
| M5 | left | 50 | ok | 0.27 | 0.82 | 441464 | 3786540 |
| M6 | right | 60 | ok | 0.27 | 0.89 | 608308 | 3651443 |
| M6 | left | 60 | ok | 0.27 | 0.81 | 453904 | 3651209 |
| M7 | right | 70 | ok | 0.28 | 0.97 | 736190 | 4257790 |
| M7 | left | 70 | ok | 0.29 | 0.89 | 558460 | 4260863 |
| M8 | right | 80 | ok | 0.26 | 1.13 | 1072962 | 3933673 |
| M8 | left | 80 | ok | 0.27 | 1.05 | 873052 | 3935714 |
| M10 | right | 100 | ok | 0.28 | 1.56 | 1613994 | 3736332 |
| M10 | left | 100 | ok | 0.29 | 1.41 | 1247152 | 3715911 |
| M12 | right | 120 | ok | 0.31 | 1.89 | 1805228 | 4212788 |
| M12 | left | 120 | ok | 0.31 | 1.68 | 1427396 | 4234645 |
| M14 | right | 140 | ok | 0.30 | 2.25 | 2194088 | 4368959 |
| M14 | left | 140 | ok | 0.30 | 2.00 | 1634744 | 4374068 |
| M16 | right | 160 | ok | 0.36 | 2.71 | 2768418 | 4983558 |
| M16 | left | 160 | ok | 0.36 | 2.39 | 1951234 | 4970441 |
| M18 | right | 180 | ok | 0.36 | 2.40 | 2476444 | 4527783 |
| M18 | left | 180 | ok | 0.37 | 2.04 | 1778886 | 4535139 |
| M20 | right | 200 | ok | 0.36 | 2.67 | 2894830 | 5050734 |
| M20 | left | 200 | ok | 0.36 | 2.32 | 2014508 | 5043593 |

The cone angle is 30 degrees from the end face at the minor radius, UNVERIFIED (ISO 4753 is unread): these rows are cost evidence for Phase 4, not geometry truth, and never enter the pass bar.

### Peak RSS and the L19 gzip table

| Size | Hand | Preset | Turns | Length mm | Row | Peak RSS | Class |
|---|---|---|---|---|---|---|---|
| M2 | right | preview | 50 | 20 | standard max | 511.5 MiB (fresh child, this row only) | ok |
| M2 | right | fine | 50 | 20 | standard max | 865.7 MiB (fresh child, this row only) | ok |
| M2 | right | fine | 250 | 100 | frontier terminal | 1138.2 MiB (fresh child, this row only) | ok |
| M2 | left | preview | 50 | 20 | standard max | 509.1 MiB (fresh child, this row only) | ok |
| M2 | left | fine | 50 | 20 | standard max | 853.4 MiB (fresh child, this row only) | ok |
| M2 | left | fine | 250 | 100 | frontier terminal | 1113.8 MiB (fresh child, this row only) | ok |
| M2.5 | right | preview | 55.5556 | 25 | standard max | 515.5 MiB (fresh child, this row only) | ok |
| M2.5 | right | fine | 55.5556 | 25 | standard max | 943.0 MiB (fresh child, this row only) | ok |
| M2.5 | right | fine | 250 | 112.5 | frontier terminal | 1174.0 MiB (fresh child, this row only) | ok |
| M2.5 | left | preview | 55.5556 | 25 | standard max | 514.3 MiB (fresh child, this row only) | ok |
| M2.5 | left | fine | 55.5556 | 25 | standard max | 904.3 MiB (fresh child, this row only) | ok |
| M2.5 | left | fine | 250 | 112.5 | frontier terminal | 1158.1 MiB (fresh child, this row only) | ok |
| M3 | right | preview | 60 | 30 | standard max | 524.9 MiB (fresh child, this row only) | ok |
| M3 | right | fine | 60 | 30 | standard max | 1020.9 MiB (fresh child, this row only) | ok |
| M3 | right | fine | 250 | 125 | frontier terminal | 1256.8 MiB (fresh child, this row only) | ok |
| M3 | left | preview | 60 | 30 | standard max | 517.3 MiB (fresh child, this row only) | ok |
| M3 | left | fine | 60 | 30 | standard max | 1017.7 MiB (fresh child, this row only) | ok |
| M3 | left | fine | 250 | 125 | frontier terminal | 1179.0 MiB (fresh child, this row only) | ok |
| M3.5 | right | preview | 58.3333 | 35 | standard max | 525.8 MiB (fresh child, this row only) | ok |
| M3.5 | right | fine | 58.3333 | 35 | standard max | 1102.9 MiB (fresh child, this row only) | ok |
| M3.5 | right | fine | 250 | 150 | frontier terminal | 1248.4 MiB (fresh child, this row only) | ok |
| M3.5 | left | preview | 58.3333 | 35 | standard max | 520.5 MiB (fresh child, this row only) | ok |
| M3.5 | left | fine | 58.3333 | 35 | standard max | 1062.5 MiB (fresh child, this row only) | ok |
| M3.5 | left | fine | 250 | 150 | frontier terminal | 1231.3 MiB (fresh child, this row only) | ok |
| M4 | right | preview | 57.1429 | 40 | standard max | 529.2 MiB (fresh child, this row only) | ok |
| M4 | right | fine | 57.1429 | 40 | standard max | 1121.0 MiB (fresh child, this row only) | ok |
| M4 | right | fine | 250 | 175 | frontier terminal | 1367.9 MiB (fresh child, this row only) | ok |
| M4 | left | preview | 57.1429 | 40 | standard max | 525.1 MiB (fresh child, this row only) | ok |
| M4 | left | fine | 57.1429 | 40 | standard max | 1114.6 MiB (fresh child, this row only) | ok |
| M4 | left | fine | 250 | 175 | frontier terminal | 1246.5 MiB (fresh child, this row only) | ok |
| M5 | right | preview | 62.5 | 50 | standard max | 550.3 MiB (fresh child, this row only) | ok |
| M5 | right | fine | 62.5 | 50 | standard max | 1142.7 MiB (fresh child, this row only) | ok |
| M5 | right | fine | 250 | 200 | frontier terminal | 1392.6 MiB (fresh child, this row only) | ok |
| M5 | left | preview | 62.5 | 50 | standard max | 538.3 MiB (fresh child, this row only) | ok |
| M5 | left | fine | 62.5 | 50 | standard max | 1072.2 MiB (fresh child, this row only) | ok |
| M5 | left | fine | 250 | 200 | frontier terminal | 1226.2 MiB (fresh child, this row only) | ok |
| M6 | right | preview | 60 | 60 | standard max | 545.7 MiB (fresh child, this row only) | ok |
| M6 | right | fine | 60 | 60 | standard max | 1171.0 MiB (fresh child, this row only) | ok |
| M6 | right | fine | 250 | 250 | frontier terminal | 1387.2 MiB (fresh child, this row only) | ok |
| M6 | left | preview | 60 | 60 | standard max | 538.6 MiB (fresh child, this row only) | ok |
| M6 | left | fine | 60 | 60 | standard max | 1094.3 MiB (fresh child, this row only) | ok |
| M6 | left | fine | 250 | 250 | frontier terminal | 1310.8 MiB (fresh child, this row only) | ok |
| M7 | right | preview | 70 | 70 | standard max | 553.3 MiB (fresh child, this row only) | ok |
| M7 | right | fine | 70 | 70 | standard max | 1182.3 MiB (fresh child, this row only) | ok |
| M7 | right | fine | 250 | 250 | frontier terminal | 1430.1 MiB (fresh child, this row only) | ok |
| M7 | left | preview | 70 | 70 | standard max | 545.2 MiB (fresh child, this row only) | ok |
| M7 | left | fine | 70 | 70 | standard max | 1141.1 MiB (fresh child, this row only) | ok |
| M7 | left | fine | 250 | 250 | frontier terminal | 1278.3 MiB (fresh child, this row only) | ok |
| M8 | right | preview | 64 | 80 | standard max | 560.0 MiB (fresh child, this row only) | ok |
| M8 | right | fine | 64 | 80 | standard max | 1305.7 MiB (fresh child, this row only) | ok |
| M8 | right | fine | 250 | 312.5 | frontier terminal | 1769.9 MiB (fresh child, this row only) | ok |
| M8 | left | preview | 64 | 80 | standard max | 550.6 MiB (fresh child, this row only) | ok |
| M8 | left | fine | 64 | 80 | standard max | 1239.5 MiB (fresh child, this row only) | ok |
| M8 | left | fine | 250 | 312.5 | frontier terminal | 1608.6 MiB (fresh child, this row only) | ok |
| M10 | right | preview | 66.6667 | 100 | standard max | 560.2 MiB (fresh child, this row only) | ok |
| M10 | right | fine | 66.6667 | 100 | standard max | 1463.4 MiB (fresh child, this row only) | ok |
| M10 | right | fine | 250 | 375 | frontier terminal | 2267.5 MiB (fresh child, this row only) | ok |
| M10 | left | preview | 66.6667 | 100 | standard max | 554.0 MiB (fresh child, this row only) | ok |
| M10 | left | fine | 66.6667 | 100 | standard max | 1407.6 MiB (fresh child, this row only) | ok |
| M10 | left | fine | 250 | 375 | frontier terminal | 1885.2 MiB (fresh child, this row only) | ok |
| M12 | right | preview | 68.5714 | 120 | standard max | 567.9 MiB (fresh child, this row only) | ok |
| M12 | right | fine | 68.5714 | 120 | standard max | 1688.5 MiB (fresh child, this row only) | ok |
| M12 | right | fine | 250 | 437.5 | frontier terminal | 2392.9 MiB (fresh child, this row only) | ok |
| M12 | left | preview | 68.5714 | 120 | standard max | 558.7 MiB (fresh child, this row only) | ok |
| M12 | left | fine | 68.5714 | 120 | standard max | 1602.6 MiB (fresh child, this row only) | ok |
| M12 | left | fine | 250 | 437.5 | frontier terminal | 2112.9 MiB (fresh child, this row only) | ok |
| M14 | right | preview | 70 | 140 | standard max | 581.5 MiB (fresh child, this row only) | ok |
| M14 | right | fine | 70 | 140 | standard max | 1872.4 MiB (fresh child, this row only) | ok |
| M14 | right | fine | 250 | 500 | frontier terminal | 2610.5 MiB (fresh child, this row only) | ok |
| M14 | left | preview | 70 | 140 | standard max | 571.0 MiB (fresh child, this row only) | ok |
| M14 | left | fine | 70 | 140 | standard max | 1748.7 MiB (fresh child, this row only) | ok |
| M14 | left | fine | 250 | 500 | frontier terminal | 2264.2 MiB (fresh child, this row only) | ok |
| M16 | right | preview | 80 | 160 | standard max | 643.0 MiB (fresh child, this row only) | ok |
| M16 | right | fine | 80 | 160 | standard max | 1916.6 MiB (fresh child, this row only) | ok |
| M16 | right | fine | 250 | 500 | frontier terminal | 2730.9 MiB (fresh child, this row only) | ok |
| M16 | left | preview | 80 | 160 | standard max | 639.8 MiB (fresh child, this row only) | ok |
| M16 | left | fine | 80 | 160 | standard max | 1784.3 MiB (fresh child, this row only) | ok |
| M16 | left | fine | 250 | 500 | frontier terminal | 2281.6 MiB (fresh child, this row only) | ok |
| M18 | right | preview | 72 | 180 | standard max | 673.5 MiB (fresh child, this row only) | ok |
| M18 | right | fine | 72 | 180 | standard max | 1795.1 MiB (fresh child, this row only) | ok |
| M18 | right | fine | 250 | 625 | frontier terminal | 2741.7 MiB (fresh child, this row only) | ok |
| M18 | left | preview | 72 | 180 | standard max | 676.5 MiB (fresh child, this row only) | ok |
| M18 | left | fine | 72 | 180 | standard max | 1651.4 MiB (fresh child, this row only) | ok |
| M18 | left | fine | 250 | 625 | frontier terminal | 2329.5 MiB (fresh child, this row only) | ok |
| M20 | right | preview | 80 | 200 | standard max | 711.0 MiB (fresh child, this row only) | ok |
| M20 | right | fine | 80 | 200 | standard max | 1854.9 MiB (fresh child, this row only) | ok |
| M20 | right | fine | 250 | 625 | frontier terminal | 2804.6 MiB (fresh child, this row only) | ok |
| M20 | left | preview | 80 | 200 | standard max | 682.4 MiB (fresh child, this row only) | ok |
| M20 | left | fine | 80 | 200 | standard max | 1785.3 MiB (fresh child, this row only) | ok |
| M20 | left | fine | 250 | 625 | frontier terminal | 2291.8 MiB (fresh child, this row only) | ok |

L19 gzip table (levels 1, 6 and 9 on the row's own STL, fresh child):

| Size | Level | Output bytes | Single-threaded median ms | 10-concurrent wall median ms |
|---|---|---|---|---|
| M2 | 1 | 7024461 | 101.7 | 122.6 |
| M2 | 6 | 6752985 | 183.6 | 222.1 |
| M2 | 9 | 6754143 | 206.7 | 254.4 |
| M2.5 | 1 | 9639781 | 143.4 | 169.0 |
| M2.5 | 6 | 9219593 | 242.3 | 293.5 |
| M2.5 | 9 | 9220536 | 264.4 | 323.7 |
| M3 | 1 | 10634274 | 160.2 | 186.7 |
| M3 | 6 | 10139845 | 288.7 | 353.4 |
| M3 | 9 | 10140314 | 329.3 | 403.5 |
| M3.5 | 1 | 10583521 | 162.1 | 186.8 |
| M3.5 | 6 | 10147763 | 275.7 | 330.1 |
| M3.5 | 9 | 10148944 | 300.0 | 360.2 |
| M4 | 1 | 12356444 | 189.8 | 218.2 |
| M4 | 6 | 11848427 | 323.9 | 381.7 |
| M4 | 9 | 11850333 | 348.5 | 413.0 |
| M5 | 1 | 13850880 | 210.1 | 240.3 |
| M5 | 6 | 13246686 | 364.3 | 426.0 |
| M5 | 9 | 13248972 | 397.4 | 467.7 |
| M6 | 1 | 13970930 | 211.8 | 242.4 |
| M6 | 6 | 13360183 | 374.0 | 436.5 |
| M6 | 9 | 13361643 | 417.4 | 490.4 |
| M7 | 1 | 17249144 | 260.4 | 297.4 |
| M7 | 6 | 16505179 | 459.8 | 539.1 |
| M7 | 9 | 16507342 | 521.9 | 618.4 |
| M8 | 1 | 25818148 | 387.9 | 447.9 |
| M8 | 6 | 24831288 | 652.8 | 766.7 |
| M8 | 9 | 24834915 | 721.2 | 847.9 |
| M10 | 1 | 37691313 | 563.3 | 649.6 |
| M10 | 6 | 35970130 | 1019.6 | 1191.7 |
| M10 | 9 | 35975052 | 1111.5 | 1298.9 |
| M12 | 1 | 42084822 | 632.5 | 733.0 |
| M12 | 6 | 40259958 | 1142.4 | 1335.4 |
| M12 | 9 | 40262125 | 1221.5 | 1438.2 |
| M14 | 1 | 50611949 | 765.1 | 885.9 |
| M14 | 6 | 48446123 | 1434.1 | 1684.6 |
| M14 | 9 | 48447578 | 1580.8 | 1877.8 |
| M16 | 1 | 62726041 | 942.2 | 1104.9 |
| M16 | 6 | 60072616 | 1795.3 | 2111.0 |
| M16 | 9 | 60071266 | 1985.2 | 2338.3 |
| M18 | 1 | 56785836 | 847.5 | 998.2 |
| M18 | 6 | 54535211 | 1533.7 | 1803.9 |
| M18 | 9 | 54539361 | 1646.8 | 1942.5 |
| M20 | 1 | 66190237 | 982.5 | 1161.8 |
| M20 | 6 | 63558367 | 1751.3 | 2064.0 |
| M20 | 9 | 63562242 | 1873.8 | 2198.8 |

- M2: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M2.5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M3: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M3.5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M4: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M6: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M7: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M8: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M10: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M12: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M14: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M16: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M18: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M20: selected gzip level 1 (spur L19's rule, `select_gzip_level`)

### Container validity (D-05)

7160 rows in `screw:latest` under linux/amd64: ok 7160, silent_wrong 0, failure 0, timeout 0, worker_died 0.
Every timing in this run is emulation: validity, solid count and volume are the measurement, and a timing here feeds no bound (D-05).

### Pair check (D-11 to D-14)

Locked K = 3; every cell below is read at it. A cell is proven only if all 3 matched poses read empty (<= 1e-06 mm3) and all 3 controls read within 0.001 of the closed form (D-12, D-14).

#### M2 right hand (m = 1.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.428872/0.428877/0.428872 | 0.859203/0.859202/0.859203 | 0.859202 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0.647798/0/0.647798 | 0.647802 | 0/0/0 ; 1/0/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.455395/0.455395/0.455396 | 0.455399 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.284711/0 | 0.284715 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.138463/0.138464/0.138464 | 0.138468 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0/0.0244833/0 | 0.0244813 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M2 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.284715 mm3); control at theta +2.0944 reads empty (closed form 0.284715 mm3)
- M2 right c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 0.0244813 mm3); control at theta +2.0944 reads empty (closed form 0.0244813 mm3)

#### M2 left hand (m = 1.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.428872/0.428877/0.428872 | 0.859203/0.859202/0.859202 | 0.859202 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0.647798/0/0.647797 | 0.647802 | 0/0/0 ; 1/0/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.455396/0.455395/0.455395 | 0.455399 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.284711/0 | 0.284715 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.138464/0.138464/0.138463 | 0.138468 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0/0.0244833/0 | 0.0244813 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M2 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.284715 mm3); control at theta +2.0944 reads empty (closed form 0.284715 mm3)
- M2 left c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 0.0244813 mm3); control at theta +2.0944 reads empty (closed form 0.0244813 mm3)

#### M2.5 right hand (m = 2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.683622/0.6836/0.683576 | 1.49169/1.49171/1.49169 | 1.49169 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.15397/1.15398/1.15397 | 1.15397 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.845031/0.845045/0.845032 | 0.845035 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.567913/0 | 0.567908 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.325602/0.325609/0.325603 | 0.325612 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.121421/0.121424/0.121422 | 0.121426 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M2.5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2.5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2.5 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.567908 mm3); control at theta +2.0944 reads empty (closed form 0.567908 mm3)

#### M2.5 left hand (m = 2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.683576/0.6836/0.683622 | 1.49169/1.49171/1.49168 | 1.49169 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.15397/1.15399/1.15397 | 1.15397 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.845034/0.845046/0.84503 | 0.845035 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.567914/0 | 0.567908 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.325603/0.32561/0.325601 | 0.325612 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.121421/0.121424/0.12142 | 0.121426 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M2.5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2.5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2.5 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.567908 mm3); control at theta +2.0944 reads empty (closed form 0.567908 mm3)

#### M3 right hand (m = 2.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.997365/0.99734/0.997269 | 0/2.35538/2.35539 | 2.35543 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.86255/1.86258/1.86258 | 1.86262 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/1.40915/1.40915 | 1.4092 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0.998331/0.998359/0.99836 | 0.998409 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 0/0.633481/0 | 0.633531 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0.317787/0.317808/0.317809 | 0.317827 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M3 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 1.4092 mm3)
- M3 right c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 0.633531 mm3); control at theta +2.0944 reads empty (closed form 0.633531 mm3)

#### M3 left hand (m = 2.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.997269/0.99734/0.997365 | 2.35539/2.35538/0 | 2.35543 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.86258/1.86258/1.86255 | 1.86262 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 1.40915/1.40915/0 | 1.4092 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0.998359/0.998359/0.99833 | 0.998409 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 0/0.633481/0 | 0.633531 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0.317809/0.317808/0.317787 | 0.317827 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M3 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 1.4092 mm3)
- M3 left c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 0.633531 mm3); control at theta +2.0944 reads empty (closed form 0.633531 mm3)

#### M3.5 right hand (m = 2.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.35671/1.3567/1.3567 | 3.69532/3.69532/3.69531 | 3.69532 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 3.0328/3.03279/3.03279 | 3.0328 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 2.4141/2.4141/2.4141 | 2.4141 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 1.84241/1.8424/1.8424 | 1.8424 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 1.32088/1.32088/1.32088 | 1.32088 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.852706/0.852705/0.852704 | 0.852709 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3.5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3.5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M3.5 left hand (m = 2.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.3567/1.3567/1.35671 | 3.69531/3.69531/3.69532 | 3.69532 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000633645/0/0 | 3.03279/3.03279/3.0328 | 3.0328 | 25/0/0 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 2.4141/2.4141/2.4141 | 2.4141 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 1.8424/1.8424/1.84241 | 1.8424 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 1.32088/1.32088/1.32088 | 1.32088 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.852704/0.852704/0.852707 | 0.852709 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3.5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3.5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M4 right hand (m = 3.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.77124/1.77123/1.77123 | 5.46813/5.46812/5.46812 | 5.46812 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 5.79139e-06/0/-0.00279567 | 4.61056/4.61056/4.61056 | 4.61055 | 4/0/12 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/3.80135/3.80135 | 3.80135 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 3.04361/3.04361/3.04361 | 3.04361 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 2.34045/2.34045/2.34045 | 2.34044 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 1.69497/1.69497/1.69497 | 1.69497 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M4 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M4 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M4 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 3.80135 mm3)

#### M4 left hand (m = 3.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.77123/1.77123/1.77124 | 5.46812/5.46812/5.46812 | 5.46812 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0910952/0/-0.00132387 | 4.61056/4.61056/4.61056 | 4.61055 | 10/0/12 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 3.80135/3.80135/0 | 3.80135 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 3.04361/3.04361/3.04361 | 3.04361 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 2.34045/2.34045/2.34045 | 2.34044 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 1.69497/1.69497/1.69497 | 1.69497 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M4 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M4 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M4 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 3.80135 mm3)

#### M5 right hand (m = 4.7 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 3.29489/3.29482/3.29482 | 11.3681/11.3681/11.3681 | 11.3681 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -2.1969e-06/0/-0.0184956 | 9.76954/9.76954/9.76954 | 9.76953 | 5/0/15 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 8.25346/8.25346/0 | 8.25345 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 6.82381/6.82382/6.82381 | 6.8238 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 5.4846/5.48461/5.48461 | 5.4846 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 4.23983/4.23983/4.23983 | 4.23982 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M5 right c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 8.25345 mm3)

#### M5 left hand (m = 4.7 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 3.29482/3.29482/3.29489 | 11.3681/11.3681/11.3681 | 11.3681 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00240809/0/0.00325241 | 9.76954/9.76954/9.76954 | 9.76953 | 17/0/11 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/8.25346/8.25346 | 8.25345 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 6.82381/6.82381/6.82381 | 6.8238 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 5.48461/5.4846/5.4846 | 5.4846 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 4.23983/4.23983/4.23983 | 4.23982 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M5 left c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 8.25345 mm3)

#### M6 right hand (m = 5.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 4.36276/4.36266/4.36271 | 18.2374/18.2374/18.2373 | 18.2374 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00177739/0/-0.00603191 | 16.1428/16.1428/16.1427 | 16.1427 | 13/0/7 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 14.1335/14.1335/14.1334 | 14.1335 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 12.213/12.213/12.213 | 12.213 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 10.385/10.385/10.3849 | 10.385 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 8.65294/8.65294/8.65289 | 8.65288 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M6 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M6 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M6 left hand (m = 5.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 4.36271/4.36266/4.36276 | 18.2373/18.2374/18.2374 | 18.2374 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.00513391/0/-0.0115552 | 16.1427/16.1428/16.1428 | 16.1427 | 9/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 14.1334/14.1335/14.1335 | 14.1335 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 12.213/12.213/12.213 | 12.213 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 10.3849/10.385/10.385 | 10.385 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 8.65289/8.65294/8.65294 | 8.65288 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M6 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M6 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M7 right hand (m = 5.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 5.57807/5.5779/5.57786 | 23.3066/23.3066/23.3066 | 23.3066 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.319506/0/-0.492389 | 20.5983/20.5983/20.5983 | 20.5983 | 11/0/14 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/18.0073/18.0073 | 18.0073 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 15.5375/15.5374/15.5374 | 15.5375 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 13.1925/13.1924/13.1925 | 13.1925 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 10.9762/10.9761/10.9762 | 10.9762 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M7 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M7 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M7 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 18.0073 mm3)

#### M7 left hand (m = 5.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 5.57786/5.5779/5.57807 | 23.3066/23.3066/23.3066 | 23.3066 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.453107/0/-0.00801368 | 20.5983/20.5983/20.5983 | 20.5983 | 19/0/8 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 18.0073/18.0073/0 | 18.0073 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 15.5374/15.5375/15.5374 | 15.5375 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 13.1925/13.1925/13.1925 | 13.1925 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 10.9762/10.9762/10.9762 | 10.9762 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M7 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M7 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M7 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 18.0073 mm3)

#### M8 right hand (m = 6.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 7.67898/7.6787/7.67872 | 39.1066/39.1066/0 | 39.1065 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.00082956/0/0.00415998 | 35.4231/35.4231/35.4231 | 35.423 | 12/0/9 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 31.8635/31.8635/31.8635 | 31.8635 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 28.4315/28.4315/28.4315 | 28.4315 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 25.1309/25.1309/25.1309 | 25.1308 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 21.9652/21.9652/21.9652 | 21.9652 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M8 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M8 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M8 left hand (m = 6.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 7.67872/7.6787/7.67898 | 0/39.1065/39.1066 | 39.1065 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0393199/0/0.00759806 | 35.4231/35.4231/35.4231 | 35.423 | 11/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 31.8635/31.8635/31.8635 | 31.8635 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 28.4315/28.4315/28.4315 | 28.4315 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 25.1308/25.1308/25.1308 | 25.1308 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 21.9652/21.9652/21.9652 | 21.9652 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M8 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M8 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M10 right hand (m = 8.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 11.9241/11.9235/11.923 | 71.6178/71.6178/71.6181 | 71.618 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000873794/0/0.00116949 | 65.9036/65.9037/65.9039 | 65.9038 | 7/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/60.3527/60.353 | 60.3528 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0/54.9688/54.9691 | 54.9689 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 49.7557/49.7557/49.756 | 49.7558 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 44.7172/44.7173/44.7175 | 44.7174 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M10 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M10 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M10 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 60.3528 mm3)
- M10 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 54.9689 mm3)

#### M10 left hand (m = 8.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 11.923/11.9235/11.9241 | 71.6181/71.6179/71.6178 | 71.618 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0225569/0/0.00510398 | 65.9039/65.9037/65.9036 | 65.9038 | 9/0/11 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 60.353/60.3528/0 | 60.3528 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 54.969/54.9688/0 | 54.9689 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 49.756/49.7558/49.7556 | 49.7558 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 44.7175/44.7173/44.7172 | 44.7174 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M10 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M10 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M10 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 60.3528 mm3)
- M10 left c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 54.9689 mm3)

#### M12 right hand (m = 10.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 18.4657/18.4649/18.465 | 127.789/127.789/127.789 | 127.789 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00778178/0/0.0176886 | 118.947/118.947/0 | 118.947 | 8/0/8 ; 1/1/0 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 110.325/110.325/0 | 110.325 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 101.926/101.926/101.926 | 101.926 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 93.7549/93.7551/93.755 | 93.7548 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 85.8153/85.8155/85.8155 | 85.8153 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M12 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M12 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M12 right c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 110.325 mm3)

#### M12 left hand (m = 10.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 18.465/18.4649/18.4657 | 127.789/127.789/127.789 | 127.789 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0593007/0/-0.0279531 | 0/118.947/118.947 | 118.947 | 13/0/11 ; 0/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/110.325/110.325 | 110.325 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 101.926/101.926/101.926 | 101.926 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 93.7549/93.7549/93.7548 | 93.7548 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 85.8154/85.8154/85.8153 | 85.8153 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M12 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M12 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M12 left c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 110.325 mm3)

#### M14 right hand (m = 12.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 25.6006/25.5995/25.6008 | 200.577/200.576/200.576 | 200.576 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000104004/0/-9.33039e-05 | 188.328/188.328/188.327 | 188.328 | 6/0/6 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 176.348/176.347/176.346 | 176.347 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 164.639/164.639/0 | 164.639 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 153.208/153.207/153.207 | 153.207 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 142.057/142.057/142.056 | 142.057 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M14 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M14 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M14 right c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 164.639 mm3)

#### M14 left hand (m = 12.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 25.6008/25.5995/25.6006 | 200.576/200.576/200.577 | 200.576 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0249251/0/-0.0240166 | 188.327/188.328/188.328 | 188.328 | 10/0/8 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 176.346/176.347/176.347 | 176.347 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/164.639/164.639 | 164.639 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 153.207/153.207/153.208 | 153.207 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 142.056/142.057/142.057 | 142.057 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M14 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M14 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M14 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 164.639 mm3)

#### M16 right hand (m = 14.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 34.249/34.249/34.2488 | 268.248/268.248/268.248 | 268.249 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 251.727/251.727/251.727 | 251.728 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 235.584/235.583/235.583 | 235.585 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 219.822/219.822/219.822 | 219.823 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 204.447/204.447/204.447 | 204.448 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 189.465/189.464/189.464 | 189.466 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M16 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M16 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M16 left hand (m = 14.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 34.2488/34.249/34.249 | 268.248/268.248/268.248 | 268.249 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 251.727/251.727/251.727 | 251.728 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 235.583/235.583/235.584 | 235.585 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 219.822/219.822/219.822 | 219.823 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 204.447/204.447/204.447 | 204.448 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 189.464/189.464/189.465 | 189.466 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M16 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M16 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M18 right hand (m = 15.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 40.7729/40.7719/40.7716 | 0/394.049/394.049 | 394.05 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0/374.563/374.562 | 374.564 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/355.422/355.421 | 355.423 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0/336.63/336.63 | 336.632 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0/318.193/318.193 | 318.194 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0/300.113/300.113 | 300.115 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M18 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M18 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M18 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 355.423 mm3)
- M18 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 336.632 mm3)
- M18 right c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 318.194 mm3)
- M18 right c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 300.115 mm3)

#### M18 left hand (m = 15.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 40.7716/40.7719/40.7729 | 394.049/394.049/0 | 394.05 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 374.562/374.562/0 | 374.564 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 355.421/355.421/0 | 355.423 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 336.63/336.63/0 | 336.632 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 318.192/318.193/0 | 318.194 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 300.113/300.113/0 | 300.115 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M18 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M18 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M18 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 355.423 mm3)
- M18 left c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 336.632 mm3)
- M18 left c=0.15: inconclusive: control at theta +2.0944 reads empty (closed form 318.194 mm3)
- M18 left c=0.2: inconclusive: control at theta +2.0944 reads empty (closed form 300.115 mm3)

#### M20 right hand (m = 18 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 52.1062/52.1031/52.1072 | 503.428/503.428/503.429 | 503.429 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 478.369/478.369/478.37 | 478.369 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 453.768/453.768/453.769 | 453.768 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 429.63/429.63/429.632 | 429.631 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 405.961/405.962/405.963 | 405.962 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 382.766/382.766/382.767 | 382.766 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M20 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M20 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M20 left hand (m = 18 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 52.1072/52.1031/52.1062 | 503.429/503.428/503.428 | 503.429 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 478.37/478.368/478.368 | 478.369 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 453.769/453.768/453.768 | 453.768 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 429.631/429.63/429.63 | 429.631 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 405.963/405.961/405.961 | 405.962 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 382.767/382.766/382.766 | 382.766 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M20 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M20 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### Falsifiability (D-14)

- M2: falsifiable on both hands
- M2 right: excluded clearances 0.1, 0.2
- M2 left: excluded clearances 0.1, 0.2
- M2: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M2 right: sensitivity (c = -0.05) ok
- M2 left: sensitivity (c = -0.05) ok
- M2.5: falsifiable on both hands
- M2.5 right: excluded clearances 0.1
- M2.5 left: excluded clearances 0.1
- M2.5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M2.5 right: sensitivity (c = -0.05) ok
- M2.5 left: sensitivity (c = -0.05) ok
- M3: falsifiable on both hands
- M3 right: excluded clearances 0.05, 0.15
- M3 left: excluded clearances 0.05, 0.15
- M3: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M3 right: sensitivity (c = -0.05) ok
- M3 left: sensitivity (c = -0.05) ok
- M3.5: falsifiable on both hands
- M3.5 right: excluded clearances none
- M3.5 left: excluded clearances none
- M3.5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M3.5 right: sensitivity (c = -0.05) ok
- M3.5 left: sensitivity (c = -0.05) ok
- M4: falsifiable on both hands
- M4 right: excluded clearances 0.05
- M4 left: excluded clearances 0.05
- M4: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M4 right: sensitivity (c = -0.05) ok
- M4 left: sensitivity (c = -0.05) ok
- M5: falsifiable on both hands
- M5 right: excluded clearances 0.05
- M5 left: excluded clearances 0.05
- M5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M5 right: sensitivity (c = -0.05) ok
- M5 left: sensitivity (c = -0.05) ok
- M6: falsifiable on both hands
- M6 right: excluded clearances none
- M6 left: excluded clearances none
- M6: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M6 right: sensitivity (c = -0.05) ok
- M6 left: sensitivity (c = -0.05) ok
- M7: falsifiable on both hands
- M7 right: excluded clearances 0.05
- M7 left: excluded clearances 0.05
- M7: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M7 right: sensitivity (c = -0.05) ok
- M7 left: sensitivity (c = -0.05) ok
- M8: falsifiable on both hands
- M8 right: excluded clearances none
- M8 left: excluded clearances none
- M8: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M8 right: sensitivity (c = -0.05) ok
- M8 left: sensitivity (c = -0.05) ok
- M10: falsifiable on both hands
- M10 right: excluded clearances 0.05, 0.1
- M10 left: excluded clearances 0.05, 0.1
- M10: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M10 right: sensitivity (c = -0.05) ok
- M10 left: sensitivity (c = -0.05) ok
- M12: falsifiable on both hands
- M12 right: excluded clearances 0.05
- M12 left: excluded clearances 0.05
- M12: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M12 right: sensitivity (c = -0.05) ok
- M12 left: sensitivity (c = -0.05) ok
- M14: falsifiable on both hands
- M14 right: excluded clearances 0.1
- M14 left: excluded clearances 0.1
- M14: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M14 right: sensitivity (c = -0.05) ok
- M14 left: sensitivity (c = -0.05) ok
- M16: falsifiable on both hands
- M16 right: excluded clearances none
- M16 left: excluded clearances none
- M16: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M16 right: sensitivity (c = -0.05) ok
- M16 left: sensitivity (c = -0.05) ok
- not falsifiable for size M18 (right, left hand): the escape clause fires
- M18 right: excluded clearances 0.05, 0.1, 0.15, 0.2
- M18 left: excluded clearances 0.05, 0.1, 0.15, 0.2
- M18: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M18 right: sensitivity (c = -0.05) ok
- M18 left: sensitivity (c = -0.05) ok
- M20: falsifiable on both hands
- M20 right: excluded clearances none
- M20 left: excluded clearances none
- M20: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M20 right: sensitivity (c = -0.05) ok
- M20 left: sensitivity (c = -0.05) ok

#### Reference K (reported, not verdict inputs)

| Size | K | c = 0.05 | c = 0.1 | c = 0.15 | c = 0.2 |
|---|---|---|---|---|---|
| M2 | 5 | inconclusive | inconclusive | inconclusive | inconclusive |
| M2 | 10 | proven | inconclusive | inconclusive | inconclusive |
| M6 | 5 | inconclusive | inconclusive | inconclusive | inconclusive |
| M6 | 10 | proven | inconclusive | inconclusive | inconclusive |
| M10 | 5 | inconclusive | proven | proven | proven |
| M10 | 10 | inconclusive | inconclusive | inconclusive | inconclusive |
| M20 | 5 | proven | proven | proven | inconclusive |
| M20 | 10 | inconclusive | inconclusive | inconclusive | inconclusive |

#### Variant rules (reported, never the verdict)

Computed from the same recorded readings. The D-14 column is the verdict; the others are for Phase 5's revision and never feed it (owner ruling R1).

| Cell | D-14 verdict | two of three controls fire in band | seam pose excluded | same-pose c=-0.05 reading as the control |
|---|---|---|---|---|
| M2 right c=0.05 K=3 | proven | yes | yes | yes |
| M2 right c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2 right c=0.15 K=3 | proven | yes | yes | yes |
| M2 right c=0.2 K=3 | inconclusive | NO | NO | yes |
| M2 left c=0.05 K=3 | proven | yes | yes | yes |
| M2 left c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2 left c=0.15 K=3 | proven | yes | yes | yes |
| M2 left c=0.2 K=3 | inconclusive | NO | NO | yes |
| M2.5 right c=0.05 K=3 | proven | yes | yes | yes |
| M2.5 right c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2.5 right c=0.15 K=3 | proven | yes | yes | yes |
| M2.5 right c=0.2 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.05 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2.5 left c=0.15 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.2 K=3 | proven | yes | yes | yes |
| M3 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M3 right c=0.1 K=3 | proven | yes | yes | yes |
| M3 right c=0.15 K=3 | inconclusive | NO | NO | yes |
| M3 right c=0.2 K=3 | proven | yes | yes | yes |
| M3 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M3 left c=0.1 K=3 | proven | yes | yes | yes |
| M3 left c=0.15 K=3 | inconclusive | NO | NO | yes |
| M3 left c=0.2 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.05 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.1 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.15 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.2 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.05 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.1 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.15 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.2 K=3 | proven | yes | yes | yes |
| M4 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M4 right c=0.1 K=3 | proven | yes | yes | yes |
| M4 right c=0.15 K=3 | proven | yes | yes | yes |
| M4 right c=0.2 K=3 | proven | yes | yes | yes |
| M4 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M4 left c=0.1 K=3 | proven | yes | yes | yes |
| M4 left c=0.15 K=3 | proven | yes | yes | yes |
| M4 left c=0.2 K=3 | proven | yes | yes | yes |
| M5 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M5 right c=0.1 K=3 | proven | yes | yes | yes |
| M5 right c=0.15 K=3 | proven | yes | yes | yes |
| M5 right c=0.2 K=3 | proven | yes | yes | yes |
| M5 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M5 left c=0.1 K=3 | proven | yes | yes | yes |
| M5 left c=0.15 K=3 | proven | yes | yes | yes |
| M5 left c=0.2 K=3 | proven | yes | yes | yes |
| M6 right c=0.05 K=3 | proven | yes | yes | yes |
| M6 right c=0.1 K=3 | proven | yes | yes | yes |
| M6 right c=0.15 K=3 | proven | yes | yes | yes |
| M6 right c=0.2 K=3 | proven | yes | yes | yes |
| M6 left c=0.05 K=3 | proven | yes | yes | yes |
| M6 left c=0.1 K=3 | proven | yes | yes | yes |
| M6 left c=0.15 K=3 | proven | yes | yes | yes |
| M6 left c=0.2 K=3 | proven | yes | yes | yes |
| M7 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M7 right c=0.1 K=3 | proven | yes | yes | yes |
| M7 right c=0.15 K=3 | proven | yes | yes | yes |
| M7 right c=0.2 K=3 | proven | yes | yes | yes |
| M7 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M7 left c=0.1 K=3 | proven | yes | yes | yes |
| M7 left c=0.15 K=3 | proven | yes | yes | yes |
| M7 left c=0.2 K=3 | proven | yes | yes | yes |
| M8 right c=0.05 K=3 | proven | yes | yes | yes |
| M8 right c=0.1 K=3 | proven | yes | yes | yes |
| M8 right c=0.15 K=3 | proven | yes | yes | yes |
| M8 right c=0.2 K=3 | proven | yes | yes | yes |
| M8 left c=0.05 K=3 | proven | yes | yes | yes |
| M8 left c=0.1 K=3 | proven | yes | yes | yes |
| M8 left c=0.15 K=3 | proven | yes | yes | yes |
| M8 left c=0.2 K=3 | proven | yes | yes | yes |
| M10 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M10 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M10 right c=0.15 K=3 | proven | yes | yes | yes |
| M10 right c=0.2 K=3 | proven | yes | yes | yes |
| M10 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M10 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M10 left c=0.15 K=3 | proven | yes | yes | yes |
| M10 left c=0.2 K=3 | proven | yes | yes | yes |
| M12 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M12 right c=0.1 K=3 | proven | yes | yes | yes |
| M12 right c=0.15 K=3 | proven | yes | yes | yes |
| M12 right c=0.2 K=3 | proven | yes | yes | yes |
| M12 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M12 left c=0.1 K=3 | proven | yes | yes | yes |
| M12 left c=0.15 K=3 | proven | yes | yes | yes |
| M12 left c=0.2 K=3 | proven | yes | yes | yes |
| M14 right c=0.05 K=3 | proven | yes | yes | yes |
| M14 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M14 right c=0.15 K=3 | proven | yes | yes | yes |
| M14 right c=0.2 K=3 | proven | yes | yes | yes |
| M14 left c=0.05 K=3 | proven | yes | yes | yes |
| M14 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M14 left c=0.15 K=3 | proven | yes | yes | yes |
| M14 left c=0.2 K=3 | proven | yes | yes | yes |
| M16 right c=0.05 K=3 | proven | yes | yes | yes |
| M16 right c=0.1 K=3 | proven | yes | yes | yes |
| M16 right c=0.15 K=3 | proven | yes | yes | yes |
| M16 right c=0.2 K=3 | proven | yes | yes | yes |
| M16 left c=0.05 K=3 | proven | yes | yes | yes |
| M16 left c=0.1 K=3 | proven | yes | yes | yes |
| M16 left c=0.15 K=3 | proven | yes | yes | yes |
| M16 left c=0.2 K=3 | proven | yes | yes | yes |
| M18 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.15 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.2 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.15 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.2 K=3 | inconclusive | yes | NO | yes |
| M20 right c=0.05 K=3 | proven | yes | yes | yes |
| M20 right c=0.1 K=3 | proven | yes | yes | yes |
| M20 right c=0.15 K=3 | proven | yes | yes | yes |
| M20 right c=0.2 K=3 | proven | yes | yes | yes |
| M20 left c=0.05 K=3 | proven | yes | yes | yes |
| M20 left c=0.1 K=3 | proven | yes | yes | yes |
| M20 left c=0.15 K=3 | proven | yes | yes | yes |
| M20 left c=0.2 K=3 | proven | yes | yes | yes |

**Verdict:** not a pass: see the sections above

campaign finished
```

**What this shows / what it does not.** The campaign log reads the nine block runs back and prints the verdict. Its headline lines, verbatim: "selected K: 3"; "estimator: precise; max abs error 8.147e-06; T_gate 9e-05"; "pass bar: held" with "mesh checks skipped: 1025 of 7160 meshes unchecked"; "escape clause: FIRED" with "pair: not falsifiable for size M18 (right, left hand)"; turn caps reading "not established (non-decisive gate)" in the seconds column; and "**Verdict:** not a pass: see the sections above". The console log of the same run (`$HOME/screw-campaign-2026-10-08-a.log`, outside the repo) ends with "campaign finished" followed by "make: *** [Makefile:167: bench.thread] Error 1"; the `campaign` command's help text says it exits 1 unless the verdict is clean. This entry does not interpret the verdict.

### 2026-10-08-a-verdict

Re-run of the campaign verdict on the committed records, finished 2026-10-09T01:28:19Z (file time of the saved output), on HEAD `cb3c39bc3cbfbb0d92dfede7c56a679d0cd65d0a`. This is a computation over committed records, not a run: it reads the nine JSONL files of prefix `2026-10-08-a` and builds nothing, so it has no quiet gate, no release line and no load readings, and its output is not a timing.

Command: `.venv/bin/python -m bench.thread_spike verdict --campaign 2026-10-08-a > "$TMPDIR/verdict.txt"` (the Makefile form is `make bench.thread ARGS="verdict --campaign 2026-10-08-a"`).

Exit code: 1. That is the verdict command's designed exit for a verdict that is not a pass (protocol, "The verdict": it exits 0 only when the pass bar held, the escape clause did not fire and all six verdict blocks were read and complete); it is not a crash.

Reproducibility check: the output below is byte-identical (`cmp`, empty `diff`) to lines 13 to 1086 of `bench/results/thread-spike/2026-10-08-a-campaign.md`, which is the verdict section of the campaign log, from its `## Thread spike verdict: campaign 2026-10-08-a` heading to its `**Verdict:**` line, without the blank line and the final "campaign finished" line. sha256 of the saved output: 49b68b85c1ca04846a54487162545a7cee6ddeba78dfbefe5371e0243be908ba.

Output verbatim:

```
## Thread spike verdict: campaign 2026-10-08-a

- Blocks read: ksweep (run `2026-10-08-a-ksweep`, non-decisive), grid (run `2026-10-08-a-grid`, non-decisive), frontier (run `2026-10-08-a-frontier`, non-decisive), ladder (run `2026-10-08-a-ladder`, decisive), pair (run `2026-10-08-a-pair`, decisive), container (run `2026-10-08-a-container`, non-decisive), controls (run `2026-10-08-a-controls`, decisive), trim (run `2026-10-08-a-trim`, decisive), rss (run `2026-10-08-a-rss`, decisive)

### K

selected K: 3 (select_k over run `2026-10-08-a-ksweep`)

| K | Rows | Non-ok rows | Fine triangles at the standard max | STEP bytes at the standard max | Qualifies |
|---|---|---|---|---|---|
| 3 | 64 | 0 | 17600302 | 59043400 | yes |
| 5 | 64 | 0 | 18245886 | 56721599 | yes |
| 10 | 64 | 0 | 20504224 | 54245913 | yes |

### Volume estimator

estimator: precise; max abs error 8.147e-06; T_gate 9e-05

### Pass bar

pass bar: held
- mesh checks skipped: 1025 of 7160 meshes unchecked (a skipped check is not a pass for its mesh)

### Escape clause

escape clause: FIRED
- pair: not falsifiable for size M18 (right, left hand)

### Turn caps

| Size | Construction cap (turns) | Construction stop | Bytes cap (mm) | Bytes cap (turns) | Seconds cap (mm) |
|---|---|---|---|---|---|
| M2 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M2.5 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M3 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M3.5 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M4 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M5 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M6 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M7 | 250 | left: no stop up to 250 turns | no row over budget | no row over budget | not established (non-decisive gate) |
| M8 | 250 | left: no stop up to 250 turns | 67.5 | 54 | not established (non-decisive gate) |
| M10 | 250 | left: no stop up to 250 turns | 56 | 37.3333 | not established (non-decisive gate) |
| M12 | 250 | left: no stop up to 250 turns | 60 | 34.2857 | not established (non-decisive gate) |
| M14 | 250 | left: no stop up to 250 turns | 58 | 29 | not established (non-decisive gate) |
| M16 | 250 | left: no stop up to 250 turns | 52 | 26 | not established (non-decisive gate) |
| M18 | 250 | left: no stop up to 250 turns | 65 | 26 | not established (non-decisive gate) |
| M20 | 250 | left: no stop up to 250 turns | 64 | 25.6 | not established (non-decisive gate) |

- construction cap from run `2026-10-08-a-frontier`; bytes and seconds caps from run `2026-10-08-a-grid`
- M2: first row over the seconds budget: seconds not established (non-decisive gate)
- M2.5: first row over the seconds budget: seconds not established (non-decisive gate)
- M3: first row over the seconds budget: seconds not established (non-decisive gate)
- M3.5: first row over the seconds budget: seconds not established (non-decisive gate)
- M4: first row over the seconds budget: seconds not established (non-decisive gate)
- M5: first row over the seconds budget: seconds not established (non-decisive gate)
- M6: first row over the seconds budget: seconds not established (non-decisive gate)
- M7: first row over the seconds budget: seconds not established (non-decisive gate)
- M8: first row over the bytes budget: M8 right L=68 rod
- M8: first row over the seconds budget: seconds not established (non-decisive gate)
- M10: first row over the bytes budget: M10 right L=57 rod
- M10: first row over the seconds budget: seconds not established (non-decisive gate)
- M12: first row over the bytes budget: M12 right L=61 rod
- M12: first row over the seconds budget: seconds not established (non-decisive gate)
- M14: first row over the bytes budget: M14 right L=59 rod
- M14: first row over the seconds budget: seconds not established (non-decisive gate)
- M16: first row over the bytes budget: M16 right L=53 rod
- M16: first row over the seconds budget: seconds not established (non-decisive gate)
- M18: first row over the bytes budget: M18 right L=66 rod
- M18: first row over the seconds budget: seconds not established (non-decisive gate)
- M20: first row over the bytes budget: M20 right L=65 rod
- M20: first row over the seconds budget: seconds not established (non-decisive gate)

### Controls (D-06)

| Construction | Size | Length mm | Turns | Class | Solids | Valid | Precise ratio | Default ratio |
|---|---|---|---|---|---|---|---|---|
| naive sweep + fuse (negative control) | M2 | 4 | 10 | silent_wrong | 1 | yes | 0.290229 | 0.290298 |
| naive sweep + fuse (negative control) | M2 | 10 | 25 | silent_wrong | 1 | yes | 0.261206 | 0.261210 |
| naive sweep + fuse (negative control) | M2 | 20 | 50 | silent_wrong | 1 | yes | 0.251542 | 0.222915 |
| naive sweep + fuse (negative control) | M2.5 | 4.5 | 10 | silent_wrong | 1 | yes | 0.258961 | 0.259095 |
| naive sweep + fuse (negative control) | M2.5 | 10 | 22.2222 | silent_wrong | 1 | yes | 0.236871 | 0.236870 |
| naive sweep + fuse (negative control) | M2.5 | 20 | 44.4444 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M2.5 | 25 | 55.5556 | silent_wrong | 2 | yes | 1.035730 | 1.056853 |
| naive sweep + fuse (negative control) | M3 | 5 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M3 | 10 | 20 | silent_wrong | 1 | yes | 0.218512 | 0.218716 |
| naive sweep + fuse (negative control) | M3 | 20 | 40 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M3 | 30 | 60 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M6 | 10 | 10 | silent_wrong | 1 | yes | 0.238384 | 0.238232 |
| naive sweep + fuse (negative control) | M6 | 20 | 20 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M6 | 60 | 60 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 10 | 8 | silent_wrong | 1 | yes | 0.231722 | 0.231694 |
| naive sweep + fuse (negative control) | M8 | 12.5 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 20 | 16 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M8 | 80 | 64 | silent_wrong | 1 | yes | 0.191174 | 0.186273 |
| naive sweep + fuse (negative control) | M10 | 10 | 6.66667 | silent_wrong | 1 | yes | 0.230710 | 0.230710 |
| naive sweep + fuse (negative control) | M10 | 15 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M10 | 20 | 13.3333 | silent_wrong | 1 | yes | 1.026621 | 1.026622 |
| naive sweep + fuse (negative control) | M10 | 100 | 66.6667 | silent_wrong | 1 | yes | 0.182793 | 0.200653 |
| naive sweep + fuse (negative control) | M16 | 10 | 5 | silent_wrong | 1 | yes | 0.204723 | 0.204724 |
| naive sweep + fuse (negative control) | M16 | 20 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M16 | 160 | 80 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M20 | 10 | 4 | silent_wrong | 1 | yes | 0.219346 | 0.219347 |
| naive sweep + fuse (negative control) | M20 | 20 | 8 | silent_wrong | 1 | yes | 0.182789 | 0.182788 |
| naive sweep + fuse (negative control) | M20 | 25 | 10 | failure | n/a | n/a | n/a | n/a |
| naive sweep + fuse (negative control) | M20 | 200 | 80 | silent_wrong | 1 | yes | 0.149887 | 0.060069 |
| one-pipe twist | M2 | 20 | 50 | ok | 1 | yes | 0.999990 | 0.999021 |
| one-pipe twist | M2 | 40 | 100 | ok | 1 | yes | 0.999990 | 1.001131 |
| one-pipe twist | M2 | 64 | 160 | silent_wrong | 1 | yes | -1.000015 | -1.002367 |
| one-pipe twist | M2 | 80 | 200 | ok | 1 | yes | 0.999958 | 0.999035 |
| one-pipe twist | M2 | 100 | 250 | ok | 1 | yes | 0.999980 | 1.000803 |
| one-pipe twist | M2.5 | 25 | 55.5556 | ok | 1 | yes | 0.999996 | 1.000296 |
| one-pipe twist | M2.5 | 45 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M2.5 | 72 | 160 | silent_wrong | 1 | yes | -1.000008 | -1.002367 |
| one-pipe twist | M2.5 | 90 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M2.5 | 112.5 | 250 | ok | 1 | yes | 0.999994 | 0.999924 |
| one-pipe twist | M3 | 30 | 60 | ok | 1 | yes | 0.999984 | 1.000324 |
| one-pipe twist | M3 | 50 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M3 | 80 | 160 | silent_wrong | 1 | yes | -1.000007 | -1.002367 |
| one-pipe twist | M3 | 100 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M3 | 125 | 250 | ok | 1 | yes | 0.999993 | 0.999924 |
| one-pipe twist | M6 | 60 | 60 | ok | 1 | yes | 0.999994 | 0.999942 |
| one-pipe twist | M6 | 100 | 100 | ok | 1 | yes | 0.999999 | 1.000071 |
| one-pipe twist | M6 | 160 | 160 | silent_wrong | 1 | yes | -0.999995 | -1.001450 |
| one-pipe twist | M6 | 200 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M6 | 250 | 250 | ok | 1 | yes | 0.999993 | 0.999924 |
| one-pipe twist | M8 | 80 | 64 | ok | 1 | yes | 1.000010 | 0.999934 |
| one-pipe twist | M8 | 125 | 100 | ok | 1 | yes | 0.999998 | 1.000071 |
| one-pipe twist | M8 | 200 | 160 | silent_wrong | 1 | yes | -1.000006 | -0.999825 |
| one-pipe twist | M8 | 250 | 200 | ok | 1 | yes | 0.999988 | 1.000186 |
| one-pipe twist | M8 | 312.5 | 250 | ok | 1 | yes | 1.000000 | 0.999949 |
| one-pipe twist | M10 | 100 | 66.6667 | ok | 1 | yes | 1.000001 | 1.000171 |
| one-pipe twist | M10 | 150 | 100 | ok | 1 | yes | 0.999997 | 1.000064 |
| one-pipe twist | M10 | 240 | 160 | silent_wrong | 1 | yes | -1.000003 | -0.999897 |
| one-pipe twist | M10 | 300 | 200 | ok | 1 | yes | 0.999991 | 1.000156 |
| one-pipe twist | M10 | 375 | 250 | ok | 1 | yes | 1.000008 | 0.999949 |
| one-pipe twist | M16 | 160 | 80 | ok | 1 | yes | 0.999994 | 1.000130 |
| one-pipe twist | M16 | 200 | 100 | ok | 1 | yes | 0.999995 | 1.000055 |
| one-pipe twist | M16 | 320 | 160 | silent_wrong | 1 | yes | -1.000008 | -0.999897 |
| one-pipe twist | M16 | 400 | 200 | ok | 1 | yes | 0.999995 | 1.000114 |
| one-pipe twist | M16 | 500 | 250 | ok | 1 | yes | 0.999975 | 1.000072 |
| one-pipe twist | M20 | 200 | 80 | ok | 1 | yes | 0.999998 | 1.000013 |
| one-pipe twist | M20 | 250 | 100 | ok | 1 | yes | 0.999992 | 1.000014 |
| one-pipe twist | M20 | 400 | 160 | silent_wrong | 1 | yes | -0.999995 | -1.000023 |
| one-pipe twist | M20 | 500 | 200 | ok | 1 | yes | 0.999986 | 0.999853 |
| one-pipe twist | M20 | 625 | 250 | ok | 1 | yes | 0.999998 | 0.999993 |
| ruled-surface reference | M2 | 4 | 10 | silent_wrong | 1 | yes | 0.981297 | 0.874977 |
| ruled-surface reference | M2 | 20 | 50 | silent_wrong | 1 | yes | 0.995713 | 0.793632 |
| ruled-surface reference | M2.5 | 4.5 | 10 | silent_wrong | 1 | yes | 0.983412 | 0.876551 |
| ruled-surface reference | M2.5 | 25 | 55.5556 | silent_wrong | 1 | yes | 0.996569 | 1.015351 |
| ruled-surface reference | M3 | 5 | 10 | silent_wrong | 1 | yes | 0.984799 | 0.877611 |
| ruled-surface reference | M3 | 30 | 60 | silent_wrong | 1 | yes | 0.997092 | 0.623208 |
| ruled-surface reference | M6 | 10 | 10 | silent_wrong | 1 | yes | 0.985012 | 0.878017 |
| ruled-surface reference | M6 | 60 | 60 | silent_wrong | 1 | yes | 0.997312 | 0.595680 |
| ruled-surface reference | M8 | 12.5 | 10 | silent_wrong | 1 | yes | 0.986069 | 0.878869 |
| ruled-surface reference | M8 | 80 | 64 | silent_wrong | 1 | yes | 0.997679 | 0.976243 |
| ruled-surface reference | M10 | 15 | 10 | silent_wrong | 1 | yes | 0.986698 | 0.879391 |
| ruled-surface reference | M10 | 100 | 66.6667 | silent_wrong | 1 | yes | 0.997889 | 0.908570 |
| ruled-surface reference | M16 | 20 | 10 | silent_wrong | 1 | yes | 0.989094 | 0.881278 |
| ruled-surface reference | M16 | 160 | 80 | silent_wrong | 1 | yes | 0.998564 | 0.952563 |
| ruled-surface reference | M20 | 25 | 10 | silent_wrong | 1 | yes | 0.989110 | 0.881327 |
| ruled-surface reference | M20 | 200 | 80 | silent_wrong | 1 | yes | 0.998580 | 0.952577 |

Known-bad inputs for THRD-04 (naive rows with 1 solid, isValid True and a precise ratio below 0.5):
- naive_sweep_fuse(d=2.0, pitch=0.4, length=4.0): precise ratio 0.290229
- naive_sweep_fuse(d=2.0, pitch=0.4, length=10.0): precise ratio 0.261206
- naive_sweep_fuse(d=2.0, pitch=0.4, length=20.0): precise ratio 0.251542
- naive_sweep_fuse(d=2.5, pitch=0.45, length=4.5): precise ratio 0.258961
- naive_sweep_fuse(d=2.5, pitch=0.45, length=10.0): precise ratio 0.236871
- naive_sweep_fuse(d=3.0, pitch=0.5, length=10.0): precise ratio 0.218512
- naive_sweep_fuse(d=6.0, pitch=1.0, length=10.0): precise ratio 0.238384
- naive_sweep_fuse(d=8.0, pitch=1.25, length=10.0): precise ratio 0.231722
- naive_sweep_fuse(d=8.0, pitch=1.25, length=80.0): precise ratio 0.191174
- naive_sweep_fuse(d=10.0, pitch=1.5, length=10.0): precise ratio 0.230710
- naive_sweep_fuse(d=10.0, pitch=1.5, length=100.0): precise ratio 0.182793
- naive_sweep_fuse(d=16.0, pitch=2.0, length=10.0): precise ratio 0.204723
- naive_sweep_fuse(d=20.0, pitch=2.5, length=10.0): precise ratio 0.219346
- naive_sweep_fuse(d=20.0, pitch=2.5, length=20.0): precise ratio 0.182789
- naive_sweep_fuse(d=20.0, pitch=2.5, length=200.0): precise ratio 0.149887

The ruled-surface profile is not identical to the pinned profile, so its ratio to this closed form is not an accuracy claim.

### Tip trim cost (D-08)

| Size | Hand | Length mm | Class | Trim s | Request s (build + trim + slower export) | Fine triangles | STEP bytes |
|---|---|---|---|---|---|---|---|
| M2 | right | 20 | ok | 0.21 | 0.55 | 310660 | 2672684 |
| M2 | left | 20 | ok | 0.19 | 0.51 | 278332 | 2672228 |
| M2.5 | right | 25 | ok | 0.20 | 0.59 | 412682 | 2971967 |
| M2.5 | left | 25 | ok | 0.22 | 0.57 | 330746 | 3005466 |
| M3 | right | 30 | ok | 0.23 | 0.71 | 452446 | 3260380 |
| M3 | left | 30 | ok | 0.24 | 0.66 | 365390 | 3262870 |
| M3.5 | right | 35 | ok | 0.22 | 0.71 | 450624 | 3180075 |
| M3.5 | left | 35 | ok | 0.24 | 0.69 | 367860 | 3199718 |
| M4 | right | 40 | ok | 0.20 | 0.72 | 532590 | 3493913 |
| M4 | left | 40 | ok | 0.21 | 0.67 | 389820 | 3494580 |
| M5 | right | 50 | ok | 0.26 | 0.90 | 601758 | 3784631 |
| M5 | left | 50 | ok | 0.27 | 0.82 | 441464 | 3786540 |
| M6 | right | 60 | ok | 0.27 | 0.89 | 608308 | 3651443 |
| M6 | left | 60 | ok | 0.27 | 0.81 | 453904 | 3651209 |
| M7 | right | 70 | ok | 0.28 | 0.97 | 736190 | 4257790 |
| M7 | left | 70 | ok | 0.29 | 0.89 | 558460 | 4260863 |
| M8 | right | 80 | ok | 0.26 | 1.13 | 1072962 | 3933673 |
| M8 | left | 80 | ok | 0.27 | 1.05 | 873052 | 3935714 |
| M10 | right | 100 | ok | 0.28 | 1.56 | 1613994 | 3736332 |
| M10 | left | 100 | ok | 0.29 | 1.41 | 1247152 | 3715911 |
| M12 | right | 120 | ok | 0.31 | 1.89 | 1805228 | 4212788 |
| M12 | left | 120 | ok | 0.31 | 1.68 | 1427396 | 4234645 |
| M14 | right | 140 | ok | 0.30 | 2.25 | 2194088 | 4368959 |
| M14 | left | 140 | ok | 0.30 | 2.00 | 1634744 | 4374068 |
| M16 | right | 160 | ok | 0.36 | 2.71 | 2768418 | 4983558 |
| M16 | left | 160 | ok | 0.36 | 2.39 | 1951234 | 4970441 |
| M18 | right | 180 | ok | 0.36 | 2.40 | 2476444 | 4527783 |
| M18 | left | 180 | ok | 0.37 | 2.04 | 1778886 | 4535139 |
| M20 | right | 200 | ok | 0.36 | 2.67 | 2894830 | 5050734 |
| M20 | left | 200 | ok | 0.36 | 2.32 | 2014508 | 5043593 |

The cone angle is 30 degrees from the end face at the minor radius, UNVERIFIED (ISO 4753 is unread): these rows are cost evidence for Phase 4, not geometry truth, and never enter the pass bar.

### Peak RSS and the L19 gzip table

| Size | Hand | Preset | Turns | Length mm | Row | Peak RSS | Class |
|---|---|---|---|---|---|---|---|
| M2 | right | preview | 50 | 20 | standard max | 511.5 MiB (fresh child, this row only) | ok |
| M2 | right | fine | 50 | 20 | standard max | 865.7 MiB (fresh child, this row only) | ok |
| M2 | right | fine | 250 | 100 | frontier terminal | 1138.2 MiB (fresh child, this row only) | ok |
| M2 | left | preview | 50 | 20 | standard max | 509.1 MiB (fresh child, this row only) | ok |
| M2 | left | fine | 50 | 20 | standard max | 853.4 MiB (fresh child, this row only) | ok |
| M2 | left | fine | 250 | 100 | frontier terminal | 1113.8 MiB (fresh child, this row only) | ok |
| M2.5 | right | preview | 55.5556 | 25 | standard max | 515.5 MiB (fresh child, this row only) | ok |
| M2.5 | right | fine | 55.5556 | 25 | standard max | 943.0 MiB (fresh child, this row only) | ok |
| M2.5 | right | fine | 250 | 112.5 | frontier terminal | 1174.0 MiB (fresh child, this row only) | ok |
| M2.5 | left | preview | 55.5556 | 25 | standard max | 514.3 MiB (fresh child, this row only) | ok |
| M2.5 | left | fine | 55.5556 | 25 | standard max | 904.3 MiB (fresh child, this row only) | ok |
| M2.5 | left | fine | 250 | 112.5 | frontier terminal | 1158.1 MiB (fresh child, this row only) | ok |
| M3 | right | preview | 60 | 30 | standard max | 524.9 MiB (fresh child, this row only) | ok |
| M3 | right | fine | 60 | 30 | standard max | 1020.9 MiB (fresh child, this row only) | ok |
| M3 | right | fine | 250 | 125 | frontier terminal | 1256.8 MiB (fresh child, this row only) | ok |
| M3 | left | preview | 60 | 30 | standard max | 517.3 MiB (fresh child, this row only) | ok |
| M3 | left | fine | 60 | 30 | standard max | 1017.7 MiB (fresh child, this row only) | ok |
| M3 | left | fine | 250 | 125 | frontier terminal | 1179.0 MiB (fresh child, this row only) | ok |
| M3.5 | right | preview | 58.3333 | 35 | standard max | 525.8 MiB (fresh child, this row only) | ok |
| M3.5 | right | fine | 58.3333 | 35 | standard max | 1102.9 MiB (fresh child, this row only) | ok |
| M3.5 | right | fine | 250 | 150 | frontier terminal | 1248.4 MiB (fresh child, this row only) | ok |
| M3.5 | left | preview | 58.3333 | 35 | standard max | 520.5 MiB (fresh child, this row only) | ok |
| M3.5 | left | fine | 58.3333 | 35 | standard max | 1062.5 MiB (fresh child, this row only) | ok |
| M3.5 | left | fine | 250 | 150 | frontier terminal | 1231.3 MiB (fresh child, this row only) | ok |
| M4 | right | preview | 57.1429 | 40 | standard max | 529.2 MiB (fresh child, this row only) | ok |
| M4 | right | fine | 57.1429 | 40 | standard max | 1121.0 MiB (fresh child, this row only) | ok |
| M4 | right | fine | 250 | 175 | frontier terminal | 1367.9 MiB (fresh child, this row only) | ok |
| M4 | left | preview | 57.1429 | 40 | standard max | 525.1 MiB (fresh child, this row only) | ok |
| M4 | left | fine | 57.1429 | 40 | standard max | 1114.6 MiB (fresh child, this row only) | ok |
| M4 | left | fine | 250 | 175 | frontier terminal | 1246.5 MiB (fresh child, this row only) | ok |
| M5 | right | preview | 62.5 | 50 | standard max | 550.3 MiB (fresh child, this row only) | ok |
| M5 | right | fine | 62.5 | 50 | standard max | 1142.7 MiB (fresh child, this row only) | ok |
| M5 | right | fine | 250 | 200 | frontier terminal | 1392.6 MiB (fresh child, this row only) | ok |
| M5 | left | preview | 62.5 | 50 | standard max | 538.3 MiB (fresh child, this row only) | ok |
| M5 | left | fine | 62.5 | 50 | standard max | 1072.2 MiB (fresh child, this row only) | ok |
| M5 | left | fine | 250 | 200 | frontier terminal | 1226.2 MiB (fresh child, this row only) | ok |
| M6 | right | preview | 60 | 60 | standard max | 545.7 MiB (fresh child, this row only) | ok |
| M6 | right | fine | 60 | 60 | standard max | 1171.0 MiB (fresh child, this row only) | ok |
| M6 | right | fine | 250 | 250 | frontier terminal | 1387.2 MiB (fresh child, this row only) | ok |
| M6 | left | preview | 60 | 60 | standard max | 538.6 MiB (fresh child, this row only) | ok |
| M6 | left | fine | 60 | 60 | standard max | 1094.3 MiB (fresh child, this row only) | ok |
| M6 | left | fine | 250 | 250 | frontier terminal | 1310.8 MiB (fresh child, this row only) | ok |
| M7 | right | preview | 70 | 70 | standard max | 553.3 MiB (fresh child, this row only) | ok |
| M7 | right | fine | 70 | 70 | standard max | 1182.3 MiB (fresh child, this row only) | ok |
| M7 | right | fine | 250 | 250 | frontier terminal | 1430.1 MiB (fresh child, this row only) | ok |
| M7 | left | preview | 70 | 70 | standard max | 545.2 MiB (fresh child, this row only) | ok |
| M7 | left | fine | 70 | 70 | standard max | 1141.1 MiB (fresh child, this row only) | ok |
| M7 | left | fine | 250 | 250 | frontier terminal | 1278.3 MiB (fresh child, this row only) | ok |
| M8 | right | preview | 64 | 80 | standard max | 560.0 MiB (fresh child, this row only) | ok |
| M8 | right | fine | 64 | 80 | standard max | 1305.7 MiB (fresh child, this row only) | ok |
| M8 | right | fine | 250 | 312.5 | frontier terminal | 1769.9 MiB (fresh child, this row only) | ok |
| M8 | left | preview | 64 | 80 | standard max | 550.6 MiB (fresh child, this row only) | ok |
| M8 | left | fine | 64 | 80 | standard max | 1239.5 MiB (fresh child, this row only) | ok |
| M8 | left | fine | 250 | 312.5 | frontier terminal | 1608.6 MiB (fresh child, this row only) | ok |
| M10 | right | preview | 66.6667 | 100 | standard max | 560.2 MiB (fresh child, this row only) | ok |
| M10 | right | fine | 66.6667 | 100 | standard max | 1463.4 MiB (fresh child, this row only) | ok |
| M10 | right | fine | 250 | 375 | frontier terminal | 2267.5 MiB (fresh child, this row only) | ok |
| M10 | left | preview | 66.6667 | 100 | standard max | 554.0 MiB (fresh child, this row only) | ok |
| M10 | left | fine | 66.6667 | 100 | standard max | 1407.6 MiB (fresh child, this row only) | ok |
| M10 | left | fine | 250 | 375 | frontier terminal | 1885.2 MiB (fresh child, this row only) | ok |
| M12 | right | preview | 68.5714 | 120 | standard max | 567.9 MiB (fresh child, this row only) | ok |
| M12 | right | fine | 68.5714 | 120 | standard max | 1688.5 MiB (fresh child, this row only) | ok |
| M12 | right | fine | 250 | 437.5 | frontier terminal | 2392.9 MiB (fresh child, this row only) | ok |
| M12 | left | preview | 68.5714 | 120 | standard max | 558.7 MiB (fresh child, this row only) | ok |
| M12 | left | fine | 68.5714 | 120 | standard max | 1602.6 MiB (fresh child, this row only) | ok |
| M12 | left | fine | 250 | 437.5 | frontier terminal | 2112.9 MiB (fresh child, this row only) | ok |
| M14 | right | preview | 70 | 140 | standard max | 581.5 MiB (fresh child, this row only) | ok |
| M14 | right | fine | 70 | 140 | standard max | 1872.4 MiB (fresh child, this row only) | ok |
| M14 | right | fine | 250 | 500 | frontier terminal | 2610.5 MiB (fresh child, this row only) | ok |
| M14 | left | preview | 70 | 140 | standard max | 571.0 MiB (fresh child, this row only) | ok |
| M14 | left | fine | 70 | 140 | standard max | 1748.7 MiB (fresh child, this row only) | ok |
| M14 | left | fine | 250 | 500 | frontier terminal | 2264.2 MiB (fresh child, this row only) | ok |
| M16 | right | preview | 80 | 160 | standard max | 643.0 MiB (fresh child, this row only) | ok |
| M16 | right | fine | 80 | 160 | standard max | 1916.6 MiB (fresh child, this row only) | ok |
| M16 | right | fine | 250 | 500 | frontier terminal | 2730.9 MiB (fresh child, this row only) | ok |
| M16 | left | preview | 80 | 160 | standard max | 639.8 MiB (fresh child, this row only) | ok |
| M16 | left | fine | 80 | 160 | standard max | 1784.3 MiB (fresh child, this row only) | ok |
| M16 | left | fine | 250 | 500 | frontier terminal | 2281.6 MiB (fresh child, this row only) | ok |
| M18 | right | preview | 72 | 180 | standard max | 673.5 MiB (fresh child, this row only) | ok |
| M18 | right | fine | 72 | 180 | standard max | 1795.1 MiB (fresh child, this row only) | ok |
| M18 | right | fine | 250 | 625 | frontier terminal | 2741.7 MiB (fresh child, this row only) | ok |
| M18 | left | preview | 72 | 180 | standard max | 676.5 MiB (fresh child, this row only) | ok |
| M18 | left | fine | 72 | 180 | standard max | 1651.4 MiB (fresh child, this row only) | ok |
| M18 | left | fine | 250 | 625 | frontier terminal | 2329.5 MiB (fresh child, this row only) | ok |
| M20 | right | preview | 80 | 200 | standard max | 711.0 MiB (fresh child, this row only) | ok |
| M20 | right | fine | 80 | 200 | standard max | 1854.9 MiB (fresh child, this row only) | ok |
| M20 | right | fine | 250 | 625 | frontier terminal | 2804.6 MiB (fresh child, this row only) | ok |
| M20 | left | preview | 80 | 200 | standard max | 682.4 MiB (fresh child, this row only) | ok |
| M20 | left | fine | 80 | 200 | standard max | 1785.3 MiB (fresh child, this row only) | ok |
| M20 | left | fine | 250 | 625 | frontier terminal | 2291.8 MiB (fresh child, this row only) | ok |

L19 gzip table (levels 1, 6 and 9 on the row's own STL, fresh child):

| Size | Level | Output bytes | Single-threaded median ms | 10-concurrent wall median ms |
|---|---|---|---|---|
| M2 | 1 | 7024461 | 101.7 | 122.6 |
| M2 | 6 | 6752985 | 183.6 | 222.1 |
| M2 | 9 | 6754143 | 206.7 | 254.4 |
| M2.5 | 1 | 9639781 | 143.4 | 169.0 |
| M2.5 | 6 | 9219593 | 242.3 | 293.5 |
| M2.5 | 9 | 9220536 | 264.4 | 323.7 |
| M3 | 1 | 10634274 | 160.2 | 186.7 |
| M3 | 6 | 10139845 | 288.7 | 353.4 |
| M3 | 9 | 10140314 | 329.3 | 403.5 |
| M3.5 | 1 | 10583521 | 162.1 | 186.8 |
| M3.5 | 6 | 10147763 | 275.7 | 330.1 |
| M3.5 | 9 | 10148944 | 300.0 | 360.2 |
| M4 | 1 | 12356444 | 189.8 | 218.2 |
| M4 | 6 | 11848427 | 323.9 | 381.7 |
| M4 | 9 | 11850333 | 348.5 | 413.0 |
| M5 | 1 | 13850880 | 210.1 | 240.3 |
| M5 | 6 | 13246686 | 364.3 | 426.0 |
| M5 | 9 | 13248972 | 397.4 | 467.7 |
| M6 | 1 | 13970930 | 211.8 | 242.4 |
| M6 | 6 | 13360183 | 374.0 | 436.5 |
| M6 | 9 | 13361643 | 417.4 | 490.4 |
| M7 | 1 | 17249144 | 260.4 | 297.4 |
| M7 | 6 | 16505179 | 459.8 | 539.1 |
| M7 | 9 | 16507342 | 521.9 | 618.4 |
| M8 | 1 | 25818148 | 387.9 | 447.9 |
| M8 | 6 | 24831288 | 652.8 | 766.7 |
| M8 | 9 | 24834915 | 721.2 | 847.9 |
| M10 | 1 | 37691313 | 563.3 | 649.6 |
| M10 | 6 | 35970130 | 1019.6 | 1191.7 |
| M10 | 9 | 35975052 | 1111.5 | 1298.9 |
| M12 | 1 | 42084822 | 632.5 | 733.0 |
| M12 | 6 | 40259958 | 1142.4 | 1335.4 |
| M12 | 9 | 40262125 | 1221.5 | 1438.2 |
| M14 | 1 | 50611949 | 765.1 | 885.9 |
| M14 | 6 | 48446123 | 1434.1 | 1684.6 |
| M14 | 9 | 48447578 | 1580.8 | 1877.8 |
| M16 | 1 | 62726041 | 942.2 | 1104.9 |
| M16 | 6 | 60072616 | 1795.3 | 2111.0 |
| M16 | 9 | 60071266 | 1985.2 | 2338.3 |
| M18 | 1 | 56785836 | 847.5 | 998.2 |
| M18 | 6 | 54535211 | 1533.7 | 1803.9 |
| M18 | 9 | 54539361 | 1646.8 | 1942.5 |
| M20 | 1 | 66190237 | 982.5 | 1161.8 |
| M20 | 6 | 63558367 | 1751.3 | 2064.0 |
| M20 | 9 | 63562242 | 1873.8 | 2198.8 |

- M2: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M2.5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M3: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M3.5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M4: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M5: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M6: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M7: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M8: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M10: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M12: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M14: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M16: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M18: selected gzip level 1 (spur L19's rule, `select_gzip_level`)
- M20: selected gzip level 1 (spur L19's rule, `select_gzip_level`)

### Container validity (D-05)

7160 rows in `screw:latest` under linux/amd64: ok 7160, silent_wrong 0, failure 0, timeout 0, worker_died 0.
Every timing in this run is emulation: validity, solid count and volume are the measurement, and a timing here feeds no bound (D-05).

### Pair check (D-11 to D-14)

Locked K = 3; every cell below is read at it. A cell is proven only if all 3 matched poses read empty (<= 1e-06 mm3) and all 3 controls read within 0.001 of the closed form (D-12, D-14).

#### M2 right hand (m = 1.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.428872/0.428877/0.428872 | 0.859203/0.859202/0.859203 | 0.859202 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0.647798/0/0.647798 | 0.647802 | 0/0/0 ; 1/0/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.455395/0.455395/0.455396 | 0.455399 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.284711/0 | 0.284715 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.138463/0.138464/0.138464 | 0.138468 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0/0.0244833/0 | 0.0244813 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M2 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.284715 mm3); control at theta +2.0944 reads empty (closed form 0.284715 mm3)
- M2 right c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 0.0244813 mm3); control at theta +2.0944 reads empty (closed form 0.0244813 mm3)

#### M2 left hand (m = 1.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.428872/0.428877/0.428872 | 0.859203/0.859202/0.859202 | 0.859202 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0.647798/0/0.647797 | 0.647802 | 0/0/0 ; 1/0/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.455396/0.455395/0.455395 | 0.455399 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.284711/0 | 0.284715 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.138464/0.138464/0.138463 | 0.138468 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0/0.0244833/0 | 0.0244813 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M2 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.284715 mm3); control at theta +2.0944 reads empty (closed form 0.284715 mm3)
- M2 left c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 0.0244813 mm3); control at theta +2.0944 reads empty (closed form 0.0244813 mm3)

#### M2.5 right hand (m = 2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.683622/0.6836/0.683576 | 1.49169/1.49171/1.49169 | 1.49169 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.15397/1.15398/1.15397 | 1.15397 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.845031/0.845045/0.845032 | 0.845035 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.567913/0 | 0.567908 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.325602/0.325609/0.325603 | 0.325612 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.121421/0.121424/0.121422 | 0.121426 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M2.5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2.5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2.5 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.567908 mm3); control at theta +2.0944 reads empty (closed form 0.567908 mm3)

#### M2.5 left hand (m = 2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.683576/0.6836/0.683622 | 1.49169/1.49171/1.49168 | 1.49169 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.15397/1.15399/1.15397 | 1.15397 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0.845034/0.845046/0.84503 | 0.845035 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/0.567914/0 | 0.567908 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0.325603/0.32561/0.325601 | 0.325612 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.121421/0.121424/0.12142 | 0.121426 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M2.5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M2.5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M2.5 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 0.567908 mm3); control at theta +2.0944 reads empty (closed form 0.567908 mm3)

#### M3 right hand (m = 2.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.997365/0.99734/0.997269 | 0/2.35538/2.35539 | 2.35543 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.86255/1.86258/1.86258 | 1.86262 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/1.40915/1.40915 | 1.4092 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0.998331/0.998359/0.99836 | 0.998409 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 0/0.633481/0 | 0.633531 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0.317787/0.317808/0.317809 | 0.317827 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M3 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 1.4092 mm3)
- M3 right c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 0.633531 mm3); control at theta +2.0944 reads empty (closed form 0.633531 mm3)

#### M3 left hand (m = 2.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 0.997269/0.99734/0.997365 | 2.35539/2.35538/0 | 2.35543 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 1.86258/1.86258/1.86255 | 1.86262 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 1.40915/1.40915/0 | 1.4092 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0.998359/0.998359/0.99833 | 0.998409 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 0/0.633481/0 | 0.633531 | 0/0/0 ; 0/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0.317809/0.317808/0.317787 | 0.317827 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M3 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 1.4092 mm3)
- M3 left c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 0.633531 mm3); control at theta +2.0944 reads empty (closed form 0.633531 mm3)

#### M3.5 right hand (m = 2.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.35671/1.3567/1.3567 | 3.69532/3.69532/3.69531 | 3.69532 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 3.0328/3.03279/3.03279 | 3.0328 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 2.4141/2.4141/2.4141 | 2.4141 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 1.84241/1.8424/1.8424 | 1.8424 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 1.32088/1.32088/1.32088 | 1.32088 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.852706/0.852705/0.852704 | 0.852709 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3.5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3.5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M3.5 left hand (m = 2.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.3567/1.3567/1.35671 | 3.69531/3.69531/3.69532 | 3.69532 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000633645/0/0 | 3.03279/3.03279/3.0328 | 3.0328 | 25/0/0 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 2.4141/2.4141/2.4141 | 2.4141 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 1.8424/1.8424/1.84241 | 1.8424 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 1.32088/1.32088/1.32088 | 1.32088 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 0.852704/0.852704/0.852707 | 0.852709 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M3.5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M3.5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M4 right hand (m = 3.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.77124/1.77123/1.77123 | 5.46813/5.46812/5.46812 | 5.46812 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 5.79139e-06/0/-0.00279567 | 4.61056/4.61056/4.61056 | 4.61055 | 4/0/12 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/3.80135/3.80135 | 3.80135 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 3.04361/3.04361/3.04361 | 3.04361 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 2.34045/2.34045/2.34045 | 2.34044 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 1.69497/1.69497/1.69497 | 1.69497 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M4 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M4 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M4 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 3.80135 mm3)

#### M4 left hand (m = 3.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 1.77123/1.77123/1.77124 | 5.46812/5.46812/5.46812 | 5.46812 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0910952/0/-0.00132387 | 4.61056/4.61056/4.61056 | 4.61055 | 10/0/12 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 3.80135/3.80135/0 | 3.80135 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 3.04361/3.04361/3.04361 | 3.04361 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 2.34045/2.34045/2.34045 | 2.34044 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 1.69497/1.69497/1.69497 | 1.69497 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M4 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M4 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M4 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 3.80135 mm3)

#### M5 right hand (m = 4.7 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 3.29489/3.29482/3.29482 | 11.3681/11.3681/11.3681 | 11.3681 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -2.1969e-06/0/-0.0184956 | 9.76954/9.76954/9.76954 | 9.76953 | 5/0/15 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 8.25346/8.25346/0 | 8.25345 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 6.82381/6.82382/6.82381 | 6.8238 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 5.4846/5.48461/5.48461 | 5.4846 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 4.23983/4.23983/4.23983 | 4.23982 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M5 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M5 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M5 right c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 8.25345 mm3)

#### M5 left hand (m = 4.7 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 3.29482/3.29482/3.29489 | 11.3681/11.3681/11.3681 | 11.3681 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00240809/0/0.00325241 | 9.76954/9.76954/9.76954 | 9.76953 | 17/0/11 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/8.25346/8.25346 | 8.25345 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 6.82381/6.82381/6.82381 | 6.8238 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 5.48461/5.4846/5.4846 | 5.4846 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 4.23983/4.23983/4.23983 | 4.23982 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M5 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M5 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M5 left c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 8.25345 mm3)

#### M6 right hand (m = 5.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 4.36276/4.36266/4.36271 | 18.2374/18.2374/18.2373 | 18.2374 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00177739/0/-0.00603191 | 16.1428/16.1428/16.1427 | 16.1427 | 13/0/7 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 14.1335/14.1335/14.1334 | 14.1335 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 12.213/12.213/12.213 | 12.213 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 10.385/10.385/10.3849 | 10.385 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 8.65294/8.65294/8.65289 | 8.65288 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M6 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M6 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M6 left hand (m = 5.2 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 4.36271/4.36266/4.36276 | 18.2373/18.2374/18.2374 | 18.2374 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.00513391/0/-0.0115552 | 16.1427/16.1428/16.1428 | 16.1427 | 9/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 14.1334/14.1335/14.1335 | 14.1335 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 12.213/12.213/12.213 | 12.213 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 10.3849/10.385/10.385 | 10.385 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 8.65289/8.65294/8.65294 | 8.65288 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M6 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M6 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M7 right hand (m = 5.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 5.57807/5.5779/5.57786 | 23.3066/23.3066/23.3066 | 23.3066 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.319506/0/-0.492389 | 20.5983/20.5983/20.5983 | 20.5983 | 11/0/14 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/18.0073/18.0073 | 18.0073 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 15.5375/15.5374/15.5374 | 15.5375 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 13.1925/13.1924/13.1925 | 13.1925 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 10.9762/10.9761/10.9762 | 10.9762 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M7 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M7 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M7 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 18.0073 mm3)

#### M7 left hand (m = 5.6 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 5.57786/5.5779/5.57807 | 23.3066/23.3066/23.3066 | 23.3066 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.453107/0/-0.00801368 | 20.5983/20.5983/20.5983 | 20.5983 | 19/0/8 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 18.0073/18.0073/0 | 18.0073 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 15.5374/15.5375/15.5374 | 15.5375 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 13.1925/13.1925/13.1925 | 13.1925 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 10.9762/10.9762/10.9762 | 10.9762 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M7 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M7 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M7 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 18.0073 mm3)

#### M8 right hand (m = 6.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 7.67898/7.6787/7.67872 | 39.1066/39.1066/0 | 39.1065 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.00082956/0/0.00415998 | 35.4231/35.4231/35.4231 | 35.423 | 12/0/9 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 31.8635/31.8635/31.8635 | 31.8635 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 28.4315/28.4315/28.4315 | 28.4315 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 25.1309/25.1309/25.1309 | 25.1308 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 21.9652/21.9652/21.9652 | 21.9652 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M8 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M8 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M8 left hand (m = 6.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 7.67872/7.6787/7.67898 | 0/39.1065/39.1066 | 39.1065 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0393199/0/0.00759806 | 35.4231/35.4231/35.4231 | 35.423 | 11/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 31.8635/31.8635/31.8635 | 31.8635 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 28.4315/28.4315/28.4315 | 28.4315 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 25.1308/25.1308/25.1308 | 25.1308 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 21.9652/21.9652/21.9652 | 21.9652 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M8 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M8 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M10 right hand (m = 8.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 11.9241/11.9235/11.923 | 71.6178/71.6178/71.6181 | 71.618 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000873794/0/0.00116949 | 65.9036/65.9037/65.9039 | 65.9038 | 7/0/10 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/60.3527/60.353 | 60.3528 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0/54.9688/54.9691 | 54.9689 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 49.7557/49.7557/49.756 | 49.7558 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 44.7172/44.7173/44.7175 | 44.7174 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M10 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M10 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M10 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 60.3528 mm3)
- M10 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 54.9689 mm3)

#### M10 left hand (m = 8.4 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 11.923/11.9235/11.9241 | 71.6181/71.6179/71.6178 | 71.618 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0225569/0/0.00510398 | 65.9039/65.9037/65.9036 | 65.9038 | 9/0/11 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 60.353/60.3528/0 | 60.3528 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 54.969/54.9688/0 | 54.9689 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 49.756/49.7558/49.7556 | 49.7558 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 44.7175/44.7173/44.7172 | 44.7174 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M10 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M10 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M10 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 60.3528 mm3)
- M10 left c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 54.9689 mm3)

#### M12 right hand (m = 10.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 18.4657/18.4649/18.465 | 127.789/127.789/127.789 | 127.789 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0.00778178/0/0.0176886 | 118.947/118.947/0 | 118.947 | 8/0/8 ; 1/1/0 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 110.325/110.325/0 | 110.325 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 101.926/101.926/101.926 | 101.926 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 93.7549/93.7551/93.755 | 93.7548 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 85.8153/85.8155/85.8155 | 85.8153 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M12 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M12 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M12 right c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 110.325 mm3)

#### M12 left hand (m = 10.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 18.465/18.4649/18.4657 | 127.789/127.789/127.789 | 127.789 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0593007/0/-0.0279531 | 0/118.947/118.947 | 118.947 | 13/0/11 ; 0/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/110.325/110.325 | 110.325 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 101.926/101.926/101.926 | 101.926 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 93.7549/93.7549/93.7548 | 93.7548 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 85.8154/85.8154/85.8153 | 85.8153 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M12 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M12 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M12 left c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 110.325 mm3)

#### M14 right hand (m = 12.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 25.6006/25.5995/25.6008 | 200.577/200.576/200.576 | 200.576 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.000104004/0/-9.33039e-05 | 188.328/188.328/188.327 | 188.328 | 6/0/6 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 176.348/176.347/176.346 | 176.347 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 164.639/164.639/0 | 164.639 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 153.208/153.207/153.207 | 153.207 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 142.057/142.057/142.056 | 142.057 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M14 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M14 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M14 right c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 164.639 mm3)

#### M14 left hand (m = 12.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 25.6008/25.5995/25.6006 | 200.576/200.576/200.577 | 200.576 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | -0.0249251/0/-0.0240166 | 188.327/188.328/188.328 | 188.328 | 10/0/8 ; 1/1/1 | errors 0 of 6, warnings 2 of 6 | inconclusive |
| 0.05 | 0/0/0 | 176.346/176.347/176.347 | 176.347 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 0/164.639/164.639 | 164.639 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 153.207/153.207/153.208 | 153.207 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 142.056/142.057/142.057 | 142.057 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M14 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M14 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M14 left c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 164.639 mm3)

#### M16 right hand (m = 14.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 34.249/34.249/34.2488 | 268.248/268.248/268.248 | 268.249 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 251.727/251.727/251.727 | 251.728 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 235.584/235.583/235.583 | 235.585 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 219.822/219.822/219.822 | 219.823 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 204.447/204.447/204.447 | 204.448 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 189.465/189.464/189.464 | 189.466 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M16 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M16 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M16 left hand (m = 14.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 34.2488/34.249/34.249 | 268.248/268.248/268.248 | 268.249 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 251.727/251.727/251.727 | 251.728 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 235.583/235.583/235.584 | 235.585 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 219.822/219.822/219.822 | 219.823 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 204.447/204.447/204.447 | 204.448 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 189.464/189.464/189.465 | 189.466 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M16 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M16 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M18 right hand (m = 15.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 40.7729/40.7719/40.7716 | 0/394.049/394.049 | 394.05 | 1/1/1 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 0/374.563/374.562 | 374.564 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 0/355.422/355.421 | 355.423 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 0/336.63/336.63 | 336.632 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 0/318.193/318.193 | 318.194 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 0/300.113/300.113 | 300.115 | 0/0/0 ; 0/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M18 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M18 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M18 right c=0.05: inconclusive: control at theta -2.0944 reads empty (closed form 355.423 mm3)
- M18 right c=0.1: inconclusive: control at theta -2.0944 reads empty (closed form 336.632 mm3)
- M18 right c=0.15: inconclusive: control at theta -2.0944 reads empty (closed form 318.194 mm3)
- M18 right c=0.2: inconclusive: control at theta -2.0944 reads empty (closed form 300.115 mm3)

#### M18 left hand (m = 15.8 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 40.7716/40.7719/40.7729 | 394.049/394.049/0 | 394.05 | 1/1/1 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 374.562/374.562/0 | 374.564 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 355.421/355.421/0 | 355.423 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.1 | 0/0/0 | 336.63/336.63/0 | 336.632 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.15 | 0/0/0 | 318.192/318.193/0 | 318.194 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.2 | 0/0/0 | 300.113/300.113/0 | 300.115 | 0/0/0 ; 1/1/0 | errors 0 of 6, warnings 0 of 6 | inconclusive |

- M18 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M18 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)
- M18 left c=0.05: inconclusive: control at theta +2.0944 reads empty (closed form 355.423 mm3)
- M18 left c=0.1: inconclusive: control at theta +2.0944 reads empty (closed form 336.632 mm3)
- M18 left c=0.15: inconclusive: control at theta +2.0944 reads empty (closed form 318.194 mm3)
- M18 left c=0.2: inconclusive: control at theta +2.0944 reads empty (closed form 300.115 mm3)

#### M20 right hand (m = 18 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 52.1062/52.1031/52.1072 | 503.428/503.428/503.429 | 503.429 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 478.369/478.369/478.37 | 478.369 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 453.768/453.768/453.769 | 453.768 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 429.63/429.63/429.632 | 429.631 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 405.961/405.962/405.963 | 405.962 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 382.766/382.766/382.767 | 382.766 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M20 right c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M20 right c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### M20 left hand (m = 18 mm, UNVERIFIED)

| c mm | Matched mm3 (-2pi/3, 0, 2pi/3) | Control mm3 (same poses) | Control closed form mm3 | Solids matched ; control | Diagnostics (columns only) | Cell verdict |
|---|---|---|---|---|---|---|
| -0.05 | 52.1072/52.1031/52.1062 | 503.429/503.428/503.428 | 503.429 | 1/1/1 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0 | 0/0/0 | 478.37/478.368/478.368 | 478.369 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | inconclusive |
| 0.05 | 0/0/0 | 453.769/453.768/453.768 | 453.768 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.1 | 0/0/0 | 429.631/429.63/429.63 | 429.631 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.15 | 0/0/0 | 405.963/405.961/405.961 | 405.962 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |
| 0.2 | 0/0/0 | 382.767/382.766/382.766 | 382.766 | 0/0/0 ; 1/1/1 | errors 0 of 6, warnings 0 of 6 | proven |

- M20 left c=-0.05: inconclusive: c = -0.05 mm: inconclusive by definition (D-11)
- M20 left c=0: inconclusive: c = 0 mm: inconclusive by definition (D-11)

#### Falsifiability (D-14)

- M2: falsifiable on both hands
- M2 right: excluded clearances 0.1, 0.2
- M2 left: excluded clearances 0.1, 0.2
- M2: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M2 right: sensitivity (c = -0.05) ok
- M2 left: sensitivity (c = -0.05) ok
- M2.5: falsifiable on both hands
- M2.5 right: excluded clearances 0.1
- M2.5 left: excluded clearances 0.1
- M2.5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M2.5 right: sensitivity (c = -0.05) ok
- M2.5 left: sensitivity (c = -0.05) ok
- M3: falsifiable on both hands
- M3 right: excluded clearances 0.05, 0.15
- M3 left: excluded clearances 0.05, 0.15
- M3: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M3 right: sensitivity (c = -0.05) ok
- M3 left: sensitivity (c = -0.05) ok
- M3.5: falsifiable on both hands
- M3.5 right: excluded clearances none
- M3.5 left: excluded clearances none
- M3.5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M3.5 right: sensitivity (c = -0.05) ok
- M3.5 left: sensitivity (c = -0.05) ok
- M4: falsifiable on both hands
- M4 right: excluded clearances 0.05
- M4 left: excluded clearances 0.05
- M4: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M4 right: sensitivity (c = -0.05) ok
- M4 left: sensitivity (c = -0.05) ok
- M5: falsifiable on both hands
- M5 right: excluded clearances 0.05
- M5 left: excluded clearances 0.05
- M5: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M5 right: sensitivity (c = -0.05) ok
- M5 left: sensitivity (c = -0.05) ok
- M6: falsifiable on both hands
- M6 right: excluded clearances none
- M6 left: excluded clearances none
- M6: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M6 right: sensitivity (c = -0.05) ok
- M6 left: sensitivity (c = -0.05) ok
- M7: falsifiable on both hands
- M7 right: excluded clearances 0.05
- M7 left: excluded clearances 0.05
- M7: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M7 right: sensitivity (c = -0.05) ok
- M7 left: sensitivity (c = -0.05) ok
- M8: falsifiable on both hands
- M8 right: excluded clearances none
- M8 left: excluded clearances none
- M8: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M8 right: sensitivity (c = -0.05) ok
- M8 left: sensitivity (c = -0.05) ok
- M10: falsifiable on both hands
- M10 right: excluded clearances 0.05, 0.1
- M10 left: excluded clearances 0.05, 0.1
- M10: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M10 right: sensitivity (c = -0.05) ok
- M10 left: sensitivity (c = -0.05) ok
- M12: falsifiable on both hands
- M12 right: excluded clearances 0.05
- M12 left: excluded clearances 0.05
- M12: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M12 right: sensitivity (c = -0.05) ok
- M12 left: sensitivity (c = -0.05) ok
- M14: falsifiable on both hands
- M14 right: excluded clearances 0.1
- M14 left: excluded clearances 0.1
- M14: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M14 right: sensitivity (c = -0.05) ok
- M14 left: sensitivity (c = -0.05) ok
- M16: falsifiable on both hands
- M16 right: excluded clearances none
- M16 left: excluded clearances none
- M16: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M16 right: sensitivity (c = -0.05) ok
- M16 left: sensitivity (c = -0.05) ok
- not falsifiable for size M18 (right, left hand): the escape clause fires
- M18 right: excluded clearances 0.05, 0.1, 0.15, 0.2
- M18 left: excluded clearances 0.05, 0.1, 0.15, 0.2
- M18: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M18 right: sensitivity (c = -0.05) ok
- M18 left: sensitivity (c = -0.05) ok
- M20: falsifiable on both hands
- M20 right: excluded clearances none
- M20 left: excluded clearances none
- M20: mixed-hand pair read violated at every matched pose: yes (4 mixed cells)
- M20 right: sensitivity (c = -0.05) ok
- M20 left: sensitivity (c = -0.05) ok

#### Reference K (reported, not verdict inputs)

| Size | K | c = 0.05 | c = 0.1 | c = 0.15 | c = 0.2 |
|---|---|---|---|---|---|
| M2 | 5 | inconclusive | inconclusive | inconclusive | inconclusive |
| M2 | 10 | proven | inconclusive | inconclusive | inconclusive |
| M6 | 5 | inconclusive | inconclusive | inconclusive | inconclusive |
| M6 | 10 | proven | inconclusive | inconclusive | inconclusive |
| M10 | 5 | inconclusive | proven | proven | proven |
| M10 | 10 | inconclusive | inconclusive | inconclusive | inconclusive |
| M20 | 5 | proven | proven | proven | inconclusive |
| M20 | 10 | inconclusive | inconclusive | inconclusive | inconclusive |

#### Variant rules (reported, never the verdict)

Computed from the same recorded readings. The D-14 column is the verdict; the others are for Phase 5's revision and never feed it (owner ruling R1).

| Cell | D-14 verdict | two of three controls fire in band | seam pose excluded | same-pose c=-0.05 reading as the control |
|---|---|---|---|---|
| M2 right c=0.05 K=3 | proven | yes | yes | yes |
| M2 right c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2 right c=0.15 K=3 | proven | yes | yes | yes |
| M2 right c=0.2 K=3 | inconclusive | NO | NO | yes |
| M2 left c=0.05 K=3 | proven | yes | yes | yes |
| M2 left c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2 left c=0.15 K=3 | proven | yes | yes | yes |
| M2 left c=0.2 K=3 | inconclusive | NO | NO | yes |
| M2.5 right c=0.05 K=3 | proven | yes | yes | yes |
| M2.5 right c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2.5 right c=0.15 K=3 | proven | yes | yes | yes |
| M2.5 right c=0.2 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.05 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.1 K=3 | inconclusive | NO | NO | yes |
| M2.5 left c=0.15 K=3 | proven | yes | yes | yes |
| M2.5 left c=0.2 K=3 | proven | yes | yes | yes |
| M3 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M3 right c=0.1 K=3 | proven | yes | yes | yes |
| M3 right c=0.15 K=3 | inconclusive | NO | NO | yes |
| M3 right c=0.2 K=3 | proven | yes | yes | yes |
| M3 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M3 left c=0.1 K=3 | proven | yes | yes | yes |
| M3 left c=0.15 K=3 | inconclusive | NO | NO | yes |
| M3 left c=0.2 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.05 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.1 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.15 K=3 | proven | yes | yes | yes |
| M3.5 right c=0.2 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.05 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.1 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.15 K=3 | proven | yes | yes | yes |
| M3.5 left c=0.2 K=3 | proven | yes | yes | yes |
| M4 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M4 right c=0.1 K=3 | proven | yes | yes | yes |
| M4 right c=0.15 K=3 | proven | yes | yes | yes |
| M4 right c=0.2 K=3 | proven | yes | yes | yes |
| M4 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M4 left c=0.1 K=3 | proven | yes | yes | yes |
| M4 left c=0.15 K=3 | proven | yes | yes | yes |
| M4 left c=0.2 K=3 | proven | yes | yes | yes |
| M5 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M5 right c=0.1 K=3 | proven | yes | yes | yes |
| M5 right c=0.15 K=3 | proven | yes | yes | yes |
| M5 right c=0.2 K=3 | proven | yes | yes | yes |
| M5 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M5 left c=0.1 K=3 | proven | yes | yes | yes |
| M5 left c=0.15 K=3 | proven | yes | yes | yes |
| M5 left c=0.2 K=3 | proven | yes | yes | yes |
| M6 right c=0.05 K=3 | proven | yes | yes | yes |
| M6 right c=0.1 K=3 | proven | yes | yes | yes |
| M6 right c=0.15 K=3 | proven | yes | yes | yes |
| M6 right c=0.2 K=3 | proven | yes | yes | yes |
| M6 left c=0.05 K=3 | proven | yes | yes | yes |
| M6 left c=0.1 K=3 | proven | yes | yes | yes |
| M6 left c=0.15 K=3 | proven | yes | yes | yes |
| M6 left c=0.2 K=3 | proven | yes | yes | yes |
| M7 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M7 right c=0.1 K=3 | proven | yes | yes | yes |
| M7 right c=0.15 K=3 | proven | yes | yes | yes |
| M7 right c=0.2 K=3 | proven | yes | yes | yes |
| M7 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M7 left c=0.1 K=3 | proven | yes | yes | yes |
| M7 left c=0.15 K=3 | proven | yes | yes | yes |
| M7 left c=0.2 K=3 | proven | yes | yes | yes |
| M8 right c=0.05 K=3 | proven | yes | yes | yes |
| M8 right c=0.1 K=3 | proven | yes | yes | yes |
| M8 right c=0.15 K=3 | proven | yes | yes | yes |
| M8 right c=0.2 K=3 | proven | yes | yes | yes |
| M8 left c=0.05 K=3 | proven | yes | yes | yes |
| M8 left c=0.1 K=3 | proven | yes | yes | yes |
| M8 left c=0.15 K=3 | proven | yes | yes | yes |
| M8 left c=0.2 K=3 | proven | yes | yes | yes |
| M10 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M10 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M10 right c=0.15 K=3 | proven | yes | yes | yes |
| M10 right c=0.2 K=3 | proven | yes | yes | yes |
| M10 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M10 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M10 left c=0.15 K=3 | proven | yes | yes | yes |
| M10 left c=0.2 K=3 | proven | yes | yes | yes |
| M12 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M12 right c=0.1 K=3 | proven | yes | yes | yes |
| M12 right c=0.15 K=3 | proven | yes | yes | yes |
| M12 right c=0.2 K=3 | proven | yes | yes | yes |
| M12 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M12 left c=0.1 K=3 | proven | yes | yes | yes |
| M12 left c=0.15 K=3 | proven | yes | yes | yes |
| M12 left c=0.2 K=3 | proven | yes | yes | yes |
| M14 right c=0.05 K=3 | proven | yes | yes | yes |
| M14 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M14 right c=0.15 K=3 | proven | yes | yes | yes |
| M14 right c=0.2 K=3 | proven | yes | yes | yes |
| M14 left c=0.05 K=3 | proven | yes | yes | yes |
| M14 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M14 left c=0.15 K=3 | proven | yes | yes | yes |
| M14 left c=0.2 K=3 | proven | yes | yes | yes |
| M16 right c=0.05 K=3 | proven | yes | yes | yes |
| M16 right c=0.1 K=3 | proven | yes | yes | yes |
| M16 right c=0.15 K=3 | proven | yes | yes | yes |
| M16 right c=0.2 K=3 | proven | yes | yes | yes |
| M16 left c=0.05 K=3 | proven | yes | yes | yes |
| M16 left c=0.1 K=3 | proven | yes | yes | yes |
| M16 left c=0.15 K=3 | proven | yes | yes | yes |
| M16 left c=0.2 K=3 | proven | yes | yes | yes |
| M18 right c=0.05 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.1 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.15 K=3 | inconclusive | yes | NO | yes |
| M18 right c=0.2 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.05 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.1 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.15 K=3 | inconclusive | yes | NO | yes |
| M18 left c=0.2 K=3 | inconclusive | yes | NO | yes |
| M20 right c=0.05 K=3 | proven | yes | yes | yes |
| M20 right c=0.1 K=3 | proven | yes | yes | yes |
| M20 right c=0.15 K=3 | proven | yes | yes | yes |
| M20 right c=0.2 K=3 | proven | yes | yes | yes |
| M20 left c=0.05 K=3 | proven | yes | yes | yes |
| M20 left c=0.1 K=3 | proven | yes | yes | yes |
| M20 left c=0.15 K=3 | proven | yes | yes | yes |
| M20 left c=0.2 K=3 | proven | yes | yes | yes |

**Verdict:** not a pass: see the sections above
```

**What this shows / what it does not.** The verdict is a deterministic function of the committed records, and re-running it reproduces the campaign log's verdict exactly. It interprets nothing: the rules that produced it are the pre-registered ones in `02-SPIKE.md` (Rules, Escape clause). Reading of the verdict is in `02-SPIKE.md` (Results, Verdict), by citation.
