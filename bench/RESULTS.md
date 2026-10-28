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

## Coverage floor (Phase 3)

Measured on the Phase 3 suite (843 tests collected, 60 `grid` cells deselected by `addopts`:
`test_bench` 449, `test_api` 88, `test_pr_land` 58, `test_thread_maths` 50, `test_cli` 37,
`test_params` 35, `test_solid` 31, `test_skip_tokens` 27, `test_pool` 17, `test_parity` 17,
`test_calc` 15, `test_records` 13, `test_grid` 6), 2026-10-10, by spur L34's rule as Phase 1
recorded it: one serial run and three `-n 8` runs, the floor being `floor(L - max(0.25, S))` with
L the lowest of the four totals and S the spread (max minus min) of the three `-n 8` totals. This
is a floor on what the suite covers today, not a statement that the code is correct to that
fraction.

Host: Apple M5 Max, 18 CPUs, 64 GiB RAM, macOS 27.0.1 (Darwin 27.0.0), Python 3.12.15,
pytest-cov 7.1.0, pytest-xdist 3.8.0, native arm64 (no container). It is not the host of the
Phase 1 entry (an M2 Max). Other applications were running on it, so it was not idle; `uptime`
immediately before each run read:

| Run | Command | Load averages (1, 5, 15 min) | TOTAL | Wall |
|---|---|---|---|---|
| serial | `.venv/bin/python -m pytest -n0 --cov --cov-report=term --cov-fail-under=0` | 6.59, 4.94, 4.72 | 96.66 % | 108.15 s |
| -n 8 (1) | `.venv/bin/python -m pytest -n 8 --cov --cov-report=term --cov-fail-under=0` | 3.71, 4.26, 4.47 | 97.02 % | 35.96 s |
| -n 8 (2) | same | 5.27, 4.62, 4.59 | 96.66 % | 36.77 s |
| -n 8 (3) | same | 6.92, 5.11, 4.77 | 97.02 % | 35.87 s |

L = 96.66 (the serial run and `-n 8` run 2, equal). S = 0.36 (97.02 - 96.66). Floor =
floor(96.66 - max(0.25, 0.36)) = floor(96.30) = **96**, set as `fail_under` in `pyproject.toml`
(it was 94, from the Phase 1 entry above).

The 0.36 between runs is `pool.py` again, as in Phase 1: the serial run and `-n 8` run 2 missed 3
of its 56 lines (95.31 %), runs 1 and 3 covered it fully (100.00 %). In Phase 1 all three `-n 8`
runs covered it, so this time the loss was not limited to the serial run; the cause was not
isolated here (spur's Pitfall 13), and the rule already takes the lowest total. Every other
module reads the same in all four runs:

| Module | Cover |
|---|---|
| `__init__.py` | 71.43 % |
| `__main__.py` | 0.00 % |
| `app.py` | 97.07 % |
| `build_errors.py` | 100.00 % |
| `calc/__init__.py` | 100.00 % |
| `calc/thread.py` | 100.00 % |
| `cli.py` | 96.75 % |
| `params.py` | 97.78 % |
| `pool.py` | 95.31 % in the serial run and `-n 8` run 2, 100.00 % in `-n 8` runs 1 and 3 |
| `records.py` | 94.03 % |
| `solid/__init__.py` | 94.50 % |
| `solid/bolt.py` | 100.00 % |
| `solid/helical.py` | 100.00 % |

`PYTEST_WORKERS` is 8, spur L34's knee, not re-measured for screw. `make test` runs
`-n 8 --cov`: the 36 s above is pytest's own time with coverage on, against 108 s serial.
The `grid` cells are not in these totals; `make grid` runs them with `--no-cov`.

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


## Thread grid tier (Phase 3)

The slow tier of SC4 (D-14): `tests/test_grid.py` builds every row of the 02 D-03 corpus (15
sizes, both hands, rod and void at `VOID_CLEARANCE` 0.20 mm, every integer-mm and integer-turn
length up to min(10 d, 200 mm), 7160 rows in all) with `screw.solid.helical.thread` at K = 3 and
judges it with `check_solid` against the closed form, and checks that the end faces sit at
z = 0 and z = length to 1e-6 mm. `make grid [SIZE=M6]` runs it locally and
`.github/workflows/grid.yml` runs one job per size; neither is in `make verify` or the required
jobs. This is a harness check of the slow tier, not a bound; macOS arm64, not linux/amd64; the
first CI dispatch after merge is recorded here the same way.

Two shards ran before the PR, the two sizes where the sub-`MIN_TAIL_MM` tail fold fires
(03-RESEARCH: 14 of 82 and 17 of 92 lengths). Run on HEAD `08776d30045b88e873fb8cbcecdea077df5049b5`
plus the uncommitted grid files, 2026-10-10 (UTC). Host: Apple M5 Max, 18 CPUs, arm64, 64.0 GiB
RAM, macOS 27.0.1 (`bench.machine_facts()`: `18 CPUs, arm64, 64.0 GiB RAM`), Python 3.12.15,
cadquery 2.8.0, cadquery-ocp 7.9.3.1.1, pytest-xdist 3.8.0. Other work was running on the host,
so it was not idle; `uptime` immediately before and after each run:

| Shard | Command | Load before (1, 5, 15 min) | Load after | Rows built | Failures | Wall (pytest) |
|---|---|---|---|---|---|---|
| M3.5 | `make grid SIZE=M3.5` (`pytest -m grid -n 8 --no-cov -k 'M3.5-'`) | 2.56, 5.31, 4.08 | 4.42, 5.13, 4.18 | 4 cells x 82 = 328 | none | 131.89 s |
| M4 | `make grid SIZE=M4` (`pytest -m grid -n 8 --no-cov -k 'M4-'`) | 4.06, 5.04, 4.15 | 4.79, 4.92, 4.24 | 4 cells x 92 = 368 | none | 148.15 s |

Both reported `4 passed`: every row of the four cells was one valid solid inside `T_GATE` of the
closed form, and ended at its length. The shard is four cells, so four of the eight workers
carried a cell each and the wall time is that of the longest cell: arithmetic on the table, 131.89
s for 82 rows is 1.6 s a row and 148.15 s for 92 rows 1.6 s a row, against the 2 s a row the
research assumed for the CI sizing (A2). That is this host and this load, not a GitHub runner.
The corpus was not re-picked and no row was skipped.

### GitHub runner: run 38240380994 (2026-10-12)

The first run of `.github/workflows/grid.yml` on `main` was not a `workflow_dispatch`, so the
section intro's "first CI dispatch after merge" did not happen that way. It was the workflow's
weekly `schedule` trigger (`cron: "23 3 * * 1"` in grid.yml): same workflow file, same 15-size
matrix, same command. The ref was `main` at `57d05c6c7844a2b0403107f647e5251acc2477eb`, which is
after the Phase 3 merge 66d9393 and before the Phase 4 merge e8df305, so the run speaks for that
commit only. Run URL: https://github.com/halfb00t/screw/actions/runs/38240380994. Created
2026-10-12T11:05:07Z, last updated 2026-10-12T11:34:14Z (29 min 7 s, by subtraction), conclusion
success, 15 of 15 jobs success.

Machine: each shard ran on its own GitHub-hosted `ubuntu-latest` runner (15 distinct runner names
in the jobs API). The "Set up job" log printed `Image: ubuntu-24.04`, `Version: 20261004.327.1`,
and the setup-python cache key carries `Linux-x64-24.04`. Each shard ran 4 pytest-xdist workers
(`created: 4/4 workers` in every log; the Makefile clamps `PYTEST_WORKERS` to the online CPU
count, so 4 is what the runner reported). The logs printed Python 3.12.15, pytest 9.1.1,
cadquery 2.8.0 and cadquery-ocp 7.9.3.1.1. Load is not readable on a hosted runner and was not
recorded. Command per shard: `make grid PYTHON=python SIZE=<size>`, which is
`pytest -m grid -n 4 --no-cov -k '<size>-'` once `make` has created `.venv`. The Wall (pytest)
column is the figure from pytest's own summary line, the Job wall column is the jobs API's
`completed_at` minus `started_at` at 1 s resolution:

| Shard | Rows built | pytest result | Wall (pytest) | Job wall | s a row |
|---|---|---|---|---|---|
| M2 | 4 cells x 60 = 240 | 4 passed | 292.77 s | 5:42 | 4.88 |
| M2.5 | 4 cells x 78 = 312 | 4 passed | 402.10 s | 7:32 | 5.16 |
| M3 | 4 cells x 60 = 240 | 4 passed | 343.20 s | 6:34 | 5.72 |
| M3.5 | 4 cells x 82 = 328 | 4 passed | 256.30 s | 4:59 | 3.13 |
| M4 | 4 cells x 92 = 368 | 4 passed | 470.87 s | 8:42 | 5.12 |
| M5 | 4 cells x 100 = 400 | 4 passed | 556.78 s | 10:08 | 5.57 |
| M6 | 4 cells x 60 = 240 | 4 passed | 327.15 s | 6:17 | 5.45 |
| M7 | 4 cells x 70 = 280 | 4 passed | 443.67 s | 8:15 | 6.34 |
| M8 | 4 cells x 128 = 512 | 4 passed | 730.42 s | 13:10 | 5.71 |
| M10 | 4 cells x 133 = 532 | 4 passed | 782.36 s | 13:56 | 5.88 |
| M12 | 4 cells x 171 = 684 | 4 passed | 1030.43 s | 18:05 | 6.03 |
| M14 | 4 cells x 140 = 560 | 4 passed | 736.56 s | 13:08 | 5.26 |
| M16 | 4 cells x 160 = 640 | 4 passed | 1129.03 s | 19:44 | 7.06 |
| M18 | 4 cells x 216 = 864 | 4 passed | 1354.47 s | 23:22 | 6.27 |
| M20 | 4 cells x 240 = 960 | 4 passed | 1686.74 s | 29:03 | 7.03 |

Column key: Wall (pytest) is the build-and-gate time alone. Job wall is the number
`timeout-minutes: 120` bounds (a job-level setting, `grid.yml`); it adds runner set-up, checkout, setup-python with its pip cache
restore, the venv creation and dependency install `make grid` does before pytest, the kernel-pair
print and the post steps; on this table it exceeds Wall (pytest) by 42.7 s (M3.5) to 59.6 s (M8)
per shard, arithmetic on the two columns with the job wall at 1 s resolution. The `make grid`
step's own time is a third number and is not recorded here. s a row is Wall (pytest) divided by
the rows of one cell: four cells run on four workers, so a shard's wall is its slowest cell's,
and all four cells of a size have the same number of rows.

**What this shows / what it does not.** All 60 cells, 7160 rows, passed the THRD-04 gate on a
GitHub runner, nothing was skipped and the corpus was not re-picked. The slowest shard, M20, took
1686.74 s of pytest wall and 29:03 (1743 s) of job wall against `timeout-minutes: 120` (7200 s):
1686.74 / 7200 = 0.234 and 1743 / 7200 = 0.242. The runner's cost per row ran from 3.13 s (M3.5)
to 7.06 s (M16), against the 2 s a row the research assumed (A2) and the 1.6 s a row the local
shards above measured on an 18-CPU host at `-n 8`. The limits: it is one run, on one runner per
shard, with load unknown; the hosted runner's hardware is GitHub's to change; and it is a harness
record, not a bound (L07). grid.yml's `timeout-minutes` and its "UNVERIFIED" sizing comment are
unchanged by this entry, and changing them is the owner's call.


## Head fuse probe (Phase 4, D-03)

Phase 2 built no head (02 D-08), so nothing had measured what a hex head and a plain shank fused
to the shipped thread do to the solid count, validity, volume, mesh closedness and export size.
D-03 asks for that record before any plan fixes an expectation about the fused bolt, so this is
it: `bench/head_fuse.py` builds each case through the shipped `screw.solid.bolt.thread` and
`assemble` from a `BoltParams`: the thread (z 0 to t), then the plain shank cylinder (t to length,
only when length exceeds t) fused on, then the hex prism of across-flats `s` and height `k`
(length to length + k), the product's own order, `Shape.fuse` one part at a time and no `clean()`.
The first run (2026-10-11, `d876dbd`) fused shank and head together before the thread, the reverse
order, so it was evidence for a different boolean sequence (04-REVIEW WR-01); the table below is the
2026-10-12 re-run through the shipped builder, and every geometry column (solids, validity, both
volume errors, z extent, triangles, bytes, open edges, head+shank bytes) is identical to that first
run; only `build+fuse s` and peak RSS moved. It then judges
the whole part against the closed form `section_area(d, P) t + pi (d/2)^2 (length - t) +
(sqrt(3)/2) s^2 k` with `precise_volume`, and meshes it at both `TESSELLATION` qualities.

Command: `.venv/bin/python -m bench.head_fuse`. Run on HEAD `979168d5d68009c113ae1dab0b672057efe38c28`
plus the uncommitted probe edit (`bench/head_fuse.py` through the shipped builder), 2026-10-12 (UTC).
Host: `bench.machine_facts()`: `12 CPUs, arm64, 32.0 GiB RAM`, macOS 27.0.1, Python 3.12.13, cadquery
2.8.0, cadquery-ocp 7.9.3.1.1. Load reading before the run: 2.49 at 2026-10-12T08:38:23+00:00;
after: 5.27 at 2026-10-12T08:39:08+00:00 (the second one includes the run's own meshing load,
`exportStl` uses every core). Wall time of the whole run 47.0 s (`time -p`: real 46.97, user 115.60).

| Case | build+fuse s | solids | isValid | whole-part rel. volume error | bare-thread rel. volume error | z extent | triangles preview / fine | bytes preview / fine | open edges preview / fine | head+shank fine bytes | peak RSS so far (bytes, macOS) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 x 4 | 0.10 | 1 | True | -1.58e-06 | -4.92e-06 | -0.0000 to 5.4000 | 7720 / 62920 | 386084 / 3146084 | 0 / 0 | 1084 | 731709440 |
| M6 x 20 | 0.15 | 1 | True | +4.95e-08 | +9.71e-10 | -0.0000 to 24.0000 | 31584 / 209692 | 1579284 / 10484684 | 0 / 0 | 1084 | 1068941312 |
| M6 x 30 | 0.27 | 1 | True | -7.82e-08 | -7.26e-08 | -0.0000 to 34.0000 | 29016 / 181900 | 1450884 / 9095084 | 0 / 0 | 26284 | 1102839808 |
| M10 x 80 | 0.25 | 1 | True | -7.66e-08 | +1.74e-07 | -0.0000 to 86.4000 | 31444 / 415930 | 1572284 / 20796584 | 0 / 0 | 26284 | 1471873024 |
| M16 x 160 | 0.24 | 1 | True | -5.56e-08 | +2.60e-07 | -0.0000 to 170.0000 | 72000 / 764052 | 3600084 / 38202684 | 0 / 0 | 26284 | 1919844352 |
| M20 x 200 | 0.44 | 1 | True | -1.83e-07 | -2.13e-07 | -0.0000 to 212.5000 | 446414 / 2898906 | 22320784 / 144945384 | 0 / 0 | 1084 | 4226596864 |
| M6 x 30 left-hand | 0.27 | 1 | True | -7.82e-08 | -7.26e-08 | -0.0000 to 34.0000 | 22792 / 136080 | 1139684 / 6804084 | 0 / 0 | 26284 | 4226596864 |

Columns: `build+fuse s` is thread, shank, head and the fuses, nothing else. The two volume errors are
signed relative errors of `precise_volume` against the closed form of the whole part and against
`section_area(d, P) t` for the bare thread. `z extent` is the bounding box (the `-0.0000` is the
kernel's bounding-box tolerance, 1e-7 mm). Open edges come from `stl_check` on both meshes.
`head+shank fine bytes` is the fine STL of the head and shank fused without the thread (the head
alone where the thread runs to the head: M2 x 4, M6 x 20, M20 x 200). `peak RSS so far` is
`ru_maxrss` after the case, which is the peak of the whole process so far, so a row reads the
largest case run before it and not its own (the left-hand row reads M20 x 200's peak).

**What this shows / what it does not.** Every case is one valid solid, the whole-part volume
error is at most 1.6e-06 against `T_GATE` 9e-05 (the bare-thread error at most 4.9e-06), z ends
at length + k, and both meshes of every case have zero open edges. The head and shank add 1.1 to
26.3 KB to a fine STL, against 3.1 to 145 MB for the whole fine STL (nearly all of it the thread). This is a probe: single runs, macOS
arm64, load not controlled (2.83 before, so the host was not idle), not a bound and not
linux/amd64. The head values (`s`, `k`) and the thread lengths `t` of the cases are UNVERIFIED
preview readings used as probe inputs, not table rows. Phase 7 re-sweeps on linux/amd64
(OPER-02).


## End-cut probe (Phase 5, D-10)

Phase 4 left both thread ends plain (04 D-01, D-02), and Phase 5 adds a tip cone on the bolt, a
fillet ring under the head, and a countersink and a face chamfer on the nut before ISO 4753 and
ISO 4032 are read. Nothing had measured whether those cutters keep the solid count, validity, mesh
closedness and export size, or whether the volume gate can see them. D-10 asks for that record before
any end model or tolerance is fixed, so this is it: `bench/end_cuts.py` builds every case through the
shipped `screw.solid.helical.thread` (rod and void) and the shipped `screw.solid.bolt.thread` and
`assemble`, never a copy, adds the cutters (the tip as the `2026-10-08-a-trim` intersect recipe, the
ring fused under the head, the countersinks and chamfers cut from the nut), and judges each cut against
a kernel-free oracle of the volume it removes or adds (05-RESEARCH F4; `tests/test_bench.py` checks each
oracle against an identity that does not use it). Three comparisons per row: the **piece error** is the
kernel's removed or added volume against the oracle piece, relative to the piece; the **whole error** is
`precise_volume` of the finished part against its closed form less (or plus) the oracle pieces; the
open edges come from `stl_check` on the preview and the fine mesh.

Command: `.venv/bin/python -m bench.end_cuts` (one run, exit 0). Run on HEAD
`54a0ca5a077c23d5c3267762c866719b75f18ad4` plus the uncommitted probe module and its oracle tests (both
land in the commit that adds this entry), 2026-10-14 (UTC). Host: `bench.machine_facts()`: `18 CPUs,
arm64, 64.0 GiB RAM`, macOS 27.0.1, Python 3.12.15, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1. Load reading
before the run: 3.84 at 2026-10-14T12:04:13+00:00; after: 6.79 at 2026-10-14T12:05:48+00:00 (the second
includes the run's own meshing load). Wall time of the whole run 96.4 s (`time -p`: real 96.39, user
279.38, sys 30.22).

Every angle, radius, `s`, `m` and `r` below is an UNVERIFIED probe input chosen to span the sizes, not
a table row and not a clause of ISO 4753 or ISO 4032: tip cones at 30 and 45 degrees from the face,
meeting it at the minor radius; countersinks of 90 degrees included from radius `d/2 + c + P/2` at the
face, a crossing cone ending 0.3 thread depths below the root radius and the grazing cone ending exactly
on it; face chamfers of 30 degrees from the face starting at the inscribed circle `s/2`; nut clearance
0.1 mm; nut `s` 4.0, 10.0, 16.0, 30.0 for M2, M6, M10, M20 with `m` the spike's preview heights 1.6, 5.2,
8.4, 18.0; ring radii 0.25, 0.4, 0.8; the bolts' `s`, `k` and `t` the Head fuse probe's preview readings
(M20 x 100: `s` 30, `k` 12.5, `t` 46). The two bolt-tip rows use 30 degrees on M6 x 20 and 45 on
M10 x 80. Bare threads are 8 pitches long; the controls use M6 and M10 rods of 60 and 200 mm.

| Case | build+cut s | solids | isValid | piece rel. error | whole rel. error | open edges preview / fine | fine mesh s | peak RSS so far (bytes, macOS) |
|---|---|---|---|---|---|---|---|---|
| tip 30 M2 right | 0.16 | 1 | True | -7.71e-05 | -3.81e-06 | 0 / 0 | 0.07 | 695697408 |
| tip 45 M2 right | 0.18 | 1 | True | +2.74e-03 | -1.97e-05 | 0 / 0 | 0.06 | 722501632 |
| tip 30 M6 right | 0.19 | 1 | True | +2.34e-05 | +4.15e-07 | 0 / 0 | 0.16 | 846577664 |
| tip 45 M6 right | 0.20 | 1 | True | +2.06e-05 | +3.83e-07 | 0 / 0 | 0.13 | 881229824 |
| tip 30 M10 right | 0.21 | 1 | True | +2.60e-05 | +3.80e-07 | 0 / 0 | 0.32 | 1122959360 |
| tip 45 M10 right | 0.22 | 1 | True | +2.01e-05 | +3.59e-07 | 0 / 0 | 0.28 | 1151811584 |
| tip 30 M20 right | 0.24 | 1 | True | +3.50e-06 | +5.32e-07 | 0 / 0 | 0.52 | 1378271232 |
| tip 45 M20 right | 0.22 | 1 | True | +1.15e-04 | +1.53e-07 | 0 / 0 | 0.46 | 1398931456 |
| tip 30 M2 left | 0.15 | 1 | True | +8.98e-04 | -7.02e-06 | 0 / 0 | 0.06 | 1398931456 |
| tip 45 M2 left | 0.18 | 1 | True | +1.28e-03 | -1.14e-05 | 0 / 0 | 0.05 | 1398931456 |
| tip 30 M6 left | 0.18 | 1 | True | +1.47e-05 | +4.38e-07 | 0 / 0 | 0.11 | 1398931456 |
| tip 45 M6 left | 0.21 | 1 | True | +1.40e-05 | +4.14e-07 | 0 / 0 | 0.10 | 1398931456 |
| tip 30 M10 left | 0.20 | 1 | True | +1.66e-05 | +4.02e-07 | 0 / 0 | 0.24 | 1398931456 |
| tip 45 M10 left | 0.21 | 1 | True | +1.59e-05 | +3.76e-07 | 0 / 0 | 0.23 | 1398931456 |
| tip 30 M20 left | 0.23 | 1 | True | -2.07e-05 | +5.79e-07 | 0 / 0 | 0.40 | 1398931456 |
| tip 45 M20 left | 0.22 | 1 | True | +5.44e-05 | +3.57e-07 | 0 / 0 | 0.36 | 1398931456 |
| tip 30 bolt M6 x 20 | 0.29 | 1 | True | -5.17e-07 | -2.00e-08 | 0 / 0 | 0.25 | 1398931456 |
| tip 45 bolt M10 x 80 | 0.38 | 1 | True | +5.80e-05 | -1.48e-07 | 0 / 0 | 0.42 | 1595490304 |
| ring r 0.25 M6 x 30 | 0.23 | 1 | True | +1.77e-05 | -7.41e-08 | 0 / 0 | 0.20 | 1595490304 |
| ring r 0.4 M10 x 80 | 0.21 | 1 | True | -1.50e-05 | -7.88e-08 | 0 / 0 | 0.39 | 1626423296 |
| ring r 0.8 M20 x 100 | 0.18 | 1 | True | -1.63e-04 | -1.64e-08 | 0 / 0 | 0.69 | 1950416896 |
| ring r 0.25 M6 x 30 left | 0.23 | 1 | True | +1.77e-05 | -7.41e-08 | 0 / 0 | 0.15 | 1950416896 |
| nut M2 right none | 0.12 | 1 | True | - | +1.70e-06 | 0 / 0 | 0.05 | 1950416896 |
| nut M2 right countersinks | 0.36 | 1 | True | +5.00e-06 | +1.56e-06 | 0 / 0 | 0.04 | 1950416896 |
| nut M2 right face chamfers | 0.19 | 1 | True | -1.49e-07 | +1.72e-06 | 0 / 0 | 0.05 | 1950416896 |
| nut M2 right both | 0.42 | 1 | True | +3.98e-06 | +1.58e-06 | 0 / 0 | 0.04 | 1950416896 |
| nut M6 right none | 0.16 | 1 | True | - | -1.79e-07 | 0 / 0 | 0.12 | 1950416896 |
| nut M6 right countersinks | 0.47 | 1 | True | -1.92e-06 | -1.05e-07 | 0 / 0 | 0.11 | 1950416896 |
| nut M6 right face chamfers | 0.26 | 1 | True | +4.72e-07 | -1.83e-07 | 0 / 0 | 0.13 | 1950416896 |
| nut M6 right both | 0.55 | 1 | True | -1.68e-06 | -1.05e-07 | 0 / 0 | 0.13 | 1950416896 |
| nut M10 right none | 0.17 | 1 | True | - | -2.09e-07 | 0 / 0 | 0.28 | 1950416896 |
| nut M10 right countersinks | 0.50 | 1 | True | -2.83e-06 | -1.08e-07 | 0 / 0 | 0.22 | 1950416896 |
| nut M10 right face chamfers | 0.23 | 1 | True | +5.65e-07 | -2.15e-07 | 0 / 0 | 0.26 | 1950416896 |
| nut M10 right both | 0.57 | 1 | True | -2.51e-06 | -1.03e-07 | 0 / 0 | 0.23 | 1950416896 |
| nut M20 right none | 0.18 | 1 | True | - | +1.96e-08 | 0 / 0 | 0.43 | 1950416896 |
| nut M20 right countersinks | 0.58 | 1 | True | +5.58e-06 | -1.48e-07 | 0 / 0 | 0.37 | 1950416896 |
| nut M20 right face chamfers | 0.26 | 1 | True | -1.51e-07 | +2.07e-08 | 0 / 0 | 0.43 | 1950416896 |
| nut M20 right both | 0.65 | 1 | True | +4.62e-06 | -1.51e-07 | 0 / 0 | 0.38 | 1950416896 |
| nut M2 left none | 0.12 | 1 | True | - | +1.70e-06 | 0 / 0 | 0.05 | 1950416896 |
| nut M2 left countersinks | 0.36 | 1 | True | +5.00e-06 | +1.56e-06 | 0 / 0 | 0.03 | 1950416896 |
| nut M2 left face chamfers | 0.18 | 1 | True | -1.49e-07 | +1.72e-06 | 0 / 0 | 0.05 | 1950416896 |
| nut M2 left both | 0.43 | 1 | True | +3.98e-06 | +1.58e-06 | 0 / 0 | 0.03 | 1950416896 |
| nut M6 left none | 0.16 | 1 | True | - | -1.79e-07 | 0 / 0 | 0.10 | 1950416896 |
| nut M6 left countersinks | 0.47 | 1 | True | -2.80e-06 | -6.84e-08 | 0 / 0 | 0.09 | 1950416896 |
| nut M6 left face chamfers | 0.25 | 1 | True | +4.72e-07 | -1.83e-07 | 0 / 0 | 0.10 | 1950416896 |
| nut M6 left both | 0.53 | 1 | True | -2.43e-06 | -6.73e-08 | 0 / 0 | 0.09 | 1950416896 |
| nut M10 left none | 0.15 | 1 | True | - | -2.09e-07 | 0 / 0 | 0.23 | 1950416896 |
| nut M10 left countersinks | 0.49 | 1 | True | -3.33e-06 | -8.81e-08 | 0 / 0 | 0.19 | 1950416896 |
| nut M10 left face chamfers | 0.23 | 1 | True | +5.65e-07 | -2.15e-07 | 0 / 0 | 0.22 | 1950416896 |
| nut M10 left both | 0.57 | 1 | True | -2.79e-06 | -8.97e-08 | 0 / 0 | 0.20 | 1950416896 |
| nut M20 left none | 0.18 | 1 | True | - | +1.96e-08 | 0 / 0 | 0.37 | 1950416896 |
| nut M20 left countersinks | 0.60 | 1 | True | +5.00e-06 | -1.31e-07 | 0 / 0 | 0.32 | 1950416896 |
| nut M20 left face chamfers | 0.26 | 1 | True | -1.51e-07 | +2.07e-08 | 0 / 0 | 0.38 | 1950416896 |
| nut M20 left both | 0.81 | 1 | True | +3.82e-06 | -1.22e-07 | 0 / 0 | 0.31 | 1950416896 |
| nut M6 right countersinks grazing | 0.60 | 1 | True | - | -1.28e-07 | 8 / 4 | 7.02 | 1950416896 |
| nut M6 left countersinks grazing | 0.56 | 1 | True | - | -9.07e-08 | 9 / 752 | 0.09 | 1950416896 |
| control tip cut skipped M6 L60 | 0.13 | 1 | True | -1.00e+00 | +3.55e-04 | 0 / - | - | 1950416896 |
| control tip 45 built, 30 expected M6 L60 | 0.43 | 1 | True | +7.32e-01 | -2.61e-04 | 0 / - | - | 1950416896 |
| control tip cut skipped M10 L200 | 0.28 | 1 | True | -1.00e+00 | +1.41e-04 | 0 / - | - | 1950416896 |
| control tip 45 built, 30 expected M10 L200 | 0.76 | 1 | True | +7.33e-01 | -1.05e-04 | 0 / - | - | 1950416896 |
| ring dropped r 0.25 M6 x 60 | 0.19 | 1 | True | -1.00e+00 | -1.32e-04 | 0 / - | - | 1950416896 |
| ring dropped r 0.4 M10 x 200 | 0.18 | 1 | True | -1.00e+00 | -6.55e-05 | 0 / - | - | 1950416896 |

Fine STL of a finished nut (countersinks and chamfers, both faces) at the `FINE_STL_ROWS` cap of the
same (d, pitch, hand) and at the cap + 1 mm, with its gzip level-1 copy, against the 64 MiB (67 108 864
byte) export budget the caps were measured against (`sum / 64 MiB` above 1.000 is over budget):

| Case | build s | solids | isValid | whole rel. error | fine STL bytes | gzip-1 bytes | sum | sum / 64 MiB | fine mesh s | gzip s | peak RSS so far (bytes, macOS) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nut M10 right m 56 | 0.88 | 1 | True | +6.89e-08 | 43774484 | 20407813 | 64182297 | 0.956 | 0.79 | 0.32 | 1950416896 |
| nut M10 right m 57 | 0.91 | 1 | True | +3.61e-08 | 44518584 | 20760539 | 65279123 | 0.973 | 0.80 | 0.33 | 1950416896 |
| nut M20 right m 64 | 0.85 | 1 | True | -2.21e-07 | 42345984 | 19456785 | 61802769 | 0.921 | 0.86 | 0.31 | 2072117248 |
| nut M20 right m 65 | 0.86 | 1 | True | +2.60e-07 | 43056184 | 19762089 | 62818273 | 0.936 | 0.88 | 0.31 | 2079916032 |
| nut M20 left m 91 | 0.94 | 1 | True | -1.13e-07 | 45604884 | 21713461 | 67318345 | 1.003 | 0.96 | 0.35 | 2110341120 |
| nut M20 left m 92 | 0.99 | 1 | True | -2.52e-08 | 46292084 | 22059153 | 68351237 | 1.019 | 1.01 | 0.35 | 2111094784 |

Positive controls: a tip cut skipped, a 45 degree cone built where 30 is expected, a ring dropped, each
judged by the piece comparison and by the whole-part comparison at `T_GATE` 9e-05. The piece gate used
for the flag is the arithmetic of the rule R11 as proposed to the owner (10 times the largest honest
piece error rounded up to one significant figure), printed here to show what it would flag; it is not
adopted and no tolerance is chosen by this entry:

| Control | piece rel. error | piece flagged at that gate | whole rel. error | whole flagged at T_GATE |
|---|---|---|---|---|
| control tip cut skipped M6 L60 | -1.00e+00 | True | +3.55e-04 | True |
| control tip 45 built, 30 expected M6 L60 | +7.32e-01 | True | -2.61e-04 | True |
| control tip cut skipped M10 L200 | -1.00e+00 | True | +1.41e-04 | True |
| control tip 45 built, 30 expected M10 L200 | +7.33e-01 | True | -1.05e-04 | True |
| ring dropped r 0.25 M6 x 60 | -1.00e+00 | True | -1.32e-04 | True |
| ring dropped r 0.4 M10 x 200 | -1.00e+00 | True | -6.55e-05 | False |

Largest honest piece errors (absolute values; the grazing rows and the controls are not honest rows):

```
largest |piece error| tip: 2.737e-03 over 16 rows
largest |piece error| tip-bolt: 5.803e-05 over 2 rows
largest |piece error| ring: 1.627e-04 over 4 rows
largest |piece error| nut: 5.578e-06 over 24 rows
largest |piece error| overall: 2.737e-03 over 46 rows
```

Columns: `build+cut s` is the rod or void, the cutters and the fuse, nothing else (the volume estimates and
the meshes are after it). `piece rel. error` is `-` where no piece exists (the no-cutter nut) or none was
computed (the grazing rows). `peak RSS so far` is `ru_maxrss` after the case, the peak of the whole
process so far, so a row reads the largest case run before it and not its own. `open edges` is `-` where
that quality was not meshed (the controls mesh the preview only; the cap rows do not read the fine mesh).

**What this shows / what it does not.** All 54 honest rows (16 bare tips, 2 bolt tips, 4 rings, 32 nuts)
are one valid solid with 0 open edges at the preview and the fine mesh, and their whole-part error is at
most 1.97e-05 (tip 45 M2 right) against `T_GATE` 9e-05. The largest piece error is 2.737e-03, tip 45
degrees on the M2 right-hand rod, a piece of 0.0444 mm3 whose absolute error is about 1.2e-04 mm3; the
M2 rows set the tip maximum (the next largest tip errors are M2 left 45 and 30 degrees at 1.28e-03 and
8.98e-04, then M20 right 45 degrees at 1.15e-04, and every M6 and M10 tip is at most 2.6e-05), the two bolt tips are at most
5.80e-05, the rings at most 1.63e-04 (M20 x 100, r 0.8) and the 24 nut pieces at most 5.58e-06. The
cutters' piece errors therefore do not grow with the part, the noise is the absolute volume noise of the
kernel on a small piece, and the input of the differential-tolerance ruling is **2.737e-03**, read as one
single-run maximum over 46 rows, not a bound. A cone that ends exactly on the root radius is valid
and has the right volume (M6 grazing: -1.28e-07 right, -9.07e-08 left against the closed form) but
meshes open: 8 open edges at the preview and 4 at the fine mesh on the right-hand nut (fine mesh 7.02 s,
against 0.11 to 0.13 s for the crossing variants of that nut), 9 and 752 on the left-hand nut; neither
`isValid()` nor the volume comparison sees it, which is why every countersink in the nut rows crosses the
root radius and all 32 of those rows are watertight. The positive controls: the piece comparison flags
all six, the whole-part comparison at `T_GATE` flags five of six and does not see the dropped ring on
M10 x 200 (6.55e-05, 0.73 of `T_GATE`), the dilution P8 predicted. The nut fine STL at the caps: a nut of
M10 right at m 56 and 57 and M20 right at m 64 and 65 fits the budget (0.921 to 0.973), including at
cap + 1 where the rod of that length was over it (the rod rows of `2026-10-08-a-grid` at L = 56, 57, 64,
65 are 66 414 767, 67 426 226, 66 578 235 and 70 089 640 bytes for raw plus gzip), while M20 left at
m 91 is already over (67 318 345 bytes, 1.003; the rod at L = 91 was 66 845 877). The cap rows are nut
heights of 56 to 92 mm, far above any nut height read so far (the largest `m` above is the M20 preview
18.0), so they say what the rod caps would do on a nut, not what a nut costs. This is a probe: single
runs, macOS arm64, load not controlled (3.84 before, so the host was not idle), not a bound and not
linux/amd64; every geometry input is an UNVERIFIED preview value and no table value of ISO 4032 or
ISO 4753 is read here. Phase 7 re-sweeps on linux/amd64 (OPER-02).


## M18 control diagnosis (Phase 5, D-08)

The recorded pair campaign (`2026-10-08-a-pair`) read the M18 half-pitch control at theta -2pi/3 (right
hand) and +2pi/3 (left hand) as 0 solids in every same-hand cell, at every clearance from -0.05 to
0.20 mm, so M18 is `inconclusive` on both hands. `05-M18-DIAGNOSIS.md` (on `origin/main` before this
run, blob `9544d6f286d659d4f7cc63ba614bfd43fc7c8d26`, the probe's guard checked it byte for byte)
fixed 36 readings and five predictions before any of them existed. This entry is the one run of them.
Nothing was re-run, and no rule, constant, body, pose, K or the M18 label changed.

Command: `.venv/bin/python -m bench.m18_probe`. HEAD `b19348a974434072accbb6d410e9fb133ebc16ef` (clean
apart from two untracked planning files), 2026-10-20 (UTC). Host: `bench.machine_facts()`: `18 CPUs,
arm64, 64.0 GiB RAM`, Python 3.12, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1. The host is shared with
other sessions and was busy: load1 **9.46** before the first child (13:56:35Z) and **12.85** after the
last (13:57:32Z, includes the run's own load); the probe is non-decisive whatever the load, and
volumes and solid counts do not depend on it. Wall time **59.6 s** (`time`: real 59.588, user 209.34,
four children at a time); each reading took 2.89 to 3.70 s against the 130 s deadline, none timed out
or failed (36 of 36 `built`). The record `bench/results/phase-05/m18-diagnosis.jsonl` (37 lines: the
header and 36 readings) has sha256 `b301560c784d386dd3d680ad2d52e71b674f7355264218ab9cc397dcf0ad8fbc`.
The header's `void` is `null`: the harness controls read as predicted, so the probe is not void.

All 36 readings (cell M18: d 18.0, pitch 2.5, m 15.8, K = 3; the closed form of the control is
336.6316 mm3 at c = 0.10 and 394.0500 mm3 at c = -0.05):

| probe | hand | clearance | theta | delta from failing theta | fuzzy | swapped | outcome | solids | volume mm3 | seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | right | 0.1 | -2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.33 |
| P1 | right | 0.1 | -2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.34 |
| P1 | right | 0.1 | -2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.33 |
| P1 | right | 0.1 | -2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.34 |
| P1 | right | 0.1 | -2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.47 |
| P1 | left | 0.1 | 2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.39 |
| P1 | left | 0.1 | 2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.40 |
| P1 | left | 0.1 | 2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.37 |
| P1 | left | 0.1 | 2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.23 |
| P1 | left | 0.1 | 2.094395 | 0 | none | no | built | 0 | 0.00000 | 3.23 |
| P2 | right | 0.1 | -2.194395 | -0.1 | none | no | built | 1 | 336.63098 | 3.54 |
| P2 | right | 0.1 | -2.104395 | -0.01 | none | no | built | 0 | 0.00000 | 3.34 |
| P2 | right | 0.1 | -2.095395 | -0.001 | none | no | built | 0 | 0.00000 | 3.35 |
| P2 | right | 0.1 | -2.094495 | -0.0001 | none | no | built | 0 | 0.00000 | 3.34 |
| P2 | right | 0.1 | -2.094295 | +0.0001 | none | no | built | 0 | 0.00000 | 3.37 |
| P2 | right | 0.1 | -2.093395 | +0.001 | none | no | built | 0 | 0.00000 | 3.34 |
| P2 | right | 0.1 | -2.084395 | +0.01 | none | no | built | 0 | 0.00000 | 3.21 |
| P2 | right | 0.1 | -1.994395 | +0.1 | none | no | built | 0 | 0.00000 | 3.27 |
| P2 | left | 0.1 | 1.994395 | -0.1 | none | no | built | 0 | 0.00000 | 3.20 |
| P2 | left | 0.1 | 2.084395 | -0.01 | none | no | built | 0 | 0.00000 | 3.14 |
| P2 | left | 0.1 | 2.093395 | -0.001 | none | no | built | 0 | 0.00000 | 3.06 |
| P2 | left | 0.1 | 2.094295 | -0.0001 | none | no | built | 0 | 0.00000 | 3.07 |
| P2 | left | 0.1 | 2.094495 | +0.0001 | none | no | built | 0 | 0.00000 | 3.07 |
| P2 | left | 0.1 | 2.095395 | +0.001 | none | no | built | 0 | 0.00000 | 3.09 |
| P2 | left | 0.1 | 2.104395 | +0.01 | none | no | built | 0 | 0.00000 | 2.95 |
| P2 | left | 0.1 | 2.194395 | +0.1 | none | no | built | 1 | 336.63099 | 3.11 |
| P3 | right | -0.05 | -2.094395 | 0 | none | no | built | 0 | 0.00000 | 2.97 |
| P3 | left | -0.05 | 2.094395 | 0 | none | no | built | 0 | 0.00000 | 2.89 |
| P4a | right | 0.1 | -2.094395 | 0 | 0.0001 | no | built | 0 | 0.00000 | 3.04 |
| P4a | left | 0.1 | 2.094395 | 0 | 0.0001 | no | built | 0 | 0.00000 | 2.96 |
| P4b | right | 0.1 | -2.094395 | 0 | none | yes | built | 0 | 0.00000 | 3.03 |
| P4b | left | 0.1 | 2.094395 | 0 | none | yes | built | 0 | 0.00000 | 2.93 |
| H | right | 0.1 | 0.000000 | (control, not the failing pose) | none | no | built | 1 | 336.63033 | 3.50 |
| H | right | 0.1 | 2.094395 | (control, not the failing pose) | none | no | built | 1 | 336.63005 | 3.62 |
| H | left | 0.1 | -2.094395 | (control, not the failing pose) | none | no | built | 1 | 336.62996 | 3.63 |
| H | left | 0.1 | 0.000000 | (control, not the failing pose) | none | no | built | 1 | 336.63007 | 3.70 |

Predictions, each judged on the readings above:

- **H1 held.** All ten P1 readings (five per hand, each in a fresh process) read 0 solids and 0 mm3.
- **H2 not held.** Of the eight readings at |delta| >= 0.01 rad (delta -0.1, -0.01, +0.01, +0.1 on each
  hand), only two read non-empty, and they are mirror images (the side away from theta 0): delta -0.1
  on the right hand (theta -2.1944, 1 solid, 336.63098 mm3, relative error 2.0e-06 against the closed
  form) and delta +0.1 on the left hand (theta +2.1944, 1 solid, 336.63099 mm3, 1.9e-06). The other
  six read 0 solids (right and left at +-0.01, and +0.1 right, -0.1 left). The four readings at
  |delta| = 1e-4 and 1e-3 read 0 on both hands, which H2 left open.
- **H3 held.** Both P3 readings (c = -0.05, right and left) read 0 solids.
- **H4 held.** The two P4a readings (fuzzy value 1e-4 mm) and the two P4b readings (operands swapped)
  read 0 solids and 0 mm3 on both hands, the recorded empty.
- **H held.** The four harness controls read 1 solid each, at 336.63033, 336.63005, 336.62996 and
  336.63007 mm3, relative errors 3.9e-06 to 5.0e-06 against 336.6316, far inside `PAIR_BAND` (1e-3).

**Finding.** The empty is reproducible on this host and kernel: the failing control read 0 solids in
10 of 10 fresh processes, on both hands as mirror images, at c = 0.10 and at c = -0.05 alike, and it
does not depend on the boolean's fuzzy value or on operand order. It is not local to the one pose: the
empty spans, on each hand, every reading from 0.01 rad on the side away from theta 0 to 0.1 rad on
the side toward theta 0 (a band of at least 0.11 rad; 14 of the 16 P2 readings are empty), and a
healthy reading appears only at 0.1 rad on the away side. One edge of the band therefore lies between
0.01 and 0.1 rad on the away side, and the other lies beyond 0.1 rad on the toward side without being
bracketed by this probe (the next non-empty reading there is the harness control at theta 0, more than
2 rad away).

**What this shows / what it does not.** This is a diagnosis of one cell on one host: it says the
recorded M18 empty is a property of this kernel and the band of poses around the control, and not
noise of the single recorded run, the boolean's tolerance or its operand order. It does not say why
the boolean returns nothing there, locates only one of the band's two edges, and was run once on
macOS arm64 with the host busy. The D-08 escape clause holds: M18 stays `inconclusive` on both hands,
the label is unchanged, and `screw pair` reads `inconclusive` for the M18 nut until a later
pre-registered campaign proves it.


## Pair tier (Phase 5, D-07)

D-07 pre-registered the expected verdict of every recorded pair cell in `tests/data/pair_expected.tsv`
(240 rows: the 15 sizes M2 to M20 with M7 included, K = 3, both hands and the mixed pair, clearances
-0.05 to 0.20 mm), derived from `2026-10-08-a-pair` by the unmodified `cell_verdict` and committed
before this run. This entry is the one run of the full grid on the product's own bodies
(`screw.solid.pair.prove` with `shipped=False`, one child process and a 600 s deadline per cell, the
cell harness of 05-15 including its `s = max(10, d + 2c + 1)` deviation, which `prove` never reads).
Nothing was re-run, no cell was reclassified, and no rule, constant, body, pose, K or table changed.

Command: `make pair` (that is `.venv/bin/python -m pytest -m pair -n 8 --no-cov`). HEAD
`22bcd508f3a5e3a6497143589f0924453a4acd2d` (the M18 diagnosis commit, clean apart from two untracked
planning files), 2026-10-20 (UTC). Host: `bench.machine_facts()` `18 CPUs, arm64, 64.0 GiB RAM`,
Python 3.12.15, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1; **8 xdist workers** (`PYTEST_WORKERS`, the
Makefile's clamp of 8 to the CPU count). This is a record of this host, not a quiet-host timing: the
host is shared with other sessions. `bench.quiet.read_now()` read load1 **5.69** at 14:02:03Z before the
run and **7.53** at 14:19:37Z after it; load1 sampled every 120 s during the run (nine samples) ran
from 5.69 to 28.21 (10.85, 10.67, 28.21, 15.97, 12.70, 11.75, 13.13, 12.95 after the first), the run's
own eight workers included. Wall time **1054.04 s (0:17:34)** by pytest, 17:34.23 by `time`
(user 7487.6 s, 727 % cpu). The per-cell wall seconds sum to 7955.1 s across the 240 cells (smallest
1.65 s, an inconclusive-by-definition cell; largest 150.2 s, `M16-right-c0.05`), against the 600 s
deadline: no cell timed out, crashed or wrote an `error` line.

**Result: 240 of 240 pass.** Every cell's verdict equals its pre-registered verdict: 88 `proven`, 60
`violated` and 92 `inconclusive` expected, and 88, 60 and 92 read. **No cell mismatches the table.**

Per size (each `pair-<size>.jsonl` holds 16 lines, one per cell: id, expected, the `PairReport`, wall
seconds; 240 ids, all distinct):

| size | cells | passed | proven | violated | inconclusive | slowest cell, s | sha256 of `pair-<size>.jsonl` |
|---|---|---|---|---|---|---|---|
| M2 | 16 | 16 | 4 | 4 | 8 | 52.0 (M2-right-c0.05) | `9b4e25f582920ae2f4b65f9c9f6d22e59cdab6c698b0eb216b920d45331991ca` |
| M2.5 | 16 | 16 | 6 | 4 | 6 | 31.6 (M2.5-right-c0.2) | `9514a8279e5d690092c7469a6069399efe237b23f483714235f5f012754c16bf` |
| M3 | 16 | 16 | 4 | 4 | 8 | 26.4 (M3-left-c0.2) | `1e2e2f6d4e13b0d820dfbc5d62e0ef22094f2093e606687f92225892d8aa5659` |
| M3.5 | 16 | 16 | 8 | 4 | 4 | 30.7 (M3.5-left-c0.05) | `f29c9fad7eeb888354cc0d6c87ff6197ea4beccadca4e4e8c1db0dfd01d0db9f` |
| M4 | 16 | 16 | 6 | 4 | 6 | 30.9 (M4-right-c0.05) | `11e73c916a4a71d917dc384f555d72df0da002a41a489ce0a99413a29f668874` |
| M5 | 16 | 16 | 6 | 4 | 6 | 40.6 (M5-right-c0.05) | `b5c0d7e08a2ee2776281bdf79405cac34015e4440df367cb750a3dc9053e38e0` |
| M6 | 16 | 16 | 8 | 4 | 4 | 69.8 (M6-right-c0.1) | `2c3d45dca7de0ed52fb3161d18c316d5c7c730834758e69aba5d2a8c146cdfce` |
| M7 | 16 | 16 | 6 | 4 | 6 | 84.6 (M7-left-c0.05) | `8252b8fe60b36c47dbb95d6c846c583f91945cea901b9940cc10769ebaab491f` |
| M8 | 16 | 16 | 8 | 4 | 4 | 71.5 (M8-right-c0.05) | `4820e9cbdfa01b39419610cbd25e47ddb6a85a6d2098792c6533b2d150502bcb` |
| M10 | 16 | 16 | 4 | 4 | 8 | 76.5 (M10-right-c0.05) | `8966e7c30721b295462085dfb0ad8d6d26724a13963d75fc43f6a9465bf0f5e3` |
| M12 | 16 | 16 | 6 | 4 | 6 | 107.9 (M12-right-c0.05) | `9bd5630ffeb6f1d64b396843516271946e3d2f0674df4741fcfd29d36abe8864` |
| M14 | 16 | 16 | 6 | 4 | 6 | 110.5 (M14-right-c0.05) | `18f87683f409a7f4151ffb37db588766d9dc64fc60157a6d426a0bec38e3ad04` |
| M16 | 16 | 16 | 8 | 4 | 4 | 150.2 (M16-right-c0.05) | `c0629b9ae51e9db58fe841b8bd0828ae7200a531d7e4299d1a2e7247854d698a` |
| M18 | 16 | 16 | 0 | 4 | 12 | 114.6 (M18-right-c0.05) | `91f74e43f3b504245913fa0368e6c48e6a79985df02ae5709c6f9f1169107579` |
| M20 | 16 | 16 | 8 | 4 | 4 | 138.1 (M20-right-c0.05) | `ba27dc1d87f86c3bfe7a9fd43d78977ff7a12bbebe14709bde8bb101a71a87fb` |

**M18.** The recorded M18 empty reproduced inside the grid: all 8 same-hand cells at c = 0.05 to 0.20
read `inconclusive` with the control empty at theta -2.0944 (right hand) or +2.0944 (left hand) and
the other two controls non-empty, which is what the table expected and what the diagnosis entry
above reads at a single cell. The 4 mixed-hand M18 cells read `violated`, the
12 `inconclusive` M18 cells are those 8 plus the 4 cells at c = 0 and c = -0.05, inconclusive by
definition (D-11, 1.7 s each, no boolean). M18 has no `proven` cell, as expected.

**What this shows / what it does not.** On this host and kernel the kernel verdict equals the
recorded one at every one of 240 cells, so the table, the rule and the product's bodies agree with the
recorded campaign; a cell the rule excludes still reads `inconclusive`, and the control gate does what
the diagnosis says for M18. It is one run on macOS arm64 at a busy and varying load, not a bound and
not linux/amd64 (the ubuntu reading is 05-15's single verify cell; the weekly `pair.yml` is the
other platform's grid), and every cell's `m` is the recorded preview value, so it says nothing about
the verified ISO 4032 heights (the next entry).


## Product pair cells (Phase 5, D-07)

The D-07 planner alert asks for product cells wherever the verified ISO 4032 nut height differs from the
height the recorded campaign used: at the row's `m` the product's `screw pair nut` is a different cell
from the recorded one, so it would be predicted from the recorded verdict at the same size, clearance
and hand, committed before it runs, and run through `screw pair nut` in its own process. The prediction
step is a comparison of two tables and needs no kernel, so it was made first, on HEAD
`80aac99` (2026-10-20): the `m` of every size in `tests/data/pair_expected.tsv` (the recorded preview
values, derived from `2026-10-08-a-pair`) against the `m_max` of the same size in
`screw.tables.iso4032.NUTS` (the GOST ISO 4032-2014 rows read in 05-06, owner ruling 2026-10-20), and the
pitch beside it:

| size | recorded `m` (pair table) | ISO 4032 row `m_max` | recorded pitch | row pitch | differs |
|---|---|---|---|---|---|
| M2 | 1.6 | 1.6 | 0.4 | 0.4 | no |
| M2.5 | 2 | 2 | 0.45 | 0.45 | no |
| M3 | 2.4 | 2.4 | 0.5 | 0.5 | no |
| M3.5 | 2.8 | 2.8 | 0.6 | 0.6 | no |
| M4 | 3.2 | 3.2 | 0.7 | 0.7 | no |
| M5 | 4.7 | 4.7 | 0.8 | 0.8 | no |
| M6 | 5.2 | 5.2 | 1 | 1 | no |
| M7 | 5.6 | no row | 1 | no row | no product cell |
| M8 | 6.8 | 6.8 | 1.25 | 1.25 | no |
| M10 | 8.4 | 8.4 | 1.5 | 1.5 | no |
| M12 | 10.8 | 10.8 | 1.75 | 1.75 | no |
| M14 | 12.8 | 12.8 | 2 | 2 | no |
| M16 | 14.8 | 14.8 | 2 | 2 | no |
| M18 | 15.8 | 15.8 | 2.5 | 2.5 | no |
| M20 | 18 | 18 | 2.5 | 2.5 | no |

**Result: no size's `m` differs.** All 14 sizes that have an ISO 4032 row (M2 to M20 without M7) carry
the same `m` as the recorded cell, and the same pitch; the recorded preview heights were already the
GOST rows' `m_max`. M7 has no row, so it has no product cell, and its 16 recorded grid cells stay in
the pair tier as the previous entry ran them. So the set of product cells is empty: no prediction file
was written, no `screw pair nut` process was started, and no shipped-solid evidence readings exist
for this entry. `bench/product_cells.py` and its test were not added (the plan commits only this entry
in this case); nothing under `src/` or `tests/data/` changed.

**What this shows / what it does not.** The 240 cells of the previous entry are already cells at the
verified heights for every size that has a row, and their verdicts equal the pre-registered ones (240
of 240), so the product's nut heights are covered by that record. It does not run the product's own
`screw pair nut` command (the CLI path with the default `s`, the rows' `s`, or `--left-hand`) at any
cell beyond 05-15's single verify cell and the hand run it recorded, and the weekly `pair.yml` is
outside this entry. If a later edit moves a row's `m_max` (a re-read of the standard), this
comparison is the one to repeat, with predictions written before the run.


## Mesh deviation (Phase 5, D-21)

FRNT-06 asks that the download mesh's chord deviation be chosen against the 0.05 mm proof clearance
and not carried from spur (INTERIM, D-01). This entry is that choice, measured by the rule that was
committed before any row was run (`c87aadf`, `bench/mesh_deviation.py` docstring): **the fine preset
is the largest linear deflection on the ladder 0.01, 0.0075, 0.005, 0.0025 mm (angular 0.1 rad,
absolute) whose measured maximum radial deviation over M2, M3, M6, M10, M20, both hands, is at most
FRACTION x 0.05 mm.** FRACTION is 0.5, the owner's R6 answer (`05-OWNER-READS.md`, "Rulings", R6 `a`:
"0.5 of the 0.05 mm proof clearance, keep the 0.01 mm fine preset, cite the rule"); the agent did not
choose it. The bound is **0.025 mm**. The ladder was fixed in the same commit and no step was added or
removed after a table was seen.

**The step the rule selects: 0.01 mm / 0.1 rad.** The worst row at that step is 0.0161 mm (M20, both
hands), 64 % of the bound; the rule takes the largest step and stops there. `TESSELLATION["fine"]`
therefore stays (0.01, 0.1), so no fine-STL cap, refused-preset count or M20 x 200 figure is re-derived
(Task 3's kept-preset branch).

Command: `.venv/bin/python -m bench.mesh_deviation` (one run, exit 0). Run on HEAD
`e9698cfb8eb99e1aac390418b378b59ed47a978f` (the instrument as amended below; the working tree had no
other tracked change), 2026-10-20 (UTC). Host: `bench.machine_facts()`: `18 CPUs, arm64, 64.0 GiB RAM`,
macOS 27.0.1, Python 3.12.15, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1. Load before: load1 7.01 at
2026-10-20T14:51:36+00:00; after: load1 6.46 at 2026-10-20T14:52:15+00:00 (the second includes the
run's own meshing load). The host was shared with other sessions throughout and nothing waited for it
to quiet: the figures are geometry, not timings, and do not depend on load. Wall time of the whole run
40.7 s (`time`: user 183.0, system 4.0).

What was measured: each rod is the shipped `screw.solid.helical.thread(d, pitch, 8 pitch)`, one per size
and hand, meshed by `bench.thread_spike.measure.mesh_stl` (the shipped call, `shape.copy().exportStl(
..., ascii=False, relative=False)`), at the four ladder steps and, as the positive control, at the
preview preset (0.08 mm, 0.5 rad). Every facet of the STL is sampled; a facet is skipped when its
centroid lies within two pitches of either end of the rod. Deviation = |`section_radius(d, pitch, 0,
atan2(y, x) - hand 2 pi z / pitch)` - `hypot(x, y)`| at the facet centroid, hand +1 right, -1 left;
"p99" is the nearest-rank 99th percentile over the same facets; "Max vertex gap" is the largest
distance of any mesh vertex in the window from the modelled surface (the harness check).

| Size | Hand | Preset (lin mm / ang rad) | Triangles | Bytes | Max deviation mm | p99 deviation mm | Max vertex gap mm |
|---|---|---|---|---|---|---|---|
| M2 | right | 0.01 / 0.1 | 49130 | 2456584 | 0.0069 | 0.0067 | 5.7e-05 |
| M2 | right | 0.0075 / 0.1 | 57344 | 2867284 | 0.0069 | 0.0064 | 5.7e-05 |
| M2 | right | 0.005 / 0.1 | 72492 | 3624684 | 0.0064 | 0.0035 | 5.8e-05 |
| M2 | right | 0.0025 / 0.1 | 136794 | 6839784 | 0.0036 | 0.0022 | 5.8e-05 |
| M2 | right | 0.08 / 0.5 | 6010 | 300584 | 0.0789 | 0.0542 | 4.6e-05 |
| M2 | left | 0.01 / 0.1 | 42864 | 2143284 | 0.0068 | 0.0066 | 5.8e-05 |
| M2 | left | 0.0075 / 0.1 | 45464 | 2273284 | 0.0068 | 0.0051 | 5.8e-05 |
| M2 | left | 0.005 / 0.1 | 52730 | 2636584 | 0.0064 | 0.0036 | 5.8e-05 |
| M2 | left | 0.0025 / 0.1 | 102320 | 5116084 | 0.0036 | 0.0022 | 5.8e-05 |
| M2 | left | 0.08 / 0.5 | 5146 | 257384 | 0.0587 | 0.0542 | 4.5e-05 |
| M3 | right | 0.01 / 0.1 | 58020 | 2901084 | 0.0102 | 0.0096 | 8.6e-05 |
| M3 | right | 0.0075 / 0.1 | 70628 | 3531484 | 0.0102 | 0.0064 | 8.6e-05 |
| M3 | right | 0.005 / 0.1 | 89176 | 4458884 | 0.0079 | 0.0036 | 8.6e-05 |
| M3 | right | 0.0025 / 0.1 | 214170 | 10708584 | 0.0026 | 0.0020 | 8.6e-05 |
| M3 | right | 0.08 / 0.5 | 7054 | 352784 | 0.1237 | 0.0913 | 7.9e-05 |
| M3 | left | 0.01 / 0.1 | 46844 | 2342284 | 0.0103 | 0.0070 | 8.6e-05 |
| M3 | left | 0.0075 / 0.1 | 52522 | 2626184 | 0.0103 | 0.0056 | 8.6e-05 |
| M3 | left | 0.005 / 0.1 | 65272 | 3263684 | 0.0097 | 0.0036 | 8.6e-05 |
| M3 | left | 0.0025 / 0.1 | 160254 | 8012784 | 0.0026 | 0.0023 | 8.6e-05 |
| M3 | left | 0.08 / 0.5 | 6192 | 309684 | 0.0888 | 0.0618 | 7.9e-05 |
| M6 | right | 0.01 / 0.1 | 88846 | 4442384 | 0.0158 | 0.0071 | 5.5e-05 |
| M6 | right | 0.0075 / 0.1 | 133744 | 6687284 | 0.0158 | 0.0064 | 5.7e-05 |
| M6 | right | 0.005 / 0.1 | 212452 | 10622684 | 0.0051 | 0.0045 | 5.5e-05 |
| M6 | right | 0.0025 / 0.1 | 359630 | 17981584 | 0.0036 | 0.0017 | 5.9e-05 |
| M6 | right | 0.08 / 0.5 | 12348 | 617484 | 0.0775 | 0.0754 | 1.3e-05 |
| M6 | left | 0.01 / 0.1 | 66248 | 3312484 | 0.0159 | 0.0073 | 5.5e-05 |
| M6 | left | 0.0075 / 0.1 | 107834 | 5391784 | 0.0159 | 0.0064 | 5.8e-05 |
| M6 | left | 0.005 / 0.1 | 160550 | 8027584 | 0.0051 | 0.0035 | 5.5e-05 |
| M6 | left | 0.0025 / 0.1 | 243920 | 12196084 | 0.0036 | 0.0018 | 5.8e-05 |
| M6 | left | 0.08 / 0.5 | 9712 | 485684 | 0.0797 | 0.0631 | 1.3e-05 |
| M10 | right | 0.01 / 0.1 | 191924 | 9596284 | 0.0150 | 0.0081 | 9.0e-05 |
| M10 | right | 0.0075 / 0.1 | 235852 | 11792684 | 0.0081 | 0.0073 | 9.1e-05 |
| M10 | right | 0.005 / 0.1 | 303458 | 15172984 | 0.0081 | 0.0036 | 9.7e-05 |
| M10 | right | 0.0025 / 0.1 | 780908 | 39045484 | 0.0025 | 0.0021 | 9.7e-05 |
| M10 | right | 0.08 / 0.5 | 15520 | 776084 | 0.1268 | 0.0946 | 9.0e-05 |
| M10 | left | 0.01 / 0.1 | 145516 | 7275884 | 0.0150 | 0.0080 | 9.0e-05 |
| M10 | left | 0.0075 / 0.1 | 170980 | 8549084 | 0.0081 | 0.0068 | 9.1e-05 |
| M10 | left | 0.005 / 0.1 | 218420 | 10921084 | 0.0081 | 0.0035 | 9.7e-05 |
| M10 | left | 0.0025 / 0.1 | 599166 | 29958384 | 0.0029 | 0.0020 | 9.7e-05 |
| M10 | left | 0.08 / 0.5 | 12344 | 617284 | 0.1299 | 0.0889 | 8.9e-05 |
| M20 | right | 0.01 / 0.1 | 316938 | 15846984 | 0.0161 | 0.0068 | 1.9e-04 |
| M20 | right | 0.0075 / 0.1 | 376992 | 18849684 | 0.0127 | 0.0058 | 1.9e-04 |
| M20 | right | 0.005 / 0.1 | 783488 | 39174484 | 0.0052 | 0.0041 | 1.9e-04 |
| M20 | right | 0.0025 / 0.1 | 1341052 | 67052684 | 0.0035 | 0.0017 | 1.9e-04 |
| M20 | right | 0.08 / 0.5 | 42032 | 2101684 | 0.1250 | 0.0648 | 1.8e-04 |
| M20 | left | 0.01 / 0.1 | 222164 | 11108284 | 0.0161 | 0.0069 | 1.9e-04 |
| M20 | left | 0.0075 / 0.1 | 253848 | 12692484 | 0.0110 | 0.0058 | 1.9e-04 |
| M20 | left | 0.005 / 0.1 | 605556 | 30277884 | 0.0060 | 0.0038 | 1.9e-04 |
| M20 | left | 0.0025 / 0.1 | 905746 | 45287384 | 0.0035 | 0.0017 | 1.9e-04 |
| M20 | left | 0.08 / 0.5 | 32794 | 1639784 | 0.1233 | 0.0643 | 1.8e-04 |

**Reading it.** The rule selects 0.01 mm at 0.1 rad: the largest deviation on that step in the whole
grid is 0.0161 mm (M20, right and left), against the 0.025 mm bound. The positive control works: at the
preview preset every size and both hands read 0.0587 to 0.1299 mm, all over the bound. Triangles at
the selected step are 42 864 to 316 938 across the grid; the counts for M2, M3, M6, M10 and M20
right-hand equal those 05-RESEARCH F2 recorded for the same rods (49 130, 58 020, 88 846, 191 924,
316 938).

**What this shows / what it does not.**
- The deviation is stated on sampled facet centroids (all of them, on these rods), an upper bound of
  each sampled point's distance to the surface, not a proven bound of the mesh's global maximum
  (vertices lie on the surface and read as zero). It is a radial gap: on a flank the distance normal
  to the surface is about half of it, on a crest or root equal. Checked against the kernel on M3
  right-hand at 0.01 mm: for the 12 facets tried (the six largest gaps and six at random)
  `Shape.distance` from the centroid to the solid's boundary faces read 0.498 to 0.521 of the radial
  gap on flank facets and 1.000 to 1.002 on crest and root facets.
- It covers the five sizes and both hands named, on 8-pitch rods of the shipped thread, not the
  finished bolt (head, tip cone, fillet) or the nut (void, countersinks). The head and nut faces are
  planar or conical and were not sampled.
- **A vertex departs from the model by up to 1.9e-04 mm at M20** (5.7e-05 at M2, 8.6e-05 at M3,
  9.0e-05 to 9.7e-05 at M10). It is the same at all five presets of a size, so it is the shipped solid
  and not the mesh: the order of `helical.SEWING_TOLERANCE` (1e-4 mm). It is 0.8 % of the bound and is
  not added to the deviations above.
- **The instrument was amended once, after its first run.** The first run (HEAD `c87aadf`, load1 6.35
  at 2026-10-20T14:47:19+00:00, 20.6 s) aborted at M20 right-hand, 0.01 mm: its harness check, written
  at 1e-4 mm from 05-RESEARCH F2's 1.2e-05 read at M6, found a vertex 1.912e-04 mm off the model, and
  it printed 40 rows (M2 to M10) before the abort. Those 40 rows equal this table's in every column they
  printed. The cause was diagnosed (above) and the threshold became 1e-3 mm in `e9698cf`, before this
  run: 540 times below the 0.54 mm a wrong hand misses by, and 4 % of the bound. The rule, the ladder,
  the fraction and the bound were not touched.
- **05-RESEARCH F2's maxima are not all reproduced.** Triangle counts match F2 exactly, but F2's
  sampled maxima (every 5th to 7th facet) are larger than this run's every-facet maxima for some
  sizes: at 0.01 mm M2 0.0094 against 0.0069, M3 0.0141 against 0.0102, M10 0.0184 against 0.0150
  (M6 0.0159 against 0.0158 and M20 0.0161 against 0.0161 agree); at 0.005 mm M2 0.0090 against
  0.0064, M6 0.0056 against 0.0051, M20 0.0059 against 0.0052 (M3 0.0079 and M10 0.0081 agree). A
  sample cannot exceed the maximum of all its facets for the same metric, so F2's probe measured
  something slightly different there; its script is not in the repository and was not recovered.
  The kernel cross-check above supports this run's metric. The decision does not turn on it: F2's
  largest fine-preset figure, 0.0184 mm, is also under the 0.025 mm bound.


## Nut fine-STL caps (Phase 5, R16)

T-05-12 (huge `m`, high) is open in `05-SECURITY.md`: a nut's fine STL plus its gzip copy can pass the
64 MiB export budget with nothing refusing it, and R12 (option b, 2026-10-20) sent the nut's caps to
their own run. R16 (`05-OWNER-READS.md`, owner's literal answer `option-a`) fixed how clearance enters:
the ceiling C is 5.0 mm, and a fine STL above C on a measured key is refused. This entry is that run,
made by the rule committed before any row was run (`0c349a7`, `bench/nut_fine_caps.py` docstring, run
id `2026-10-20-nut-fine-caps`). **The rule: for each of the 30 keys (the 15 ISO 262 coarse (d, pitch) by
both hands), build the nut `NutParams(d, pitch, s = 1e5, m, clearance = 5.0, hand)` for m = 1, 2, 3, ...
mm (and at the turn cap's own m when 248 pitches is not whole), mesh each by the shipped
`screw.solid.export(p, "stl", "fine")`, and sum the STL's length and its gzip level-1 copy's. A row fits
when the sum is at most `BUDGET_BYTES` (64 MiB, the rods' constant, imported from
`bench.thread_spike.verdict`). The cap is the largest measured m that fits below the first m over; at
each finite cap five check rows are measured (m = cap; s = 1e5 at clearance -0.05, 0, 0.1 and 2.5; and
clearance 5 at the slimmest s, d + 11). No cap ships if a check row is over budget or failed, a ladder
row failed below the crossing, a key has no fitting m, or a cap is below the key's GOST ISO 4032-2014
`m_max`.** C and s are fixed in the same commit; no step, check or constant was changed after the
first row ran.

**The run met a stop condition, so no cap ships.** All 30 ladders crossed the budget and all 30 caps
are measured (table below); no ladder row failed and no cap is below an ISO 4032 `m_max`. But **46 of
the 150 check rows failed to build**: the shipped nut build raised `BuildError: Geometry kernel produced
the wrong lead-in countersink` (the D-10 / R11 piece gate, tolerance 0.03 of the piece) at m = cap,
s = 1e5 and clearance -0.05, 0 or 0.1, on 16, 15 and 15 of the 30 keys respectively. The 104 check rows
that built all fit the budget (largest sum 0.960 of 64 MiB). By the pre-registered rule a failed check
is a stop condition, and the executor stopped at the record (L02): the caps below are measurements, not
shipped constants. What the failed rows are and what to do about them is in "What this shows" and is
the owner's.

Command: `/usr/bin/time -p timeout 7000 .venv/bin/python -m bench.nut_fine_caps` (one run, exit 0, stdout
to the session scratch). An earlier launch of the same command with the shell's `time -p` failed in the
shell before Python started (`command not found: -p`): no row ran, no records file was written, nothing
was read, and it is not a run. Run on HEAD `0c349a7bc1e3bb6510b21071ad51eb9083aaaf0c` (the instrument
commit; `git status --porcelain -- src bench tests` empty at the start), 2026-10-20 (UTC). Host:
`bench.machine_facts()`: `18 CPUs, arm64, 64.0 GiB RAM`, macOS 27.0.1, Python 3.12.15, cadquery 2.8.0,
cadquery-ocp 7.9.3.1.1. Load before: load1 9.89 at 2026-10-20T16:43:05+00:00 (`uptime`: load averages
9.89 11.48 9.41); after: load1 9.46 at 2026-10-20T17:33:16+00:00 (`uptime`: 8.87 9.96 11.12; includes
the run's own meshing load). The host was shared with other sessions throughout and nothing waited for
it to quiet: the bytes are geometry and do not depend on load, and the rule never reads a time. Wall
time 3011.1 s in the process (`time -p`: real 3012.79 s, user 12894.22 s, sys 1334.18 s), against the
7000 s deadline. Records: `bench/results/phase-05/nut-fine-caps.jsonl`, 1238 lines (a header, 1236 row
lines, an end line), sha256
`8682c7023253c1320ba6645fd72021e9122bec16c232c9a4064b7219eba92ade`. The 1236 rows are 1086 ladder rows
(all built) and 150 check rows (104 built, 46 failed).

Caps, with the first m over budget (C = 5 mm, s = 1e5 mm, fine preset (0.01 mm, 0.1 rad)):

| Key | Cap m (mm) | Sum at cap (bytes) | Sum / 64 MiB | First over m | Sum there (bytes) | ISO 4032 m_max |
|---|---|---|---|---|---|---|
| d 2 pitch 0.4 right | 12 | 64735640 | 0.965 | 13 | 71005750 | 1.6 |
| d 2.5 pitch 0.45 right | 13 | 64012922 | 0.954 | 14 | 68428108 | 2.0 |
| d 3 pitch 0.5 right | 15 | 65547006 | 0.977 | 16 | 69813724 | 2.4 |
| d 3.5 pitch 0.6 right | 18 | 66734686 | 0.994 | 19 | 70139875 | 2.8 |
| d 4 pitch 0.7 right | 21 | 66082609 | 0.985 | 22 | 69317498 | 3.2 |
| d 5 pitch 0.8 right | 24 | 66646189 | 0.993 | 25 | 69542589 | 4.7 |
| d 6 pitch 1 right | 30 | 64969342 | 0.968 | 31 | 67230121 | 5.2 |
| d 7 pitch 1 right | 30 | 66135909 | 0.986 | 31 | 68607321 | no row |
| d 8 pitch 1.25 right | 38 | 65305055 | 0.973 | 39 | 67447673 | 6.8 |
| d 10 pitch 1.5 right | 36 | 66558142 | 0.992 | 37 | 67794996 | 8.4 |
| d 12 pitch 1.75 right | 41 | 66221923 | 0.987 | 42 | 68811348 | 10.8 |
| d 14 pitch 2 right | 46 | 66441517 | 0.990 | 47 | 68790674 | 12.8 |
| d 16 pitch 2 right | 45 | 66352378 | 0.989 | 46 | 67140351 | 14.8 |
| d 18 pitch 2.5 right | 54 | 65972568 | 0.983 | 55 | 67148258 | 15.8 |
| d 20 pitch 2.5 right | 36 | 65858267 | 0.981 | 37 | 67978825 | 18.0 |
| d 2 pitch 0.4 left | 15 | 64182831 | 0.956 | 16 | 68898904 | 1.6 |
| d 2.5 pitch 0.45 left | 17 | 65952621 | 0.983 | 18 | 69371877 | 2.0 |
| d 3 pitch 0.5 left | 19 | 65310127 | 0.973 | 20 | 69714550 | 2.4 |
| d 3.5 pitch 0.6 left | 22 | 65325736 | 0.973 | 23 | 67933663 | 2.8 |
| d 4 pitch 0.7 left | 25 | 65102205 | 0.970 | 26 | 67202314 | 3.2 |
| d 5 pitch 0.8 left | 30 | 66717786 | 0.994 | 31 | 70095896 | 4.7 |
| d 6 pitch 1 left | 38 | 65483018 | 0.976 | 39 | 67660755 | 5.2 |
| d 7 pitch 1 left | 38 | 66272445 | 0.988 | 39 | 68903229 | no row |
| d 8 pitch 1.25 left | 47 | 66449900 | 0.990 | 48 | 67944606 | 6.8 |
| d 10 pitch 1.5 left | 50 | 66312444 | 0.988 | 51 | 67982376 | 8.4 |
| d 12 pitch 1.75 left | 56 | 64530454 | 0.962 | 57 | 67196836 | 10.8 |
| d 14 pitch 2 left | 61 | 66333111 | 0.988 | 62 | 67605348 | 12.8 |
| d 16 pitch 2 left | 59 | 65240948 | 0.972 | 60 | 67127438 | 14.8 |
| d 18 pitch 2.5 left | 73 | 66784551 | 0.995 | 74 | 68875260 | 15.8 |
| d 20 pitch 2.5 left | 47 | 66509248 | 0.991 | 48 | 70049843 | 18.0 |

Checks, as a fraction of 64 MiB at m = cap (the sample points of the rule; FAILED is the shipped build
refusing the part, no sum exists):

| Key | cap m | c -0.05, s 1e5 | c 0, s 1e5 | c 0.1, s 1e5 | c 2.5, s 1e5 | c 5, s = d + 11 |
|---|---|---|---|---|---|---|
| d 2 pitch 0.4 right | 12 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.357 | 0.922 |
| d 2.5 pitch 0.45 right | 13 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.491 | 0.911 |
| d 3 pitch 0.5 right | 15 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.662 | 0.935 |
| d 3.5 pitch 0.6 right | 18 | 0.291 | 0.291 | 0.293 | 0.748 | 0.952 |
| d 4 pitch 0.7 right | 21 | 0.341 | 0.339 | 0.348 | 0.812 | 0.942 |
| d 5 pitch 0.8 right | 24 | 0.344 | 0.345 | 0.347 | 0.857 | 0.950 |
| d 6 pitch 1 right | 30 | 0.361 | 0.364 | 0.368 | 0.926 | 0.925 |
| d 7 pitch 1 right | 30 | 0.378 | 0.381 | 0.381 | 0.960 | 0.942 |
| d 8 pitch 1.25 right | 38 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.960 | 0.930 |
| d 10 pitch 1.5 right | 36 | 0.648 | 0.646 | 0.649 | 0.943 | 0.948 |
| d 12 pitch 1.75 right | 41 | 0.688 | 0.678 | 0.702 | 0.936 | 0.943 |
| d 14 pitch 2 right | 46 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.940 | 0.946 |
| d 16 pitch 2 right | 45 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.932 | 0.945 |
| d 18 pitch 2.5 right | 54 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.934 | 0.939 |
| d 20 pitch 2.5 right | 36 | 0.543 | 0.549 | 0.542 | 0.661 | 0.938 |
| d 2 pitch 0.4 left | 15 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.368 | 0.914 |
| d 2.5 pitch 0.45 left | 17 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.603 | 0.940 |
| d 3 pitch 0.5 left | 19 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.790 | 0.931 |
| d 3.5 pitch 0.6 left | 22 | FAILED (piece gate) | 0.299 | 0.291 | 0.774 | 0.930 |
| d 4 pitch 0.7 left | 25 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.784 | 0.927 |
| d 5 pitch 0.8 left | 30 | 0.328 | 0.326 | 0.329 | 0.849 | 0.951 |
| d 6 pitch 1 left | 38 | 0.353 | 0.351 | 0.361 | 0.926 | 0.932 |
| d 7 pitch 1 left | 38 | 0.367 | 0.372 | 0.377 | 0.953 | 0.944 |
| d 8 pitch 1.25 left | 47 | 0.590 | 0.605 | 0.649 | 0.933 | 0.946 |
| d 10 pitch 1.5 left | 50 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.945 | 0.944 |
| d 12 pitch 1.75 left | 56 | 0.738 | 0.748 | 0.756 | 0.898 | 0.918 |
| d 14 pitch 2 left | 61 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.914 | 0.945 |
| d 16 pitch 2 left | 59 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.902 | 0.928 |
| d 18 pitch 2.5 left | 73 | FAILED (piece gate) | FAILED (piece gate) | FAILED (piece gate) | 0.936 | 0.931 |
| d 20 pitch 2.5 left | 47 | 0.547 | 0.544 | 0.562 | 0.651 | 0.948 |

The 46 failed rows all carry one error, the lead-in countersink piece gate, with relative errors from
-1.564 to +2.360 against the 0.03 allowed; the smallest in size is -0.0327 (M18 right, clearance -0.05).
They are the same part at the same s and clearance that the ladder never reached (the ladder runs at
clearance 5), so the run has no row that says whether a nut at s = 1e5 and a clearance of 0.1 is
buildable at m below the cap.

**What this shows / what it does not.**
- It shows 30 measured caps at C = 5 mm and s = 1e5 mm, each the largest whole mm whose fine STL plus
  its gzip copy fits 64 MiB on this host (0.954 to 0.995 of the budget at the cap, over by 0.03 to
  5.8 % at cap + 1). The planner's estimate for M20 was 37 to 39 mm; the measured cap is 36 (right) and 47
  (left). Against the tallest GOST ISO 4032-2014 height in its row, the caps are 2.0 times (M20
  right, 36 against 18 mm) to 9.4 times (M2 left, 15 against 1.6 mm); M7 has no row.
- It shows that the clearance and s sampled below C make a smaller file: all 104 built check rows sit at
  0.291 to 0.960 of the budget against 0.954 to 0.995 at the cap. These are samples, not a proof that
  the bytes are monotonic in clearance or in s.
- It does not show that the 46 failed check rows are numerical noise in the gate and not a real
  defect. The failures sit at the model's largest s (1e5 mm), where the hexagon's volume is about 8.7e9
  mm^3 per mm of m and a lead-in piece's oracle is 0.1 to 150 mm^3, so a volume difference can lose the piece;
  that is a reading, not a measurement made here. The ladder at clearance 5 never failed (1086 of 1086
  built), so the gate is not tripped by m or by the preset alone.
- It is one run on macOS arm64, not linux/amd64 (Phase 7 re-measures, OPER-02), against the INTERIM
  64 MiB budget and the 0.01 mm / 0.1 rad fine preset, on a load-shared host.
- It measures nothing above C = 5 mm, by R16: a fine STL above C is refused, not capped.


## Nut fine-STL caps, amended re-run (Phase 5, R17)

The first run (`2026-10-20-nut-fine-caps`, entry "Nut fine-STL caps (Phase 5, R16)" above, records
`nut-fine-caps.jsonl`, unchanged) measured all 30 caps but stopped on 46 check rows that the shipped
build refused. The owner ruled on 2026-10-21 (R17, `05-OWNER-READS.md`, `option 1`): re-run with the
rule amended so that **a check row the shipped build refuses (`BuildError`) is recorded with its
error, counts as "not a file" and is not a stop; every other stop condition is unchanged**, under a
new run id. The amendment is in the `bench/nut_fine_caps.py` docstring ("AMENDMENT 1") and was
committed, with R17 and its tests, in `9b4fbb7`, before any row of this run. The ladder, C = 5.0 mm,
s = 1e5 mm, the five checks and the 64 MiB budget are the first run's. The refusal the 46 rows show
is its own debt item, filed in `63c22a6`:
`docs/tech_debt/active/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md`.

**Result: no stop condition. The 30 caps equal the first run's caps.** All 30 ladders crossed the
budget, all 1086 ladder rows built, no cap is below an ISO 4032 `m_max`, and no check row is over
budget or failed otherwise. Of the 150 check rows 104 built and fit (largest sum 0.960 of 64 MiB)
and 46 were refused by the build, the same 46 rows with the same errors. Compared with the first
run's records row by row (1236 rows, matched on role, key, m, clearance and s): the row sets are
equal, the raw and gzip-1 bytes are equal on every row, the outcomes agree (built = built, the
first run's 46 failed = this run's 46 refused) and the 46 error strings are identical. The bytes are
deterministic, as expected; only the seconds differ.

Command: `/usr/bin/time -p timeout 7000 .venv/bin/python -m bench.nut_fine_caps` (one run, exit 0).
Run on HEAD `63c22a602daa37a394e706841468b2a42e679e0a` (`git status --porcelain -- src bench tests`
empty at the start; the instrument is byte-identical between the amendment commit `9b4fbb7` and this
records commit), 2026-10-21 (UTC). Host: `18 CPUs, arm64, 64.0 GiB RAM`, macOS 27.0.1, Python
3.12.15, cadquery 2.8.0, cadquery-ocp 7.9.3.1.1. Load before: load1 7.32 at 2026-10-21T01:48:42+00:00
(`uptime`: 7.32 7.53 5.24); after: load1 8.95 at 2026-10-21T02:37:37+00:00 (`uptime`: 7.71 10.02
10.11; includes the run's own meshing load). The host was shared and nothing waited for it to
quiet; the bytes are geometry and the rule never reads a time. Wall time 2935.7 s in the process
(`time -p`: real 2937.34 s, user 12731.02 s, sys 1347.83 s), against the 7000 s deadline. Records:
`bench/results/phase-05/nut-fine-caps-amended.jsonl`, 1238 lines (a header that names the run it
amends, 1236 rows, an end line), sha256
`64ae355a043687e30bcf98d334f6b9adf1814005e5741a01591710915fa26324`. The 1236 rows are 1086 ladder
rows (all built) and 150 check rows (104 built, 46 refused).

Caps (C = 5 mm, s = 1e5 mm, fine preset (0.01 mm, 0.1 rad); the table is identical to the first run's):

| Key | Cap m (mm) | Sum at cap (bytes) | Sum / 64 MiB | First over m | Sum there (bytes) | ISO 4032 m_max |
|---|---|---|---|---|---|---|
| d 2 pitch 0.4 right | 12 | 64735640 | 0.965 | 13 | 71005750 | 1.6 |
| d 2.5 pitch 0.45 right | 13 | 64012922 | 0.954 | 14 | 68428108 | 2.0 |
| d 3 pitch 0.5 right | 15 | 65547006 | 0.977 | 16 | 69813724 | 2.4 |
| d 3.5 pitch 0.6 right | 18 | 66734686 | 0.994 | 19 | 70139875 | 2.8 |
| d 4 pitch 0.7 right | 21 | 66082609 | 0.985 | 22 | 69317498 | 3.2 |
| d 5 pitch 0.8 right | 24 | 66646189 | 0.993 | 25 | 69542589 | 4.7 |
| d 6 pitch 1 right | 30 | 64969342 | 0.968 | 31 | 67230121 | 5.2 |
| d 7 pitch 1 right | 30 | 66135909 | 0.986 | 31 | 68607321 | no row |
| d 8 pitch 1.25 right | 38 | 65305055 | 0.973 | 39 | 67447673 | 6.8 |
| d 10 pitch 1.5 right | 36 | 66558142 | 0.992 | 37 | 67794996 | 8.4 |
| d 12 pitch 1.75 right | 41 | 66221923 | 0.987 | 42 | 68811348 | 10.8 |
| d 14 pitch 2 right | 46 | 66441517 | 0.990 | 47 | 68790674 | 12.8 |
| d 16 pitch 2 right | 45 | 66352378 | 0.989 | 46 | 67140351 | 14.8 |
| d 18 pitch 2.5 right | 54 | 65972568 | 0.983 | 55 | 67148258 | 15.8 |
| d 20 pitch 2.5 right | 36 | 65858267 | 0.981 | 37 | 67978825 | 18.0 |
| d 2 pitch 0.4 left | 15 | 64182831 | 0.956 | 16 | 68898904 | 1.6 |
| d 2.5 pitch 0.45 left | 17 | 65952621 | 0.983 | 18 | 69371877 | 2.0 |
| d 3 pitch 0.5 left | 19 | 65310127 | 0.973 | 20 | 69714550 | 2.4 |
| d 3.5 pitch 0.6 left | 22 | 65325736 | 0.973 | 23 | 67933663 | 2.8 |
| d 4 pitch 0.7 left | 25 | 65102205 | 0.970 | 26 | 67202314 | 3.2 |
| d 5 pitch 0.8 left | 30 | 66717786 | 0.994 | 31 | 70095896 | 4.7 |
| d 6 pitch 1 left | 38 | 65483018 | 0.976 | 39 | 67660755 | 5.2 |
| d 7 pitch 1 left | 38 | 66272445 | 0.988 | 39 | 68903229 | no row |
| d 8 pitch 1.25 left | 47 | 66449900 | 0.990 | 48 | 67944606 | 6.8 |
| d 10 pitch 1.5 left | 50 | 66312444 | 0.988 | 51 | 67982376 | 8.4 |
| d 12 pitch 1.75 left | 56 | 64530454 | 0.962 | 57 | 67196836 | 10.8 |
| d 14 pitch 2 left | 61 | 66333111 | 0.988 | 62 | 67605348 | 12.8 |
| d 16 pitch 2 left | 59 | 65240948 | 0.972 | 60 | 67127438 | 14.8 |
| d 18 pitch 2.5 left | 73 | 66784551 | 0.995 | 74 | 68875260 | 15.8 |
| d 20 pitch 2.5 left | 47 | 66509248 | 0.991 | 48 | 70049843 | 18.0 |

Checks, as a fraction of 64 MiB at m = cap (REFUSED: the shipped build raised `BuildError`, the
lead-in countersink piece gate; no file exists and no sum):

| Key | cap m | c -0.05, s 1e5 | c 0, s 1e5 | c 0.1, s 1e5 | c 2.5, s 1e5 | c 5, s = d + 11 |
|---|---|---|---|---|---|---|
| d 2 pitch 0.4 right | 12 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.357 | 0.922 |
| d 2.5 pitch 0.45 right | 13 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.491 | 0.911 |
| d 3 pitch 0.5 right | 15 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.662 | 0.935 |
| d 3.5 pitch 0.6 right | 18 | 0.291 | 0.291 | 0.293 | 0.748 | 0.952 |
| d 4 pitch 0.7 right | 21 | 0.341 | 0.339 | 0.348 | 0.812 | 0.942 |
| d 5 pitch 0.8 right | 24 | 0.344 | 0.345 | 0.347 | 0.857 | 0.950 |
| d 6 pitch 1 right | 30 | 0.361 | 0.364 | 0.368 | 0.926 | 0.925 |
| d 7 pitch 1 right | 30 | 0.378 | 0.381 | 0.381 | 0.960 | 0.942 |
| d 8 pitch 1.25 right | 38 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.960 | 0.930 |
| d 10 pitch 1.5 right | 36 | 0.648 | 0.646 | 0.649 | 0.943 | 0.948 |
| d 12 pitch 1.75 right | 41 | 0.688 | 0.678 | 0.702 | 0.936 | 0.943 |
| d 14 pitch 2 right | 46 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.940 | 0.946 |
| d 16 pitch 2 right | 45 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.932 | 0.945 |
| d 18 pitch 2.5 right | 54 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.934 | 0.939 |
| d 20 pitch 2.5 right | 36 | 0.543 | 0.549 | 0.542 | 0.661 | 0.938 |
| d 2 pitch 0.4 left | 15 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.368 | 0.914 |
| d 2.5 pitch 0.45 left | 17 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.603 | 0.940 |
| d 3 pitch 0.5 left | 19 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.790 | 0.931 |
| d 3.5 pitch 0.6 left | 22 | REFUSED (not a file) | 0.299 | 0.291 | 0.774 | 0.930 |
| d 4 pitch 0.7 left | 25 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.784 | 0.927 |
| d 5 pitch 0.8 left | 30 | 0.328 | 0.326 | 0.329 | 0.849 | 0.951 |
| d 6 pitch 1 left | 38 | 0.353 | 0.351 | 0.361 | 0.926 | 0.932 |
| d 7 pitch 1 left | 38 | 0.367 | 0.372 | 0.377 | 0.953 | 0.944 |
| d 8 pitch 1.25 left | 47 | 0.590 | 0.605 | 0.649 | 0.933 | 0.946 |
| d 10 pitch 1.5 left | 50 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.945 | 0.944 |
| d 12 pitch 1.75 left | 56 | 0.738 | 0.748 | 0.756 | 0.898 | 0.918 |
| d 14 pitch 2 left | 61 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.914 | 0.945 |
| d 16 pitch 2 left | 59 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.902 | 0.928 |
| d 18 pitch 2.5 left | 73 | REFUSED (not a file) | REFUSED (not a file) | REFUSED (not a file) | 0.936 | 0.931 |
| d 20 pitch 2.5 left | 47 | 0.547 | 0.544 | 0.562 | 0.651 | 0.948 |

**What this shows / what it does not.**
- It shows the first run's 30 caps again, byte for byte, under the amended rule, with no other stop
  condition. It is a repeat of a deterministic measurement, not independent evidence: the same host,
  the same kernel build, the same shipped export path.
- The amendment was made after the first run's data was seen, on the owner's ruling (R17). What it
  changes is only how 46 refused checks are classified; it moves no cap, since the caps come from the
  ladder rows, which are the same rows with the same bytes.
- It does not say the refused nuts are buildable: a nut at s = 1e5 and a clearance of -0.05, 0 or 0.1
  at the cap is refused by the shipped build today (the debt item above), so no file of that part can
  reach the budget. The sampled checks that built, 104 rows at 0.291 to 0.960 of the budget, sit below
  the cap rows (0.954 to 0.995); they are samples, not a proof that the bytes are monotonic in
  clearance or s.
- It is one run on macOS arm64, not linux/amd64 (Phase 7 re-measures, OPER-02), against the INTERIM
  64 MiB budget and the fine preset, on a load-shared host. It measures nothing above C = 5 mm, by
  R16: a fine STL above C is refused, not capped.


## Printed pair matrix (Phase 6, 06-print-run-1)

PAIR-02 asks for a default `clearance` that comes from a recorded printed test, not from a forum or
vendor figure. This entry is run 1 of that test: the clearance ladder 0.05, 0.1, 0.15, 0.2, 0.25 mm at
the four coarse sizes M6, M8, M10 and M12, three samples per cell (60 nuts, 12 bolts).

**The rule, fixed before the run.** Protocol and reader landed on `main` in PR A (#19), squash commit
`16f7041`, before any part was exported or printed: `06-PRINT-PROTOCOL.md` ("Rules", D-05 to D-08) and
`bench/print_rules.py` (`read_matrix`, `default_from`). A sample passes or binds by the hand fit test; a
cell (size, clearance) passes when all 3 samples do; the default is the smallest step from which every
cell of every size passes, and D-08 returns no default when no step qualifies or a size is not
monotone. Order of fitting per bolt was R3 (loosest first), the plate rule R4, the only reprint
exception R5. The owner's P1 prediction was 0.10 mm; it was never an input.

**The parts.** The product's own fine exports, made by `python -m bench.print_matrix export run-1 -o
bench/results/phase-06/stl/run-1` from the landed code: 24 STL files (4 bolts, 20 nuts). The manifest
`bench/results/phase-06/manifest-run-1.tsv` (name, bytes, sha256 of every file) was committed in
`646b07d` before the first print; its own sha256 is
`b98c445f88c1b7d21e198deb5d2ef17a77b698310b969d0e2b90f1cb445edb0d`.

**The print.** One profile for every part, the protocol's "Print profile" on `main`: Prusa MK4, 0.4 mm
nozzle, Prusa PETG, 0.2 mm layers, PrusaSlicer with the stock Prusa PETG profile, nut on its face and
bolt head-down. Print and test dates: not reported by the owner (reported 2026-10-23). Plates: the
owner printed each (size, sample) group, one bolt and its five nuts, on its own bed: 12 beds labelled
M6-1 to M12-3. Sample k of every cell is therefore on a bed labelled `-k`, which is plate set k of R4.
No part failed to print and no R5 reprint was reported; no note says `reprinted: print failure`.

**The record, and where it came from.** `bench/results/phase-06/print-run-1.tsv`, sha256
`f76753ded41726daec0a11ec4c5eabc5f4d2afb094cbe258d5e9d915aa6db725`, pinned as `RUN_1_SHA256` in
`bench/print_rules.py`. The owner printed and fit-tested and reported the results in prose. The
orchestrating Claude transcribed that report into the TSV, and the owner then confirmed the full
60-row table as correct ("correct", 2026-10-23). The owner did not type the cells; every cell is the
owner's reported observation as transcribed and confirmed. The agent that pinned the record changed no
cell. The owner confirmed that all 3 samples of a cell behaved the same and that "binds immediately"
means the nut would not start, recorded as 0 turns. The owner's words:

> all groups were printed separately
>
> m6, m8 - 0.1 clearence worked, less - binds immediately
>
> m10, m12 - 0.15 celarence workds, less - binds immediately
>
> loose: 0.20 and 0.25 loose for m4, m5, m6. 0.25 for m8, m10

(The loose line also names M4 and M5, which are not run 1; they are left out of this record.)

**The reading.** `default_from(read_matrix(load(RUN_1, RUN_1_SHA256)))`, run through the landed rule
with a one-off script over `read_matrix` output, not by reading the file by eye. The record read
cleanly: 60 samples, every `order` the one R3 gives its clearance. Passes per cell, n of 3:

| size | 0.05 | 0.1 | 0.15 | 0.2 | 0.25 |
|---|---|---|---|---|---|
| M6 | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| M8 | 0/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| M10 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 |
| M12 | 0/3 | 0/3 | 3/3 | 3/3 | 3/3 |

42 passes and 18 binds; every bind is 0 turns, so no sample stopped part-way. 12 passes are noted
`loose`: M6 at 0.2 and 0.25 (6), M8 at 0.25 (3), M10 at 0.25 (3). No R5 note.

**Outcome (D-07): the default is 0.15 mm.** Every size passes 3/3 from 0.15 mm up, and no size has a
passing cell below a failing one, so D-08 did not fire. `tests/test_print_rules.py` asserts it:
`test_run_1_reads_a_default_of_0_15_mm_by_d_07`, with `test_the_run_1_record_is_the_one_pinned`
refusing any later byte change of the record. The P1 prediction (0.10 mm) was not borne out: M10 and
M12 bind at 0.1 in 3 of 3. M6 and M8 would have passed at 0.1, so the size that sets the default is
the larger pair.

**Off-protocol, as reported.** The owner also printed M3 to M5 informally, before any default shipped:
M3 "too small to print"; M4 and M5 pass at 0.1 and bind below. That is not run 2: those parts are not
the run-2 exports, are not in `print-run-2.tsv`, and no number or threshold is read from them. Run 2
(plan 06-08) remains to be decided by the owner.
*Superseded 2026-10-23 by owner ruling R10: the owner later accepted these prints as run 2; see
"## Printability run (Phase 6, 06-print-run-2)" and L18.*

**What this shows / what it does not.** It shows that on this printer and profile a product nut at
0.15 mm clearance threaded by hand onto a product bolt at M6, M8, M10 and M12, in 12 of 12 samples,
and that 0.05 mm bound at every size (12 of 12). It does not show anything for another printer,
material, layer height, nozzle or orientation, nor for sizes between or outside M6 to M12 (the
M3 to M5 readings above are informal), nor for fine pitch. It tests a nominal bolt against a nut with
a clearance, not a toleranced pair. The pass is a hand judgement under D-05, and the table above is a
transcription of a verbal report that the owner confirmed. The bind turns are all 0, so the matrix
gives no measure of how far from passing a tight cell is. Whether 0.15 mm is also the right default
for a part printed upright or on a finer layer is open.


## Printability run (Phase 6, 06-print-run-2)

INFO-04 asks for the printability threshold, the smallest coarse size that prints and threads at the shipped
default clearance, to come from a recorded printed test and not from a forum or vendor figure. This entry
is run 2 of that test, and it is **not run 2 as it was pre-registered**: the owner accepted prints made
before the default shipped (owner ruling R10, `06-OWNER-RULINGS.md`, 2026-10-23). Every departure is listed
under "Where this departs from the protocol" below; none is smoothed over.

**The rule, fixed before the run.** Protocol and reader landed on `main` in PR A (#19), squash commit
`16f7041`, before any part was printed: `06-PRINT-PROTOCOL.md` ("Rules", D-10, D-11) and
`bench/print_rules.py` (`read_small`, `threshold_from`). The threshold is the smallest of M3, M4 and M5
that passes 3 of 3 together with every larger one of the three, and M6 when none does. The owner made no
P3 prediction ("have no idea", 2026-10-22).

**The parts and the default.** The shipped default clearance is 0.15 mm (L17, read from the run-1 record
by `default_from`). The protocol had the nuts come from `python -m bench.print_matrix export run-2`,
which passes no clearance argument, with a manifest committed before the first print. Neither happened:
plan 06-08 Task 1 was not executed under R10 and **no `manifest-run-2.tsv` exists**, because the printed
parts did not come from that export and a manifest committed now would say they did. The owner did not
report where the printed parts came from. The record rests on the owner's statement that the 0.15 mm
result is the one recorded; nothing in the repository ties the printed nuts to the shipped default's
STL bytes.

**The print.** The protocol's one profile (Prusa MK4, 0.4 mm nozzle, Prusa PETG, 0.2 mm layers,
PrusaSlicer, stock Prusa PETG profile; "Print profile" on `main`). Print and test dates: not reported by
the owner (reported 2026-10-23). Plates: each (size, sample) group was printed on its own bed, labelled
M3-1 to M5-3, as in run 1.

**The record, and where it came from.** `bench/results/phase-06/print-run-2.tsv`, sha256
`6c2d924006db1ccca860b665fdc2cbcd3c84137b0edefb417e6c31aab9dd923e`, pinned as `RUN_2_SHA256` in
`bench/print_rules.py`. The owner printed, fit-tested and reported the results in prose. The orchestrating
Claude transcribed that report into the TSV and the owner confirmed it as correct (2026-10-23). The owner
did not type the cells; each is the owner's reported observation as transcribed and confirmed. The agent
that pinned the record changed no cell. The owner's words, as given to Claude Code:

> passed at 0.1 and 0.15, loose at 0.20 and higher

(said of M4 and M5.)

> m2 and m3 were too small for the printer to print thread

The owner also said that at less than 0.1 mm M4 and M5 bound after half a turn.

**The reading.** `threshold_from(read_small(load(RUN_2, RUN_2_SHA256)))`, run through the landed rule and
not by reading the file by eye. The record read cleanly as 9 samples. Passes per size, n of 3:

| size | d | coarse pitch | passes at the default |
|---|---|---|---|
| M3 | 3 | 0.50 | 0/3 |
| M4 | 4 | 0.70 | 3/3 |
| M5 | 5 | 0.80 | 3/3 |

**Outcome (D-10): the threshold is M4, so `d_min` is 4.0 mm and `P_min` is 0.7 mm.** M3 fails 3 of 3, M4
and M5 pass 3 of 3, so the smallest size that passes together with every larger one is M4.
`tests/test_print_rules.py` asserts it: `test_run_2_reads_a_threshold_of_m4_by_d_10` (which also asserts
`COARSE["M4"]` is `(4.0, 0.7)`), with `test_the_run_2_record_is_the_one_pinned` refusing any later byte
change of the record. No M4 or M5 sample is noted `loose` at 0.15 mm.

**Where this departs from the protocol.**

1. The parts were printed before the default shipped. They did not come from `export run-2`, no manifest
   was committed before the first print, and the owner did not report their source.
2. The owner tested a clearance ladder on M4 and M5, not only the default. Only the 0.15 mm result (the
   shipped L17 default) is in the record. The other observations are these prose lines and nothing is
   read from them: passed at 0.1 and 0.15; loose at 0.20 and higher; bound after half a turn below 0.1.
3. M3: the owner reported the thread did not print. The record has only `pass` and `bind`, so each M3
   sample is recorded `bind`, turns `0`, note `thread did not print`. That is a part with no printed
   thread, not a nut that was fitted and stuck; the 0 turns mean no engagement was possible. M2 was
   printed too and is outside the record: it is mentioned here and nothing is read from it.
4. Three samples per size, each (size, sample) group on its own bed (M3-1 to M5-3), not plate sets as
   R4 words them for run 1; the dates were not reported.

**What this shows / what it does not.** It shows that on this printer and profile an M4 (pitch 0.7 mm)
and an M5 (pitch 0.8 mm) nut threaded by hand onto a bolt of the same size in 3 of 3 samples each at
0.15 mm, and that an M3 (pitch 0.5 mm) did not print a thread at all on the 0.4 mm nozzle at 0.2 mm
layers. It does not show anything for another printer, material, layer height, nozzle or orientation. It
covers coarse pitches only: a fine pitch at M4 or above is judged by the `P_min` edge alone (a pitch below
0.7 mm warns), not by a print. M3 is a failure of the printed thread and the record cannot say whether a
finer nozzle or layer would have printed it. Because of departures 1 and 2 the record is weaker evidence
than the pre-registered run would have been: the link from these printed nuts to the shipped default's
export is the owner's word and not a pinned file.

## Acceptance pair (Phase 6, D-16)

HEAD at the run: `de25e58` (branch `gsd/phase-06-printed-pair-acceptance`, 2026-10-23).

The default: nut clearance 0.15 mm, the shipped value (L17), read by the pre-registered D-07 rule from
06-print-run-1. The command passes no clearance, so the default applies.

Command: `.venv/bin/screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8`, exit code 0 (proven).

```json
{
  "verdict": "proven",
  "reasons": [],
  "d": 8.0,
  "pitch": 1.25,
  "m": 6.8,
  "clearance": 0.15,
  "rod_left_hand": false,
  "nut_left_hand": false,
  "readings": [
    {
      "theta": -2.0943951023931953,
      "offset_pitches": 0.0,
      "outcome": "built",
      "solids": 0,
      "volume": 0.0,
      "diag_errors": false,
      "diag_warnings": false,
      "seconds": 6.213970124954358
    },
    {
      "theta": 0.0,
      "offset_pitches": 0.0,
      "outcome": "built",
      "solids": 0,
      "volume": 0.0,
      "diag_errors": false,
      "diag_warnings": false,
      "seconds": 6.748639083001763
    },
    {
      "theta": 2.0943951023931953,
      "offset_pitches": 0.0,
      "outcome": "built",
      "solids": 0,
      "volume": 0.0,
      "diag_errors": false,
      "diag_warnings": false,
      "seconds": 6.207409374997951
    },
    {
      "theta": -2.0943951023931953,
      "offset_pitches": 0.5,
      "outcome": "built",
      "solids": 1,
      "volume": 25.130851304668752,
      "diag_errors": false,
      "diag_warnings": false,
      "seconds": 2.2457348750904202
    },
    {
      "theta": 0.0,
      "offset_pitches": 0.5,
      "outcome": "built",
      "solids": 1,
      "volume": 25.130851554683623,
      "diag_errors": false,
      "diag_warnings": false,
      "seconds": 2.3132786250207573
    },
    {
      "theta": 2.0943951023931953,
      "offset_pitches": 0.5,
      "outcome": "built",
      "solids": 1,
      "volume": 25.13085210490151,
      "diag_errors": false,
      "diag_warnings": false,
      "seconds": 2.332303582923487
    }
  ],
  "closed_control": 25.13083219814244,
  "band": 0.001,
  "engagement_turns": 5.44,
  "shipped": [
    {
      "theta": -2.0943951023931953,
      "outcome": "built",
      "solids": 0,
      "volume": 0.0,
      "seconds": 6.173219583113678,
      "error": null
    },
    {
      "theta": 0.0,
      "outcome": "built",
      "solids": 0,
      "volume": 0.0,
      "seconds": 6.220331999938935,
      "error": null
    },
    {
      "theta": 2.0943951023931953,
      "outcome": "built",
      "solids": 0,
      "volume": 0.0,
      "seconds": 6.259776999941096,
      "error": null
    }
  ],
  "seconds": 50.099970957962796
}
```

Export (CLI default path): `.venv/bin/python -m bench.print_matrix export acceptance -o bench/results/phase-06/stl/acceptance`,
manifest `bench/results/phase-06/manifest-acceptance.tsv`:

| name | bytes | sha256 |
|---|---|---|
| `bolt_d8_pitch1.25_left_hand0_length16_s13_k5.3_thread_length16.stl` | 10449184 | `30f2fca0e0e06a1714f7564097a0e37f1991cc5ba71f98c0bb833f9cf4635814` |
| `nut_d8_pitch1.25_left_hand0_s13_m6.8_clearance0.15.stl` | 4064084 | `4c09af10e06bae18ebbc756eab0968802ef01b8cf4278629a6213414cacc6324` |

Page downloads (2026-10-23, 21:29 local, owner's browser, bolt preset ISO 4017 M8 x 16 and the bolt's
Matching nut link with the clearance field left at its default). The owner named the directory
`~/Downloads/3dprint`, not two file paths; the two files resolved there are listed. Digests recomputed
here with `shasum -a 256` and sizes with `stat`, not taken from the orchestrator's check:

| name | bytes | sha256 | equals manifest |
|---|---|---|---|
| `bolt_d8_pitch1.25_left_hand0_length16_s13_k5.3_thread_length16.stl` | 10449184 | `30f2fca0e0e06a1714f7564097a0e37f1991cc5ba71f98c0bb833f9cf4635814` | yes (name, bytes, digest) |
| `nut_d8_pitch1.25_left_hand0_s13_m6.8_clearance0.15.stl` | 4064084 | `4c09af10e06bae18ebbc756eab0968802ef01b8cf4278629a6213414cacc6324` | yes (name, bytes, digest) |

The page path gave the shipped default's files: both downloads are byte-identical to the pre-registered
CLI default-path exports.

Print date: 21:53, 2026-10-23 (owner's reply). Fresh pair; no matrix or run-2 part counts (D-16).

Owner's fit test: pass. Owner's reply, verbatim: "Path: ~/Downloads/3dprint / Print date: 21:53 10.23.2026 /
Result: pass". The owner reported no turns and no notes beyond `pass`; the hand judgement is D-05's and is
the owner's word, with no mechanical check behind it.

## Phase 7 Runs I

Runner readings of the operability sweep (plan 07-05), taken under `07-SWEEP-PROTOCOL.md` as amended through PR A4 (G1 to G24), on `ubuntu-latest` (07 D-01). Every figure below is `bench.oper summarize` output over the records committed under `bench/results/phase-07/`. Artifacts are downloaded with `gh run download <id> -p 'oper-*'`: the `docker/build-push-action` step also uploads `*.dockerbuild` build-record artifacts that `gh run download <id>` cannot unzip, so the plain command fails; the oper artifacts are the same files either way.

### tracer, run 40645463872

- Dispatched sha: `a142c278f8bba48df8a2405ec7e092d42b725421`
- Records: `bench/results/phase-07/tracer-40645463872/` (5 artifacts, 5 readings), run https://github.com/halfb00t/screw/actions/runs/40645463872
- CPU models seen (jobs): AMD EPYC 7763 64-Core Processor (4); AMD EPYC 9V74 80-Core Processor (1)
- Counts by status: ok: 5
- The five repetitions are five matrix jobs, five runner instances; each built its own image (five image ids, one per job).
- Summary: `python -m bench.oper summarize --markdown --reps 1,2,3,4,5` over the directory, as printed.

### Host

| fact | value |
| --- | --- |
| image | screw:ci |
| image_id | sha256:f296242f753ef18ef3b592fe48c6935643564710a15bbf82eb957cbf3fd5c076, sha256:844d93f21d2d9a5d62c76a5e1c99ae6318db3bbd264d92e0a85063d768c364ed, sha256:491e0343c08bc4276df54328076f59f08d12faa2ecd30b91e8b60afcd36fa8a4, sha256:46fc4c6c5700aef52b342f0600b4d001f827c50479172bb5ab580698b5dc4e84, sha256:0a2a8a1af5e34723aec3bf5fbd10aea2f497285a361d56e403c5a20d191de07c |
| versions | {"cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"} |
| nproc | 4 |
| mem_total_bytes | 16759443456 |
| cpu_model | AMD EPYC 7763 64-Core Processor, AMD EPYC 9V74 80-Core Processor |
| kernel | 7.0.0-1017-azure |
| machine | x86_64 |
| GITHUB_RUN_ID | 40645463872 |
| GITHUB_JOB | measure |
| GITHUB_SHA | a142c278f8bba48df8a2405ec7e092d42b725421 |

### Readings

Status counts: ok: 5

| point | artifact | n | status | counts | median build s | max build s | median export s | max export s | median bytes | max bytes | median peak bytes | max peak bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| default-bolt | stl-preview | 5 | ok | ok: 5 | 1.925 | 1.963 | 0.201 | 0.207 | 1587384 | 1587384 | 225189888 | 226586624 |


### explore, run 40646117094

- Dispatched sha: `7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd`
- Records: `bench/results/phase-07/explore-40646117094/` (40 artifacts, 1692 readings), run https://github.com/halfb00t/screw/actions/runs/40646117094
- CPU models seen (jobs): AMD EPYC 7763 64-Core Processor (14); AMD EPYC 9V45 96-Core Processor (10); AMD EPYC 9V74 80-Core Processor (8); INTEL(R) XEON(R) PLATINUM 8573C (4); Intel(R) Xeon(R) 6973P-C (2); Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz (2)
- Counts by status: capped: 27, killed: 6, ok: 1517, refused: 142
- 40 shards (R4), one repetition per point; a failed reading is data and is in the counts.
- Summary: `python -m bench.oper summarize --markdown --reps 1` over the directory, as printed.

### Host

| fact | value |
| --- | --- |
| image | screw:ci |
| image_id | sha256:12e3727caafd5710b3c2dc3434876d00ce6a867a389ce04445ccb72f0f033270, sha256:a87fb3347cfb7edcf9cbb58679b8d6b3e7f352028fe5504bf489e070713f6510, sha256:7d1c2faefb46f9d800a01594091aed674c9a6896ad535db32ce26678206f7860, sha256:fdeecebc42fc5fe5cee0f5fa9d5045d93627154585dc4fe5be11b18c2a721aa7, sha256:f95d050b93e0dc2596a20c896865d488afb5c56260760a8724a12178c1f0c5de, sha256:15454d4a989d03aff6b658195898a9554fd92a8254f56c4889ce3199d335d740, sha256:705b1fce87255e692cd36352801d684056059d36336ffab5fed05f47804a694b, sha256:2507744b1ccb9dfa9731b7a5ef9cad360d6a6ad389e5217c50b1744ad597aa30, sha256:ea4ec411e307f3bb144cad2f6c7d24c9b4ed937823158c1da5f143a6e6ee5864, sha256:fa7431e2947a1ed700990469465089da2870a010b2c64ed32ea3d633771a806e, sha256:bcad84eb1c0bd93ecbb997d82864e54cf9ba544cd94d6f53eff44c348495e515, sha256:140168aa4606768b6fbbe509d08976ecc54ed9f8ec1ff5634c8bb3500a4b3005, sha256:a2cd129a93694e4cf6bb80990093ed4d5b6dfdd00640802a306372ad9f379aae, sha256:a213633fc0c953939c36a44cfaad0c78346e4f340e68f327cc10e1b68400de29, sha256:3eae8cdfef82c2d1aaa1f0d517582137c9d94f72cf58ab129646dfe2f6e780f1, sha256:e14d7e4a830294a6419cbf348e1efdd4798b89a6e7fdf757e4f05e923e2d26e2, sha256:1e669a7a14f485b5c6fd1d5dd6028cd5e77d4f55b20cad308a5a05b97569f965, sha256:26404788eb859a3c7f87ed1cc14853190b105d9b2acdae016ed040a040569195, sha256:51baa75483ae06589fb65feabc68a2eff104202a2fa1b36eb79d7e35ee0ea1a2, sha256:78de5e9f3b7a59f65818c91b1d822b69a129ebe033d656f167c04ea24f6004ed, sha256:242c1f6633f19548a8197877aedfd395c1cee5ca6b4102d3bf8194d7b7b30617, sha256:64eeb09a26542d624de12adcccbe51b0069f52cd00812bfb97ce77dcb70a0341, sha256:1edcfe8e55d43b306b11fcc6d96fc7d75e62a7ffe46e36c04e50004d86177010, sha256:8d57cbbdc5a829f2c3aa7bb8f3f9d9d5433cc83a5556ec9eeeaa114c0c8b7f2b, sha256:41f982c37badc2612347b7790ff1f181a6ae91c0eb127f22b598aa248a2ba7a0, sha256:742a2901d494ada68da4433e2e770b5ec899bb7ce033dadaf9f913ce39f30b5f, sha256:54a5c21a1efa8425ed48c820d8dee5422c28870af21a264208e56d04d2eec6e4, sha256:dafce62a6f6c0cdd82ef782cd4a4938564a5c19e9f6eede68d178733d66cdc78, sha256:1eb051850ecdfb7c9ac1613fd833924c2afcf59b84b1500983658935dd8ac2d7, sha256:6bbbcd03148c75ab2ff8c7bb6e94d5e2190fac9184252e8386149ddca637e57a, sha256:9b6d624be124f5f25a5b129c75f632c257f21a6a1ce9ecae3cc75845f2741a19, sha256:ae3cdec0ee13af2ae89fd580cade9bf192d3d4999752ed8d91847df187bfdf2c, sha256:30daefb006a98ac08cee0aa9dc60b04e63813defa1a931ded108d9fff9e327bb, sha256:c0572a65be3059c54e671fb6b22c9f095359fade01a063cb5b6d4a2853dc3249, sha256:b236766f7b21443f5a54107e6d30fb7ff0651add68fc5ef9b6e570302a9f73b9, sha256:b1d2f709926d65d26ef726c8573845239db6b4a7869a1adfce3870d463f96065, sha256:4a619acace5331ec6b373851f1ab23c17f9fbcee4afe2863644b0006ca312593, sha256:369ce9012aa2408d89a82b72489b3ac479a6606218a7e83fdbb79fd57cfb507d, sha256:f461165fa618c6bfcea90a9703fb10ff5b7f25a3dc2f73d5f40d66f7295a9902, sha256:1331d0aa82fffcaab234ecf05a9a289166220a96a1576a0c398989324a494adc |
| versions | {"cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"} |
| nproc | 4 |
| mem_total_bytes | 16759439360, 16759443456, 16758407168, 16758403072, 16759435264, 16759447552 |
| cpu_model | AMD EPYC 9V45 96-Core Processor, AMD EPYC 7763 64-Core Processor, INTEL(R) XEON(R) PLATINUM 8573C, AMD EPYC 9V74 80-Core Processor, Intel(R) Xeon(R) 6973P-C, Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz |
| kernel | 7.0.0-1017-azure |
| machine | x86_64 |
| GITHUB_RUN_ID | 40646117094 |
| GITHUB_JOB | measure |
| GITHUB_SHA | 7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd |

### Readings

Status counts: ok: 1517, refused: 142, killed: 6, capped: 27

| point | artifact | n | status | counts | median build s | max build s | median export s | max export s | median bytes | max bytes | median peak bytes | max peak bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iso4017:M2x4 | stl-preview | 1 | ok | ok: 1 | 0.847 | 0.847 | 0.034 | 0.034 | 383584 | 383584 | 215400448 | 215400448 |
| iso4017:M2.5x16 | stl-fine | 1 | ok | ok: 1 | 2.351 | 2.351 | 1.416 | 1.416 | 13294784 | 13294784 | 308310016 | 308310016 |
| iso4017:M3.5x12 | step | 1 | ok | ok: 1 | 1.229 | 1.229 | 0.034 | 0.034 | 1171493 | 1171493 | 217931776 | 217931776 |
| iso4017:M4x40 | stl-preview | 1 | ok | ok: 1 | 2.219 | 2.219 | 0.231 | 0.231 | 2969384 | 2969384 | 237129728 | 237129728 |
| iso4017:M6x20 | stl-fine | 1 | ok | ok: 1 | 1.188 | 1.188 | 1.191 | 1.191 | 10592984 | 10592984 | 326942720 | 326942720 |
| iso4017:M7x35 | step | 1 | ok | ok: 1 | 1.814 | 1.814 | 0.061 | 0.061 | 2216824 | 2216824 | 234672128 | 234672128 |
| iso4017:M8x45 | stl-preview | 1 | ok | ok: 1 | 1.767 | 1.767 | 0.227 | 0.227 | 3047984 | 3047984 | 235307008 | 235307008 |
| iso4017:M10x50 | stl-fine | 1 | ok | ok: 1 | 1.627 | 1.627 | 4.317 | 4.317 | 41317684 | 41317684 | 531861504 | 531861504 |
| iso4017:M12x50 | step | 1 | ok | ok: 1 | 1.570 | 1.570 | 0.051 | 0.051 | 1881029 | 1881029 | 226496512 | 226496512 |
| iso4017:M14x50 | stl-preview | 1 | ok | ok: 1 | 1.384 | 1.384 | 0.208 | 0.208 | 2572384 | 2572384 | 231116800 | 231116800 |
| iso4017:M16x35 | stl-fine | 1 | ok | ok: 1 | 1.228 | 1.228 | 3.302 | 3.302 | 30799484 | 30799484 | 596488192 | 596488192 |
| iso4017:M16x130 | step | 1 | ok | ok: 1 | 2.800 | 2.800 | 0.109 | 0.109 | 4151716 | 4151716 | 268312576 | 268312576 |
| iso4017:M18x100 | stl-preview | 1 | ok | ok: 1 | 1.970 | 1.970 | 0.752 | 0.752 | 10153384 | 10153384 | 258752512 | 258752512 |
| iso4017:M20x65 | stl-fine | 1 | ok | ok: 1 | 1.514 | 1.514 | 5.062 | 5.062 | 47873084 | 47873084 | 619479040 | 619479040 |
| iso4014:M2x16 | step | 1 | ok | ok: 1 | 2.154 | 2.154 | 0.038 | 0.038 | 1434086 | 1434086 | 221982720 | 221982720 |
| iso4014:M4x35 | stl-preview | 1 | ok | ok: 1 | 1.470 | 1.470 | 0.085 | 0.085 | 1074884 | 1074884 | 219615232 | 219615232 |
| iso4014:M6x55 | stl-fine | 1 | ok | ok: 1 | 1.414 | 1.414 | 0.971 | 0.971 | 9559584 | 9559584 | 336703488 | 336703488 |
| iso4014:M8x55 | step | 1 | ok | ok: 1 | 1.555 | 1.555 | 0.034 | 0.034 | 1209363 | 1209363 | 222580736 | 222580736 |
| iso4014:M12x50 | stl-preview | 1 | ok | ok: 1 | 1.456 | 1.456 | 0.136 | 0.136 | 1735684 | 1735684 | 224141312 | 224141312 |
| iso4014:M14x70 | stl-fine | 1 | ok | ok: 1 | 1.511 | 1.511 | 2.990 | 2.990 | 27923284 | 27923284 | 580960256 | 580960256 |
| iso4014:M16x110 | step | 1 | ok | ok: 1 | 1.510 | 1.510 | 0.039 | 0.039 | 1352663 | 1352663 | 224518144 | 224518144 |
| iso4014:M18x150 | stl-preview | 1 | ok | ok: 1 | 1.566 | 1.566 | 0.352 | 0.352 | 4787684 | 4787684 | 239067136 | 239067136 |
| iso4014:M20x200 | stl-fine | 1 | ok | ok: 1 | 1.794 | 1.794 | 3.926 | 3.926 | 37736784 | 37736784 | 608579584 | 608579584 |
| iso4032:M18 | step | 1 | ok | ok: 1 | 1.576 | 1.576 | 0.026 | 0.026 | 838183 | 838183 | 214396928 | 214396928 |
| bolt-d3-p0.1-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n3-left | stl-fine | 1 | ok | ok: 1 | 0.534 | 0.534 | 0.148 | 0.148 | 981484 | 981484 | 261455872 | 261455872 |
| bolt-d10-p0.35-n30-right | step | 1 | ok | ok: 1 | 2.140 | 2.140 | 0.053 | 0.053 | 1972908 | 1972908 | 234754048 | 234754048 |
| bolt-d10-p3-n240-right | stl-preview | 1 | ok | ok: 1 | 8.672 | 8.672 | 1.928 | 1.928 | 25922484 | 25922484 | 441364480 | 441364480 |
| bolt-d30-p0.35-n240-left | stl-fine | 1 | ok | ok: 1 | 9.549 | 9.549 | 79.712 | 79.712 | 682273884 | 682273884 | 2231574528 | 2231574528 |
| bolt-d30-p10-n3-right | step | 1 | ok | ok: 1 | 0.530 | 0.530 | 0.014 | 0.014 | 353610 | 353610 | 209096704 | 209096704 |
| bolt-d100-p0.35-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n30-left | stl-fine | 1 | ok | ok: 1 | 2.014 | 2.014 | 45.088 | 45.088 | 145794484 | 145794484 | 2581401600 | 2581401600 |
| bolt-d300-p0.1-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n3-right | stl-preview | 1 | ok | ok: 1 | 1.090 | 1.090 | 2.587 | 2.587 | 13989584 | 13989584 | 769880064 | 769880064 |
| bolt-d1000-p0.1-n3-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n30-right | step | 1 | ok | ok: 1 | 3.991 | 3.991 | 0.113 | 0.113 | 4222247 | 4222247 | 251359232 | 251359232 |
| bolt-d1000-p10-n240-right | stl-preview | 1 | killed | killed: 1 | - | - | - | - | - | - | - | - |
| nut-d10-p0.35-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 8.435 | 8.435 | 11.474 | 11.474 | 111225284 | 111225284 | 716181504 | 716181504 |
| nut-d10-p3.5-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 1.413 | 1.413 | 0.028 | 0.028 | 862779 | 862779 | 213876736 | 213876736 |
| nut-d30-p3.5-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 1.688 | 1.688 | 0.143 | 0.143 | 1702284 | 1702284 | 234098688 | 234098688 |
| nut-d100-p1-m0.8d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 9.915 | 9.915 | 132.918 | 132.918 | 514616084 | 514616084 | 3467792384 | 3467792384 |
| nut-d3-p1-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 0.980 | 0.980 | 0.016 | 0.016 | 450023 | 450023 | 214650880 | 214650880 |
| nut-d100-p1-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 8.618 | 8.618 | 5.924 | 5.924 | 65459484 | 65459484 | 475127808 | 475127808 |
| iso4017:M2x8 | stl-preview | 1 | ok | ok: 1 | 2.259 | 2.259 | 0.110 | 0.110 | 757284 | 757284 | 218312704 | 218312704 |
| iso4017:M3x6 | stl-fine | 1 | ok | ok: 1 | 1.676 | 1.676 | 0.955 | 0.955 | 4634984 | 4634984 | 290484224 | 290484224 |
| iso4017:M3.5x25 | step | 1 | ok | ok: 1 | 3.016 | 3.016 | 0.108 | 0.108 | 2344243 | 2344243 | 244092928 | 244092928 |
| iso4017:M5x16 | stl-preview | 1 | ok | ok: 1 | 2.022 | 2.022 | 0.198 | 0.198 | 1458484 | 1458484 | 225214464 | 225214464 |
| iso4017:M6x35 | stl-fine | 1 | ok | ok: 1 | 2.790 | 2.790 | 3.426 | 3.426 | 18187384 | 18187384 | 341585920 | 341585920 |
| iso4017:M7x50 | step | 1 | ok | ok: 1 | 3.574 | 3.574 | 0.130 | 0.130 | 3111484 | 3111484 | 262946816 | 262946816 |
| iso4017:M8x60 | stl-preview | 1 | ok | ok: 1 | 3.407 | 3.407 | 0.532 | 0.532 | 4064384 | 4064384 | 248623104 | 248623104 |
| iso4017:M10x65 | stl-fine | 1 | ok | ok: 1 | 3.112 | 3.112 | 8.838 | 8.838 | 53750484 | 53750484 | 546373632 | 546373632 |
| iso4017:M12x65 | step | 1 | ok | ok: 1 | 2.806 | 2.806 | 0.119 | 0.119 | 2394219 | 2394219 | 251453440 | 251453440 |
| iso4017:M14x65 | stl-preview | 1 | ok | ok: 1 | 2.697 | 2.697 | 0.609 | 0.609 | 3351284 | 3351284 | 249982976 | 249982976 |
| iso4017:M16x50 | stl-fine | 1 | ok | ok: 1 | 2.352 | 2.352 | 8.505 | 8.505 | 43410184 | 43410184 | 591454208 | 591454208 |
| iso4017:M16x160 | step | 1 | ok | ok: 1 | 5.247 | 5.247 | 0.215 | 0.215 | 5064590 | 5064590 | 293961728 | 293961728 |
| iso4017:M18x130 | stl-preview | 1 | ok | ok: 1 | 3.768 | 3.768 | 1.696 | 1.696 | 13227784 | 13227784 | 276992000 | 276992000 |
| iso4017:M20x90 | stl-fine | 1 | ok | ok: 1 | 2.898 | 2.898 | 10.859 | 10.859 | 64249184 | 64249184 | 675340288 | 675340288 |
| iso4014:M2.5x20 | step | 1 | ok | ok: 1 | 3.280 | 3.280 | 0.064 | 0.064 | 1413363 | 1413363 | 231677952 | 231677952 |
| iso4014:M5x30 | stl-preview | 1 | ok | ok: 1 | 2.455 | 2.455 | 0.196 | 0.196 | 1481784 | 1481784 | 223285248 | 223285248 |
| iso4014:M7x40 | stl-fine | 1 | ok | ok: 1 | 2.231 | 2.231 | 2.222 | 2.222 | 11039884 | 11039884 | 341155840 | 341155840 |
| iso4014:M8x70 | step | 1 | ok | ok: 1 | 2.471 | 2.471 | 0.053 | 0.053 | 1209364 | 1209364 | 220856320 | 220856320 |
| iso4014:M12x65 | stl-preview | 1 | ok | ok: 1 | 2.361 | 2.361 | 0.247 | 0.247 | 1735684 | 1735684 | 224342016 | 224342016 |
| iso4014:M14x100 | stl-fine | 1 | ok | ok: 1 | 2.409 | 2.409 | 5.245 | 5.245 | 27923284 | 27923284 | 567664640 | 567664640 |
| iso4014:M16x140 | step | 1 | ok | ok: 1 | 2.610 | 2.610 | 0.067 | 0.067 | 1536996 | 1536996 | 222367744 | 222367744 |
| iso4014:M20x80 | stl-preview | 1 | ok | ok: 1 | 2.354 | 2.354 | 0.656 | 0.656 | 5248684 | 5248684 | 249880576 | 249880576 |
| iso4032:M3 | stl-fine | 1 | ok | ok: 1 | 2.597 | 2.597 | 0.460 | 0.460 | 1942684 | 1942684 | 275488768 | 275488768 |
| bolt-d1-p0.1-n3-left | step | 1 | ok | ok: 1 | 0.874 | 0.874 | 0.017 | 0.017 | 284347 | 284347 | 209518592 | 209518592 |
| bolt-d3-p0.1-n30-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.35-n240-left | step | 1 | ok | ok: 1 | 14.548 | 14.548 | 0.617 | 0.617 | 14714979 | 14714979 | 436240384 | 436240384 |
| bolt-d30-p0.1-n3-left | stl-preview | 1 | ok | ok: 1 | 2.319 | 2.319 | 0.119 | 0.119 | 774184 | 774184 | 228646912 | 228646912 |
| bolt-d30-p1-n30-right | stl-fine | 1 | ok | ok: 1 | 3.003 | 3.003 | 16.353 | 16.353 | 79070384 | 79070384 | 981315584 | 981315584 |
| bolt-d30-p10-n30-left | step | 1 | ok | ok: 1 | 2.159 | 2.159 | 0.091 | 0.091 | 2060389 | 2060389 | 229924864 | 229924864 |
| bolt-d100-p0.35-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p10-n3-right | stl-fine | 1 | ok | ok: 1 | 1.133 | 1.133 | 8.328 | 8.328 | 25059584 | 25059584 | 1572552704 | 1572552704 |
| bolt-d300-p0.35-n3-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n30-left | stl-preview | 1 | ok | ok: 1 | 2.934 | 2.934 | 25.695 | 25.695 | 117009884 | 117009884 | 1110220800 | 1110220800 |
| bolt-d1000-p0.1-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n240-left | step | 1 | ok | ok: 1 | 14.541 | 14.541 | 1.243 | 1.243 | 28965722 | 28965722 | 570269696 | 570269696 |
| nut-d3-p0.35-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 2.592 | 2.592 | 0.048 | 0.048 | 306484 | 306484 | 211726336 | 211726336 |
| nut-d10-p1-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 2.834 | 2.834 | 1.662 | 1.662 | 8009484 | 8009484 | 402251776 | 402251776 |
| nut-d30-p0.35-m0.8d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 10.965 | 10.965 | 0.210 | 0.210 | 4649127 | 4649127 | 393736192 | 393736192 |
| nut-d30-p3.5-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 1.397 | 1.397 | 0.411 | 0.411 | 2615484 | 2615484 | 234201088 | 234201088 |
| nut-d100-p3.5-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 6.445 | 6.445 | 41.185 | 41.185 | 135745784 | 135745784 | 2564919296 | 2564919296 |
| nut-d10-p0.35-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 12.965 | 12.965 | 0.226 | 0.226 | 5515581 | 5515581 | 259907584 | 259907584 |
| corner-d100-L200 | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| iso4017:M2x8 | stl-fine | 1 | ok | ok: 1 | 2.290 | 2.290 | 1.315 | 1.315 | 6208284 | 6208284 | 276824064 | 276824064 |
| iso4017:M3x6 | step | 1 | ok | ok: 1 | 1.649 | 1.649 | 0.035 | 0.035 | 758724 | 758724 | 212811776 | 212811776 |
| iso4017:M3.5x30 | stl-preview | 1 | ok | ok: 1 | 3.331 | 3.331 | 0.352 | 0.352 | 2334084 | 2334084 | 243433472 | 243433472 |
| iso4017:M5x16 | stl-fine | 1 | ok | ok: 1 | 1.933 | 1.933 | 1.881 | 1.881 | 9763584 | 9763584 | 324288512 | 324288512 |
| iso4017:M6x35 | step | 1 | ok | ok: 1 | 2.783 | 2.783 | 0.091 | 0.091 | 2200014 | 2200014 | 235732992 | 235732992 |
| iso4017:M7x55 | stl-preview | 1 | ok | ok: 1 | 3.711 | 3.711 | 0.559 | 0.559 | 4593984 | 4593984 | 257748992 | 257748992 |
| iso4017:M8x60 | stl-fine | 1 | ok | ok: 1 | 3.404 | 3.404 | 7.092 | 7.092 | 40912184 | 40912184 | 426070016 | 426070016 |
| iso4017:M10x65 | step | 1 | ok | ok: 1 | 3.092 | 3.092 | 0.112 | 0.112 | 2517426 | 2517426 | 248778752 | 248778752 |
| iso4017:M12x70 | stl-preview | 1 | ok | ok: 1 | 2.998 | 2.998 | 0.617 | 0.617 | 3865284 | 3865284 | 253722624 | 253722624 |
| iso4017:M14x65 | stl-fine | 1 | ok | ok: 1 | 2.686 | 2.686 | 9.802 | 9.802 | 53714584 | 53714584 | 651653120 | 651653120 |
| iso4017:M16x50 | step | 1 | ok | ok: 1 | 2.362 | 2.362 | 0.074 | 0.074 | 1712826 | 1712826 | 233238528 | 233238528 |
| iso4017:M18x35 | stl-preview | 1 | ok | ok: 1 | 1.715 | 1.715 | 0.460 | 0.460 | 3385184 | 3385184 | 236810240 | 236810240 |
| iso4017:M18x130 | stl-fine | 1 | ok | ok: 1 | 3.777 | 3.777 | 15.724 | 15.724 | 91705584 | 91705584 | 743215104 | 743215104 |
| iso4017:M20x90 | step | 1 | ok | ok: 1 | 2.903 | 2.903 | 0.105 | 0.105 | 2380331 | 2380331 | 254304256 | 254304256 |
| iso4014:M2.5x25 | stl-preview | 1 | ok | ok: 1 | 3.426 | 3.426 | 0.148 | 0.148 | 1039184 | 1039184 | 231583744 | 231583744 |
| iso4014:M5x30 | stl-fine | 1 | ok | ok: 1 | 2.463 | 2.463 | 1.850 | 1.850 | 10190184 | 10190184 | 337235968 | 337235968 |
| iso4014:M7x40 | step | 1 | ok | ok: 1 | 2.236 | 2.236 | 0.057 | 0.057 | 1327433 | 1327433 | 225730560 | 225730560 |
| iso4014:M8x80 | stl-preview | 1 | ok | ok: 1 | 2.472 | 2.472 | 0.199 | 0.199 | 1541284 | 1541284 | 222912512 | 222912512 |
| iso4014:M12x65 | stl-fine | 1 | ok | ok: 1 | 2.340 | 2.340 | 4.335 | 4.335 | 23581884 | 23581884 | 487120896 | 487120896 |
| iso4014:M14x100 | step | 1 | ok | ok: 1 | 2.399 | 2.399 | 0.053 | 0.053 | 1203708 | 1203708 | 221331456 | 221331456 |
| iso4014:M16x150 | stl-preview | 1 | ok | ok: 1 | 2.630 | 2.630 | 0.598 | 0.598 | 3640284 | 3640284 | 247656448 | 247656448 |
| iso4014:M20x80 | stl-fine | 1 | ok | ok: 1 | 2.340 | 2.340 | 5.914 | 5.914 | 33255884 | 33255884 | 606826496 | 606826496 |
| iso4032:M3 | step | 1 | ok | ok: 1 | 2.573 | 2.573 | 0.028 | 0.028 | 564242 | 564242 | 213479424 | 213479424 |
| bolt-d1-p0.1-n30-right | stl-preview | 1 | ok | ok: 1 | 3.241 | 3.241 | 0.152 | 0.152 | 1265784 | 1265784 | 238518272 | 238518272 |
| bolt-d3-p0.1-n30-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p1-n3-right | stl-preview | 1 | ok | ok: 1 | 1.007 | 1.007 | 0.043 | 0.043 | 266984 | 266984 | 212733952 | 212733952 |
| bolt-d30-p0.1-n3-left | stl-fine | 1 | ok | ok: 1 | 2.307 | 2.307 | 2.109 | 2.109 | 8481484 | 8481484 | 559980544 | 559980544 |
| bolt-d30-p1-n30-right | step | 1 | ok | ok: 1 | 2.981 | 2.981 | 0.094 | 0.094 | 2065574 | 2065574 | 243412992 | 243412992 |
| bolt-d30-p10-n240-right | stl-preview | 1 | ok | ok: 1 | 10.246 | 10.246 | 10.253 | 10.253 | 85756584 | 85756584 | 566083584 | 566083584 |
| bolt-d100-p0.35-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p10-n3-right | step | 1 | ok | ok: 1 | 1.119 | 1.119 | 0.022 | 0.022 | 417400 | 417400 | 211226624 | 211226624 |
| bolt-d300-p0.35-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n30-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.1-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n3-right | stl-preview | 1 | ok | ok: 1 | 3.358 | 3.358 | 14.812 | 14.812 | 41011484 | 41011484 | 2992689152 | 2992689152 |
| nut-d3-p0.35-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 2.648 | 2.648 | 0.555 | 0.555 | 2619984 | 2619984 | 293478400 | 293478400 |
| nut-d10-p1-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 2.798 | 2.798 | 0.038 | 0.038 | 842747 | 842747 | 221679616 | 221679616 |
| nut-d30-p0.35-m0.8d-s4d-c0.15-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nut-d30-p3.5-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 1.368 | 1.368 | 8.155 | 8.155 | 34789784 | 34789784 | 925065216 | 925065216 |
| nut-d100-p3.5-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 6.412 | 6.412 | 0.084 | 0.084 | 1864447 | 1864447 | 234921984 | 234921984 |
| nut-d10-p1-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 2.821 | 2.821 | 0.093 | 0.093 | 529184 | 529184 | 225353728 | 225353728 |
| corner-d100-p5-L1250 | stl-fine | 1 | ok | ok: 1 | 11.450 | 11.450 | 531.587 | 531.587 | 1871845384 | 1871845384 | 6673383424 | 6673383424 |
| iso4017:M2x8 | step | 1 | ok | ok: 1 | 1.467 | 1.467 | 0.033 | 0.033 | 1151195 | 1151195 | 218398720 | 218398720 |
| iso4017:M3x8 | stl-preview | 1 | ok | ok: 1 | 1.223 | 1.223 | 0.061 | 0.061 | 705684 | 705684 | 216399872 | 216399872 |
| iso4017:M3.5x30 | stl-fine | 1 | ok | ok: 1 | 2.170 | 2.170 | 2.465 | 2.465 | 19768184 | 19768184 | 327675904 | 327675904 |
| iso4017:M5x16 | step | 1 | ok | ok: 1 | 1.261 | 1.261 | 0.037 | 0.037 | 1299972 | 1299972 | 223207424 | 223207424 |
| iso4017:M6x40 | stl-preview | 1 | ok | ok: 1 | 1.914 | 1.914 | 0.227 | 0.227 | 3234384 | 3234384 | 240504832 | 240504832 |
| iso4017:M7x55 | stl-fine | 1 | ok | ok: 1 | 2.402 | 2.402 | 3.211 | 3.211 | 29322984 | 29322984 | 353386496 | 353386496 |
| iso4017:M8x60 | step | 1 | ok | ok: 1 | 2.189 | 2.189 | 0.080 | 0.080 | 3018502 | 3018502 | 244342784 | 244342784 |
| iso4017:M10x70 | stl-preview | 1 | ok | ok: 1 | 2.164 | 2.164 | 0.316 | 0.316 | 4193384 | 4193384 | 242216960 | 242216960 |
| iso4017:M12x70 | stl-fine | 1 | ok | ok: 1 | 1.945 | 1.945 | 5.745 | 5.745 | 54548884 | 54548884 | 555360256 | 555360256 |
| iso4017:M14x65 | step | 1 | ok | ok: 1 | 1.721 | 1.721 | 0.058 | 0.058 | 2143835 | 2143835 | 237830144 | 237830144 |
| iso4017:M16x55 | stl-preview | 1 | ok | ok: 1 | 1.611 | 1.611 | 0.377 | 0.377 | 4509184 | 4509184 | 240050176 | 240050176 |
| iso4017:M18x35 | stl-fine | 1 | ok | ok: 1 | 1.091 | 1.091 | 2.684 | 2.684 | 24620984 | 24620984 | 586321920 | 586321920 |
| iso4017:M18x130 | step | 1 | ok | ok: 1 | 2.402 | 2.402 | 0.090 | 0.090 | 3377724 | 3377724 | 251936768 | 251936768 |
| iso4017:M20x100 | stl-preview | 1 | ok | ok: 1 | 1.977 | 1.977 | 0.729 | 0.729 | 11445984 | 11445984 | 263299072 | 263299072 |
| iso4014:M2.5x25 | stl-fine | 1 | ok | ok: 1 | 2.218 | 2.218 | 0.960 | 0.960 | 9579284 | 9579284 | 287633408 | 287633408 |
| iso4014:M5x30 | step | 1 | ok | ok: 1 | 1.610 | 1.610 | 0.037 | 0.037 | 1307957 | 1307957 | 222162944 | 222162944 |
| iso4014:M7x45 | stl-preview | 1 | ok | ok: 1 | 1.432 | 1.432 | 0.120 | 0.120 | 1646684 | 1646684 | 224067584 | 224067584 |
| iso4014:M8x80 | stl-fine | 1 | ok | ok: 1 | 1.580 | 1.580 | 1.524 | 1.524 | 14707484 | 14707484 | 371896320 | 371896320 |
| iso4014:M12x65 | step | 1 | ok | ok: 1 | 1.514 | 1.514 | 0.034 | 0.034 | 1187165 | 1187165 | 223477760 | 223477760 |
| iso4014:M14x110 | stl-preview | 1 | ok | ok: 1 | 1.591 | 1.591 | 0.156 | 0.156 | 1835884 | 1835884 | 228024320 | 228024320 |
| iso4014:M16x150 | stl-fine | 1 | ok | ok: 1 | 1.714 | 1.714 | 4.109 | 4.109 | 38614184 | 38614184 | 615268352 | 615268352 |
| iso4014:M20x80 | step | 1 | ok | ok: 1 | 1.530 | 1.530 | 0.039 | 0.039 | 1333947 | 1333947 | 223158272 | 223158272 |
| iso4032:M3.5 | stl-preview | 1 | ok | ok: 1 | 1.495 | 1.495 | 0.021 | 0.021 | 222384 | 222384 | 213905408 | 213905408 |
| bolt-d1-p0.1-n30-right | stl-fine | 1 | ok | ok: 1 | 2.077 | 2.077 | 0.903 | 0.903 | 9066784 | 9066784 | 263163904 | 263163904 |
| bolt-d3-p0.1-n30-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n240-left | stl-preview | 1 | ok | ok: 1 | 18.010 | 18.010 | 0.742 | 0.742 | 8744184 | 8744184 | 326705152 | 326705152 |
| bolt-d10-p1-n3-right | stl-fine | 1 | ok | ok: 1 | 0.660 | 0.660 | 0.560 | 0.560 | 3542084 | 3542084 | 357982208 | 357982208 |
| bolt-d30-p0.1-n3-left | step | 1 | ok | ok: 1 | 1.518 | 1.518 | 0.017 | 0.017 | 462251 | 462251 | 210698240 | 210698240 |
| bolt-d30-p1-n30-left | stl-preview | 1 | ok | ok: 1 | 2.000 | 2.000 | 0.555 | 0.555 | 7589584 | 7589584 | 251375616 | 251375616 |
| bolt-d30-p10-n240-right | stl-fine | 1 | ok | ok: 1 | 6.675 | 6.675 | 73.302 | 73.302 | 681120484 | 681120484 | 2537066496 | 2537066496 |
| bolt-d100-p0.35-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p10-n3-left | stl-preview | 1 | ok | ok: 1 | 0.750 | 0.750 | 0.328 | 0.328 | 2912784 | 2912784 | 308801536 | 308801536 |
| bolt-d300-p0.35-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n30-left | step | 1 | ok | ok: 1 | 1.925 | 1.925 | 0.085 | 0.085 | 2776707 | 2776707 | 234713088 | 234713088 |
| bolt-d1000-p0.1-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n3-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p0.35-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 1.720 | 1.720 | 0.024 | 0.024 | 736540 | 736540 | 209661952 | 209661952 |
| nut-d10-p1-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 1.594 | 1.594 | 0.056 | 0.056 | 648584 | 648584 | 215146496 | 215146496 |
| nut-d30-p0.35-m0.8d-s4d-c0.15-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nut-d30-p3.5-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 0.914 | 0.914 | 0.026 | 0.026 | 771048 | 771048 | 211128320 | 211128320 |
| nut-d100-p3.5-m0.8d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 4.387 | 4.387 | 2.620 | 2.620 | 27817884 | 27817884 | 412880896 | 412880896 |
| nut-d10-p1-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 1.884 | 1.884 | 0.794 | 0.794 | 6554584 | 6554584 | 368345088 | 368345088 |
| corner-d6-p0.1-L25 | stl-fine | 1 | ok | ok: 1 | 11.212 | 11.212 | 12.822 | 12.822 | 108951084 | 108951084 | 679555072 | 679555072 |
| iso4017:M2x10 | stl-preview | 1 | ok | ok: 1 | 1.679 | 1.679 | 0.077 | 0.077 | 955084 | 955084 | 221634560 | 221634560 |
| iso4017:M3x8 | stl-fine | 1 | ok | ok: 1 | 1.232 | 1.232 | 0.741 | 0.741 | 6239384 | 6239384 | 294998016 | 294998016 |
| iso4017:M3.5x30 | step | 1 | ok | ok: 1 | 2.166 | 2.166 | 0.117 | 0.117 | 2770782 | 2770782 | 236290048 | 236290048 |
| iso4017:M5x20 | stl-preview | 1 | ok | ok: 1 | 1.331 | 1.331 | 0.139 | 0.139 | 1861884 | 1861884 | 229756928 | 229756928 |
| iso4017:M6x40 | stl-fine | 1 | ok | ok: 1 | 1.850 | 1.850 | 2.321 | 2.321 | 20338484 | 20338484 | 360259584 | 360259584 |
| iso4017:M7x55 | step | 1 | ok | ok: 1 | 2.359 | 2.359 | 0.117 | 0.117 | 3428258 | 3428258 | 251363328 | 251363328 |
| iso4017:M8x65 | stl-preview | 1 | ok | ok: 1 | 2.297 | 2.297 | 0.340 | 0.340 | 4406984 | 4406984 | 254496768 | 254496768 |
| iso4017:M10x70 | stl-fine | 1 | ok | ok: 1 | 2.118 | 2.118 | 5.869 | 5.869 | 57701884 | 57701884 | 550027264 | 550027264 |
| iso4017:M12x70 | step | 1 | ok | ok: 1 | 1.893 | 1.893 | 0.069 | 0.069 | 2562932 | 2562932 | 243183616 | 243183616 |
| iso4017:M14x70 | stl-preview | 1 | ok | ok: 1 | 1.792 | 1.792 | 0.308 | 0.308 | 3640084 | 3640084 | 239755264 | 239755264 |
| iso4017:M16x55 | stl-fine | 1 | ok | ok: 1 | 1.569 | 1.569 | 5.112 | 5.112 | 47540884 | 47540884 | 644558848 | 644558848 |
| iso4017:M18x35 | step | 1 | ok | ok: 1 | 1.065 | 1.065 | 0.029 | 0.029 | 1025099 | 1025099 | 220852224 | 220852224 |
| iso4017:M18x140 | stl-preview | 1 | ok | ok: 1 | 2.519 | 2.519 | 1.034 | 1.034 | 14139684 | 14139684 | 287449088 | 287449088 |
| iso4017:M20x100 | stl-fine | 1 | ok | ok: 1 | 1.974 | 1.974 | 7.526 | 7.526 | 71563784 | 71563784 | 678555648 | 678555648 |
| iso4014:M2.5x25 | step | 1 | ok | ok: 1 | 2.226 | 2.226 | 0.041 | 0.041 | 1413393 | 1413393 | 218673152 | 218673152 |
| iso4014:M5x35 | stl-preview | 1 | ok | ok: 1 | 1.624 | 1.624 | 0.115 | 0.115 | 1481784 | 1481784 | 224088064 | 224088064 |
| iso4014:M7x45 | stl-fine | 1 | ok | ok: 1 | 1.434 | 1.434 | 1.272 | 1.272 | 11039884 | 11039884 | 325312512 | 325312512 |
| iso4014:M8x80 | step | 1 | ok | ok: 1 | 1.610 | 1.610 | 0.036 | 0.036 | 1209364 | 1209364 | 221933568 | 221933568 |
| iso4014:M12x70 | stl-preview | 1 | ok | ok: 1 | 1.513 | 1.513 | 0.145 | 0.145 | 1735684 | 1735684 | 226082816 | 226082816 |
| iso4014:M14x110 | stl-fine | 1 | ok | ok: 1 | 1.589 | 1.589 | 3.290 | 3.290 | 27923284 | 27923284 | 585043968 | 585043968 |
| iso4014:M16x150 | step | 1 | ok | ok: 1 | 1.719 | 1.719 | 0.044 | 0.044 | 1536999 | 1536999 | 227930112 | 227930112 |
| iso4014:M20x90 | stl-preview | 1 | ok | ok: 1 | 1.557 | 1.557 | 0.363 | 0.363 | 5248684 | 5248684 | 235290624 | 235290624 |
| iso4032:M3.5 | stl-fine | 1 | ok | ok: 1 | 1.508 | 1.508 | 0.226 | 0.226 | 1723584 | 1723584 | 264724480 | 264724480 |
| bolt-d1-p0.1-n30-right | step | 1 | ok | ok: 1 | 2.061 | 2.061 | 0.050 | 0.050 | 1619286 | 1619286 | 229769216 | 229769216 |
| bolt-d3-p0.1-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n240-left | stl-fine | 1 | ok | ok: 1 | 17.514 | 17.514 | 8.814 | 8.814 | 73511584 | 73511584 | 523030528 | 523030528 |
| bolt-d10-p1-n3-right | step | 1 | ok | ok: 1 | 0.645 | 0.645 | 0.013 | 0.013 | 339685 | 339685 | 210468864 | 210468864 |
| bolt-d30-p0.1-n30-right | stl-preview | 1 | ok | ok: 1 | 2.778 | 2.778 | 0.742 | 0.742 | 9782784 | 9782784 | 256094208 | 256094208 |
| bolt-d30-p1-n30-left | stl-fine | 1 | ok | ok: 1 | 1.954 | 1.954 | 10.874 | 10.874 | 77916984 | 77916984 | 952135680 | 952135680 |
| bolt-d30-p10-n240-right | step | 1 | ok | ok: 1 | 6.630 | 6.630 | 0.476 | 0.476 | 15732574 | 15732574 | 431206400 | 431206400 |
| bolt-d100-p1-n3-right | stl-preview | 1 | ok | ok: 1 | 1.122 | 1.122 | 0.421 | 0.421 | 3767784 | 3767784 | 321847296 | 321847296 |
| bolt-d100-p10-n3-left | stl-fine | 1 | ok | ok: 1 | 0.719 | 0.719 | 5.779 | 5.779 | 17494484 | 17494484 | 1419968512 | 1419968512 |
| bolt-d300-p0.35-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n240-right | stl-preview | 1 | ok | ok: 1 | 8.158 | 8.158 | 149.996 | 149.996 | 1217317584 | 1217317584 | 3974942720 | 3974942720 |
| bolt-d1000-p0.1-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n3-right | step | 1 | ok | ok: 1 | 2.040 | 2.040 | 0.027 | 0.027 | 863969 | 863969 | 217268224 | 217268224 |
| nut-d3-p0.35-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 4.095 | 4.095 | 0.100 | 0.100 | 1166084 | 1166084 | 253616128 | 253616128 |
| nut-d10-p1-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.552 | 1.552 | 0.965 | 0.965 | 8035884 | 8035884 | 407265280 | 407265280 |
| nut-d30-p0.35-m0.8d-s4d-c0.15-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nut-d30-p3.5-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 2.891 | 2.891 | 0.581 | 0.581 | 7808784 | 7808784 | 245198848 | 245198848 |
| nut-d100-p3.5-m0.8d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 4.236 | 4.236 | 39.296 | 39.296 | 161288384 | 161288384 | 3171237888 | 3171237888 |
| nut-d10-p1-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 1.718 | 1.718 | 0.024 | 0.024 | 842791 | 842791 | 222138368 | 222138368 |
| iso4017:M2x10 | stl-fine | 1 | ok | ok: 1 | 2.594 | 2.594 | 1.709 | 1.709 | 7823284 | 7823284 | 284516352 | 284516352 |
| iso4017:M3x8 | step | 1 | ok | ok: 1 | 1.911 | 1.911 | 0.044 | 0.044 | 977557 | 977557 | 215646208 | 215646208 |
| iso4017:M3.5x35 | stl-preview | 1 | ok | ok: 1 | 3.685 | 3.685 | 0.408 | 0.408 | 2706084 | 2706084 | 246910976 | 246910976 |
| iso4017:M5x20 | stl-fine | 1 | ok | ok: 1 | 2.099 | 2.099 | 2.328 | 2.328 | 12013084 | 12013084 | 336822272 | 336822272 |
| iso4017:M6x40 | step | 1 | ok | ok: 1 | 2.930 | 2.930 | 0.106 | 0.106 | 2519006 | 2519006 | 251056128 | 251056128 |
| iso4017:M7x60 | stl-preview | 1 | ok | ok: 1 | 4.072 | 4.072 | 0.610 | 0.610 | 5010484 | 5010484 | 262033408 | 262033408 |
| iso4017:M8x65 | stl-fine | 1 | ok | ok: 1 | 3.608 | 3.608 | 7.614 | 7.614 | 44447684 | 44447684 | 446582784 | 446582784 |
| iso4017:M10x70 | step | 1 | ok | ok: 1 | 3.327 | 3.327 | 0.116 | 0.116 | 2679425 | 2679425 | 257843200 | 257843200 |
| iso4017:M12x80 | stl-preview | 1 | ok | ok: 1 | 3.252 | 3.252 | 0.755 | 0.755 | 4417784 | 4417784 | 255598592 | 255598592 |
| iso4017:M14x70 | stl-fine | 1 | ok | ok: 1 | 2.820 | 2.820 | 10.414 | 10.414 | 57440584 | 57440584 | 652939264 | 652939264 |
| iso4017:M16x55 | step | 1 | ok | ok: 1 | 2.431 | 2.431 | 0.080 | 0.080 | 1876741 | 1876741 | 229502976 | 229502976 |
| iso4017:M18x40 | stl-preview | 1 | ok | ok: 1 | 1.845 | 1.845 | 0.548 | 0.548 | 4011684 | 4011684 | 240988160 | 240988160 |
| iso4017:M18x140 | stl-fine | 1 | ok | ok: 1 | 4.031 | 4.031 | 16.657 | 16.657 | 98796684 | 98796684 | 725958656 | 725958656 |
| iso4017:M20x100 | step | 1 | ok | ok: 1 | 3.120 | 3.120 | 0.115 | 0.115 | 2639692 | 2639692 | 258191360 | 258191360 |
| iso4014:M3x20 | stl-preview | 1 | ok | ok: 1 | 3.543 | 3.543 | 0.157 | 0.157 | 1081984 | 1081984 | 232075264 | 232075264 |
| iso4014:M5x35 | stl-fine | 1 | ok | ok: 1 | 2.462 | 2.462 | 1.865 | 1.865 | 10190184 | 10190184 | 334897152 | 334897152 |
| iso4014:M7x45 | step | 1 | ok | ok: 1 | 2.222 | 2.222 | 0.057 | 0.057 | 1327408 | 1327408 | 225333248 | 225333248 |
| iso4014:M10x45 | stl-preview | 1 | ok | ok: 1 | 2.296 | 2.296 | 0.223 | 0.223 | 1621384 | 1621384 | 223657984 | 223657984 |
| iso4014:M12x70 | stl-fine | 1 | ok | ok: 1 | 2.342 | 2.342 | 4.320 | 4.320 | 23581884 | 23581884 | 524808192 | 524808192 |
| iso4014:M14x110 | step | 1 | ok | ok: 1 | 2.412 | 2.412 | 0.053 | 0.053 | 1203691 | 1203691 | 221491200 | 221491200 |
| iso4014:M16x160 | stl-preview | 1 | ok | ok: 1 | 2.611 | 2.611 | 0.626 | 0.626 | 3640284 | 3640284 | 249372672 | 249372672 |
| iso4014:M20x90 | stl-fine | 1 | ok | ok: 1 | 2.367 | 2.367 | 5.954 | 5.954 | 33255884 | 33255884 | 591724544 | 591724544 |
| iso4032:M3.5 | step | 1 | ok | ok: 1 | 2.513 | 2.513 | 0.029 | 0.029 | 570506 | 570506 | 211943424 | 211943424 |
| bolt-d1-p0.1-n30-left | stl-preview | 1 | ok | ok: 1 | 3.125 | 3.125 | 0.159 | 0.159 | 1266384 | 1266384 | 242040832 | 242040832 |
| bolt-d3-p0.1-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n240-left | step | 1 | ok | ok: 1 | 26.447 | 26.447 | 0.565 | 0.565 | 13008587 | 13008587 | 356007936 | 356007936 |
| bolt-d10-p1-n3-left | stl-preview | 1 | ok | ok: 1 | 1.019 | 1.019 | 0.037 | 0.037 | 229184 | 229184 | 212623360 | 212623360 |
| bolt-d30-p0.1-n30-right | stl-fine | 1 | ok | ok: 1 | 4.322 | 4.322 | 19.581 | 19.581 | 104402484 | 104402484 | 1023057920 | 1023057920 |
| bolt-d30-p1-n30-left | step | 1 | ok | ok: 1 | 3.049 | 3.049 | 0.097 | 0.097 | 2070628 | 2070628 | 250904576 | 250904576 |
| bolt-d30-p10-n240-left | stl-preview | 1 | ok | ok: 1 | 10.394 | 10.394 | 7.370 | 7.370 | 62898184 | 62898184 | 519643136 | 519643136 |
| bolt-d100-p1-n3-right | stl-fine | 1 | ok | ok: 1 | 1.711 | 1.711 | 7.779 | 7.779 | 19850684 | 19850684 | 1707900928 | 1707900928 |
| bolt-d100-p10-n3-left | step | 1 | ok | ok: 1 | 1.162 | 1.162 | 0.023 | 0.023 | 417481 | 417481 | 210522112 | 210522112 |
| bolt-d300-p0.35-n30-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n240-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.1-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n3-left | stl-preview | 1 | ok | ok: 1 | 3.037 | 3.037 | 14.031 | 14.031 | 34593784 | 34593784 | 2918907904 | 2918907904 |
| nut-d3-p0.35-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 6.402 | 6.402 | 1.935 | 1.935 | 10026984 | 10026984 | 319582208 | 319582208 |
| nut-d10-p1-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 2.426 | 2.426 | 0.039 | 0.039 | 843231 | 843231 | 210018304 | 210018304 |
| nut-d30-p0.35-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 7.266 | 7.266 | 3.435 | 3.435 | 24556384 | 24556384 | 303403008 | 303403008 |
| nut-d30-p3.5-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 4.521 | 4.521 | 13.494 | 13.494 | 76436684 | 76436684 | 847650816 | 847650816 |
| nut-d100-p3.5-m0.8d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 6.621 | 6.621 | 0.090 | 0.090 | 2081802 | 2081802 | 236085248 | 236085248 |
| nut-d10-p1-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 5.763 | 5.763 | 0.286 | 0.286 | 2135084 | 2135084 | 237731840 | 237731840 |
| iso4017:M2x10 | step | 1 | ok | ok: 1 | 2.610 | 2.610 | 0.063 | 0.063 | 1425838 | 1425838 | 222654464 | 222654464 |
| iso4017:M3x10 | stl-preview | 1 | ok | ok: 1 | 2.270 | 2.270 | 0.130 | 0.130 | 883884 | 883884 | 218042368 | 218042368 |
| iso4017:M3.5x35 | stl-fine | 1 | ok | ok: 1 | 3.670 | 3.670 | 4.505 | 4.505 | 23113084 | 23113084 | 352018432 | 352018432 |
| iso4017:M5x20 | step | 1 | ok | ok: 1 | 2.068 | 2.068 | 0.069 | 0.069 | 1618670 | 1618670 | 224772096 | 224772096 |
| iso4017:M6x45 | stl-preview | 1 | ok | ok: 1 | 3.209 | 3.209 | 0.456 | 0.456 | 3641984 | 3641984 | 252190720 | 252190720 |
| iso4017:M7x60 | stl-fine | 1 | ok | ok: 1 | 4.041 | 4.041 | 5.708 | 5.708 | 31711184 | 31711184 | 361492480 | 361492480 |
| iso4017:M8x65 | step | 1 | ok | ok: 1 | 3.559 | 3.559 | 0.138 | 0.138 | 3264923 | 3264923 | 264536064 | 264536064 |
| iso4017:M10x80 | stl-preview | 1 | ok | ok: 1 | 3.675 | 3.675 | 0.637 | 0.637 | 4837684 | 4837684 | 271638528 | 271638528 |
| iso4017:M12x80 | stl-fine | 1 | ok | ok: 1 | 3.231 | 3.231 | 11.180 | 11.180 | 62320884 | 62320884 | 615174144 | 615174144 |
| iso4017:M14x70 | step | 1 | ok | ok: 1 | 2.805 | 2.805 | 0.097 | 0.097 | 2290933 | 2290933 | 243163136 | 243163136 |
| iso4017:M16x60 | stl-preview | 1 | ok | ok: 1 | 2.611 | 2.611 | 0.810 | 0.810 | 4935384 | 4935384 | 253018112 | 253018112 |
| iso4017:M18x40 | stl-fine | 1 | ok | ok: 1 | 1.829 | 1.829 | 5.091 | 5.091 | 28123284 | 28123284 | 529129472 | 529129472 |
| iso4017:M18x140 | step | 1 | ok | ok: 1 | 3.981 | 3.981 | 0.153 | 0.153 | 3612266 | 3612266 | 257400832 | 257400832 |
| iso4017:M20x110 | stl-preview | 1 | ok | ok: 1 | 3.319 | 3.319 | 1.427 | 1.427 | 12452284 | 12452284 | 265523200 | 265523200 |
| iso4014:M3x20 | stl-fine | 1 | ok | ok: 1 | 3.548 | 3.548 | 1.776 | 1.776 | 9669384 | 9669384 | 299659264 | 299659264 |
| iso4014:M5x35 | step | 1 | ok | ok: 1 | 2.549 | 2.549 | 0.058 | 0.058 | 1307911 | 1307911 | 222289920 | 222289920 |
| iso4014:M7x50 | stl-preview | 1 | ok | ok: 1 | 2.209 | 2.209 | 0.209 | 0.209 | 1646684 | 1646684 | 224165888 | 224165888 |
| iso4014:M10x45 | stl-fine | 1 | ok | ok: 1 | 2.300 | 2.300 | 3.707 | 3.707 | 21537884 | 21537884 | 462299136 | 462299136 |
| iso4014:M12x70 | step | 1 | ok | ok: 1 | 2.327 | 2.327 | 0.052 | 0.052 | 1187165 | 1187165 | 225062912 | 225062912 |
| iso4014:M14x120 | stl-preview | 1 | ok | ok: 1 | 2.397 | 2.397 | 0.265 | 0.265 | 1835884 | 1835884 | 226086912 | 226086912 |
| iso4014:M16x160 | stl-fine | 1 | ok | ok: 1 | 2.670 | 2.670 | 6.969 | 6.969 | 38614184 | 38614184 | 631156736 | 631156736 |
| iso4014:M20x90 | step | 1 | ok | ok: 1 | 2.349 | 2.349 | 0.061 | 0.061 | 1333962 | 1333962 | 223481856 | 223481856 |
| iso4032:M4 | stl-preview | 1 | ok | ok: 1 | 2.266 | 2.266 | 0.040 | 0.040 | 263584 | 263584 | 214290432 | 214290432 |
| bolt-d1-p0.1-n30-left | stl-fine | 1 | ok | ok: 1 | 3.119 | 3.119 | 1.442 | 1.442 | 8218884 | 8218884 | 266706944 | 266706944 |
| bolt-d3-p0.1-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.1-n3-right | stl-preview | 1 | ok | ok: 1 | 1.511 | 1.511 | 0.046 | 0.046 | 275084 | 275084 | 213417984 | 213417984 |
| bolt-d10-p1-n3-left | stl-fine | 1 | ok | ok: 1 | 1.043 | 1.043 | 0.592 | 0.592 | 2846684 | 2846684 | 349343744 | 349343744 |
| bolt-d30-p0.1-n30-right | step | 1 | ok | ok: 1 | 4.322 | 4.322 | 0.097 | 0.097 | 2090480 | 2090480 | 248455168 | 248455168 |
| bolt-d30-p1-n240-right | stl-preview | 1 | ok | ok: 1 | 12.084 | 12.084 | 9.609 | 9.609 | 78137784 | 78137784 | 568799232 | 568799232 |
| bolt-d30-p10-n240-left | stl-fine | 1 | ok | ok: 1 | 10.789 | 10.789 | 99.575 | 99.575 | 513173684 | 513173684 | 1809469440 | 1809469440 |
| bolt-d100-p1-n3-right | step | 1 | ok | ok: 1 | 1.714 | 1.714 | 0.024 | 0.024 | 446662 | 446662 | 211124224 | 211124224 |
| bolt-d100-p10-n30-right | stl-preview | 1 | ok | ok: 1 | 2.401 | 2.401 | 5.616 | 5.616 | 39141884 | 39141884 | 428011520 | 428011520 |
| bolt-d300-p0.35-n30-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n240-right | step | 1 | ok | ok: 1 | 12.800 | 12.800 | 0.934 | 0.934 | 20746308 | 20746308 | 461348864 | 461348864 |
| bolt-d1000-p0.35-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n3-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p0.35-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 6.388 | 6.388 | 0.073 | 0.073 | 1695765 | 1695765 | 248770560 | 248770560 |
| nut-d10-p1-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 1.577 | 1.577 | 0.312 | 0.312 | 2560284 | 2560284 | 233738240 | 233738240 |
| nut-d30-p0.35-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 7.246 | 7.246 | 67.277 | 67.277 | 377976084 | 377976084 | 2072219648 | 2072219648 |
| nut-d30-p3.5-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 4.578 | 4.578 | 0.095 | 0.095 | 2100993 | 2100993 | 234299392 | 234299392 |
| nut-d100-p3.5-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 6.076 | 6.076 | 3.509 | 3.509 | 23889184 | 23889184 | 391778304 | 391778304 |
| nut-d10-p1-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 5.927 | 5.927 | 5.196 | 5.196 | 28268184 | 28268184 | 454266880 | 454266880 |
| iso4017:M2x12 | stl-preview | 1 | ok | ok: 1 | 1.950 | 1.950 | 0.093 | 0.093 | 1146284 | 1146284 | 223371264 | 223371264 |
| iso4017:M3x10 | stl-fine | 1 | ok | ok: 1 | 1.473 | 1.473 | 0.899 | 0.899 | 7587484 | 7587484 | 299847680 | 299847680 |
| iso4017:M3.5x35 | step | 1 | ok | ok: 1 | 2.364 | 2.364 | 0.094 | 0.094 | 3232166 | 3232166 | 241631232 | 241631232 |
| iso4017:M5x25 | stl-preview | 1 | ok | ok: 1 | 1.540 | 1.540 | 0.172 | 0.172 | 2318684 | 2318684 | 231424000 | 231424000 |
| iso4017:M6x45 | stl-fine | 1 | ok | ok: 1 | 2.074 | 2.074 | 2.606 | 2.606 | 22798484 | 22798484 | 359858176 | 359858176 |
| iso4017:M7x60 | step | 1 | ok | ok: 1 | 2.646 | 2.646 | 0.103 | 0.103 | 3722154 | 3722154 | 255848448 | 255848448 |
| iso4017:M8x70 | stl-preview | 1 | ok | ok: 1 | 2.493 | 2.493 | 0.352 | 0.352 | 4719284 | 4719284 | 257110016 | 257110016 |
| iso4017:M10x80 | stl-fine | 1 | ok | ok: 1 | 2.350 | 2.350 | 6.773 | 6.773 | 65997084 | 65997084 | 584163328 | 584163328 |
| iso4017:M12x80 | step | 1 | ok | ok: 1 | 2.060 | 2.060 | 0.076 | 0.076 | 2921108 | 2921108 | 254349312 | 254349312 |
| iso4017:M14x80 | stl-preview | 1 | ok | ok: 1 | 1.958 | 1.958 | 0.352 | 0.352 | 4107184 | 4107184 | 247873536 | 247873536 |
| iso4017:M16x60 | stl-fine | 1 | ok | ok: 1 | 1.686 | 1.686 | 5.824 | 5.824 | 51974484 | 51974484 | 639315968 | 639315968 |
| iso4017:M18x40 | step | 1 | ok | ok: 1 | 1.189 | 1.189 | 0.034 | 0.034 | 1159850 | 1159850 | 224247808 | 224247808 |
| iso4017:M18x150 | stl-preview | 1 | ok | ok: 1 | 2.685 | 2.685 | 1.175 | 1.175 | 15308884 | 15308884 | 300986368 | 300986368 |
| iso4017:M20x110 | stl-fine | 1 | ok | ok: 1 | 2.124 | 2.124 | 8.291 | 8.291 | 80132684 | 80132684 | 694853632 | 694853632 |
| iso4014:M3x20 | step | 1 | ok | ok: 1 | 2.258 | 2.258 | 0.041 | 0.041 | 1402112 | 1402112 | 218652672 | 218652672 |
| iso4014:M5x40 | stl-preview | 1 | ok | ok: 1 | 1.575 | 1.575 | 0.110 | 0.110 | 1481784 | 1481784 | 223571968 | 223571968 |
| iso4014:M7x50 | stl-fine | 1 | ok | ok: 1 | 1.397 | 1.397 | 1.189 | 1.189 | 11039884 | 11039884 | 319148032 | 319148032 |
| iso4014:M10x45 | step | 1 | ok | ok: 1 | 1.445 | 1.445 | 0.032 | 0.032 | 1096241 | 1096241 | 224251904 | 224251904 |
| iso4014:M12x80 | stl-preview | 1 | ok | ok: 1 | 1.533 | 1.533 | 0.138 | 0.138 | 1735684 | 1735684 | 227069952 | 227069952 |
| iso4014:M14x120 | stl-fine | 1 | ok | ok: 1 | 1.536 | 1.536 | 3.033 | 3.033 | 27923284 | 27923284 | 578727936 | 578727936 |
| iso4014:M16x160 | step | 1 | ok | ok: 1 | 1.648 | 1.648 | 0.043 | 0.043 | 1536999 | 1536999 | 229019648 | 229019648 |
| iso4014:M20x100 | stl-preview | 1 | ok | ok: 1 | 1.438 | 1.438 | 0.350 | 0.350 | 5248684 | 5248684 | 237658112 | 237658112 |
| iso4032:M4 | stl-fine | 1 | ok | ok: 1 | 1.390 | 1.390 | 0.200 | 0.200 | 1840884 | 1840884 | 257097728 | 257097728 |
| bolt-d1-p0.1-n30-left | step | 1 | ok | ok: 1 | 2.048 | 2.048 | 0.044 | 0.044 | 1613824 | 1613824 | 227532800 | 227532800 |
| bolt-d3-p0.1-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.1-n3-right | stl-fine | 1 | ok | ok: 1 | 0.941 | 0.941 | 0.557 | 0.557 | 3958184 | 3958184 | 372797440 | 372797440 |
| bolt-d10-p1-n3-left | step | 1 | ok | ok: 1 | 0.615 | 0.615 | 0.013 | 0.013 | 338063 | 338063 | 210227200 | 210227200 |
| bolt-d30-p0.1-n30-left | stl-preview | 1 | ok | ok: 1 | 2.854 | 2.854 | 0.577 | 0.577 | 7576184 | 7576184 | 249671680 | 249671680 |
| bolt-d30-p1-n240-right | stl-fine | 1 | ok | ok: 1 | 7.834 | 7.834 | 74.103 | 74.103 | 637042284 | 637042284 | 2321612800 | 2321612800 |
| bolt-d30-p10-n240-left | step | 1 | ok | ok: 1 | 6.586 | 6.586 | 0.450 | 0.450 | 15741080 | 15741080 | 431190016 | 431190016 |
| bolt-d100-p1-n3-left | stl-preview | 1 | ok | ok: 1 | 1.060 | 1.060 | 0.305 | 0.305 | 2993984 | 2993984 | 312844288 | 312844288 |
| bolt-d100-p10-n30-right | stl-fine | 1 | ok | ok: 1 | 1.495 | 1.495 | 49.406 | 49.406 | 262436284 | 262436284 | 2855145472 | 2855145472 |
| bolt-d300-p0.35-n30-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n240-left | stl-preview | 1 | ok | ok: 1 | 8.127 | 8.127 | 117.184 | 117.184 | 940335884 | 940335884 | 3185000448 | 3185000448 |
| bolt-d1000-p0.35-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n3-left | step | 1 | ok | ok: 1 | 1.900 | 1.900 | 0.030 | 0.030 | 971259 | 971259 | 217759744 | 217759744 |
| nut-d3-p0.35-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 3.686 | 3.686 | 0.125 | 0.125 | 1166084 | 1166084 | 231968768 | 231968768 |
| nut-d10-p1-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 0.979 | 0.979 | 1.578 | 1.578 | 12971184 | 12971184 | 514265088 | 514265088 |
| nut-d30-p0.35-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 4.858 | 4.858 | 0.139 | 0.139 | 4649100 | 4649100 | 249327616 | 249327616 |
| nut-d30-p3.5-m3d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 3.156 | 3.156 | 0.775 | 0.775 | 9113584 | 9113584 | 289280000 | 289280000 |
| nut-d100-p3.5-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 4.016 | 4.016 | 29.033 | 29.033 | 135879584 | 135879584 | 2647322624 | 2647322624 |
| nut-d10-p1-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 3.737 | 3.737 | 0.059 | 0.059 | 2173615 | 2173615 | 240877568 | 240877568 |
| iso4017:M2x12 | stl-fine | 1 | ok | ok: 1 | 3.017 | 3.017 | 1.784 | 1.784 | 9283584 | 9283584 | 280317952 | 280317952 |
| iso4017:M3x10 | step | 1 | ok | ok: 1 | 2.257 | 2.257 | 0.051 | 0.051 | 1174202 | 1174202 | 217640960 | 217640960 |
| iso4017:M4x8 | stl-preview | 1 | ok | ok: 1 | 1.542 | 1.542 | 0.093 | 0.093 | 595784 | 595784 | 216641536 | 216641536 |
| iso4017:M5x25 | stl-fine | 1 | ok | ok: 1 | 2.385 | 2.385 | 2.788 | 2.788 | 14997384 | 14997384 | 346583040 | 346583040 |
| iso4017:M6x45 | step | 1 | ok | ok: 1 | 3.271 | 3.271 | 0.119 | 0.119 | 2815299 | 2815299 | 249204736 | 249204736 |
| iso4017:M7x65 | stl-preview | 1 | ok | ok: 1 | 4.378 | 4.378 | 0.653 | 0.653 | 5398684 | 5398684 | 265949184 | 265949184 |
| iso4017:M8x70 | stl-fine | 1 | ok | ok: 1 | 3.822 | 3.822 | 8.000 | 8.000 | 47607384 | 47607384 | 448172032 | 448172032 |
| iso4017:M10x80 | step | 1 | ok | ok: 1 | 3.663 | 3.663 | 0.126 | 0.126 | 3033070 | 3033070 | 262864896 | 262864896 |
| iso4017:M12x90 | stl-preview | 1 | ok | ok: 1 | 3.487 | 3.487 | 0.672 | 0.672 | 4972684 | 4972684 | 271298560 | 271298560 |
| iso4017:M14x80 | stl-fine | 1 | ok | ok: 1 | 3.022 | 3.022 | 11.722 | 11.722 | 66316284 | 66316284 | 658526208 | 658526208 |
| iso4017:M16x60 | step | 1 | ok | ok: 1 | 2.618 | 2.618 | 0.085 | 0.085 | 2007019 | 2007019 | 231133184 | 231133184 |
| iso4017:M18x45 | stl-preview | 1 | ok | ok: 1 | 1.987 | 1.987 | 0.597 | 0.597 | 4551284 | 4551284 | 242659328 | 242659328 |
| iso4017:M18x150 | stl-fine | 1 | ok | ok: 1 | 4.237 | 4.237 | 17.318 | 17.318 | 105681184 | 105681184 | 744267776 | 744267776 |
| iso4017:M20x110 | step | 1 | ok | ok: 1 | 3.321 | 3.321 | 0.120 | 0.120 | 2874627 | 2874627 | 254717952 | 254717952 |
| iso4014:M3x25 | stl-preview | 1 | ok | ok: 1 | 3.592 | 3.592 | 0.155 | 0.155 | 1081984 | 1081984 | 231628800 | 231628800 |
| iso4014:M5x40 | stl-fine | 1 | ok | ok: 1 | 2.414 | 2.414 | 1.830 | 1.830 | 10190184 | 10190184 | 320897024 | 320897024 |
| iso4014:M7x50 | step | 1 | ok | ok: 1 | 2.202 | 2.202 | 0.056 | 0.056 | 1327408 | 1327408 | 222277632 | 222277632 |
| iso4014:M10x50 | stl-preview | 1 | ok | ok: 1 | 2.313 | 2.313 | 0.261 | 0.261 | 1621384 | 1621384 | 223752192 | 223752192 |
| iso4014:M12x80 | stl-fine | 1 | ok | ok: 1 | 2.331 | 2.331 | 4.197 | 4.197 | 23581884 | 23581884 | 482979840 | 482979840 |
| iso4014:M14x120 | step | 1 | ok | ok: 1 | 2.401 | 2.401 | 0.052 | 0.052 | 1203691 | 1203691 | 223760384 | 223760384 |
| iso4014:M18x70 | stl-preview | 1 | ok | ok: 1 | 2.376 | 2.376 | 0.550 | 0.550 | 4191184 | 4191184 | 239841280 | 239841280 |
| iso4014:M20x100 | stl-fine | 1 | ok | ok: 1 | 2.305 | 2.305 | 5.614 | 5.614 | 33255884 | 33255884 | 562114560 | 562114560 |
| iso4032:M4 | step | 1 | ok | ok: 1 | 2.250 | 2.250 | 0.029 | 0.029 | 598961 | 598961 | 212766720 | 212766720 |
| bolt-d1-p0.1-n240-right | stl-preview | 1 | ok | ok: 1 | 24.148 | 24.148 | 1.281 | 1.281 | 10113784 | 10113784 | 337797120 | 337797120 |
| bolt-d3-p0.1-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.1-n3-right | step | 1 | ok | ok: 1 | 1.513 | 1.513 | 0.020 | 0.020 | 384239 | 384239 | 210247680 | 210247680 |
| bolt-d10-p1-n30-right | stl-preview | 1 | ok | ok: 1 | 2.667 | 2.667 | 0.365 | 0.365 | 2694584 | 2694584 | 243490816 | 243490816 |
| bolt-d30-p0.1-n30-left | stl-fine | 1 | ok | ok: 1 | 4.342 | 4.342 | 16.111 | 16.111 | 86454384 | 86454384 | 933781504 | 933781504 |
| bolt-d30-p1-n240-right | step | 1 | ok | ok: 1 | 12.208 | 12.208 | 0.657 | 0.657 | 15325995 | 15325995 | 438611968 | 438611968 |
| bolt-d100-p0.1-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n3-left | stl-fine | 1 | ok | ok: 1 | 1.656 | 1.656 | 6.281 | 6.281 | 16602484 | 16602484 | 1691729920 | 1691729920 |
| bolt-d100-p10-n30-right | step | 1 | ok | ok: 1 | 2.397 | 2.397 | 0.096 | 0.096 | 2245675 | 2245675 | 238874624 | 238874624 |
| bolt-d300-p0.35-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n240-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.35-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n30-right | stl-preview | 1 | ok | ok: 1 | 4.531 | 4.531 | 129.393 | 129.393 | 436518284 | 436518284 | 5029761024 | 5029761024 |
| nut-d3-p0.35-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 5.590 | 5.590 | 1.930 | 1.930 | 10036584 | 10036584 | 315318272 | 315318272 |
| nut-d10-p1-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 1.576 | 1.576 | 0.035 | 0.035 | 689365 | 689365 | 216100864 | 216100864 |
| nut-d30-p1-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 5.692 | 5.692 | 0.827 | 0.827 | 6367984 | 6367984 | 246226944 | 246226944 |
| nut-d30-p3.5-m3d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 4.935 | 4.935 | 25.815 | 25.815 | 129655484 | 129655484 | 1355812864 | 1355812864 |
| nut-d100-p3.5-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 6.067 | 6.067 | 0.082 | 0.082 | 1864679 | 1864679 | 230064128 | 230064128 |
| nut-d10-p3.5-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 1.494 | 1.494 | 0.023 | 0.023 | 147484 | 147484 | 211947520 | 211947520 |
| iso4017:M2x12 | step | 1 | ok | ok: 1 | 3.050 | 3.050 | 0.079 | 0.079 | 1679424 | 1679424 | 235995136 | 235995136 |
| iso4017:M3x12 | stl-preview | 1 | ok | ok: 1 | 2.697 | 2.697 | 0.175 | 0.175 | 1058784 | 1058784 | 222396416 | 222396416 |
| iso4017:M4x8 | stl-fine | 1 | ok | ok: 1 | 1.552 | 1.552 | 1.085 | 1.085 | 5384984 | 5384984 | 310784000 | 310784000 |
| iso4017:M5x25 | step | 1 | ok | ok: 1 | 2.409 | 2.409 | 0.086 | 0.086 | 1992505 | 1992505 | 228339712 | 228339712 |
| iso4017:M6x50 | stl-preview | 1 | ok | ok: 1 | 3.496 | 3.496 | 0.498 | 0.498 | 4018784 | 4018784 | 249044992 | 249044992 |
| iso4017:M7x65 | stl-fine | 1 | ok | ok: 1 | 4.404 | 4.404 | 6.547 | 6.547 | 34771884 | 34771884 | 343515136 | 343515136 |
| iso4017:M8x70 | step | 1 | ok | ok: 1 | 3.849 | 3.849 | 0.147 | 0.147 | 3488046 | 3488046 | 255803392 | 255803392 |
| iso4017:M10x90 | stl-preview | 1 | ok | ok: 1 | 4.098 | 4.098 | 0.724 | 0.724 | 5400784 | 5400784 | 256581632 | 256581632 |
| iso4017:M12x90 | stl-fine | 1 | ok | ok: 1 | 3.543 | 3.543 | 12.576 | 12.576 | 70002384 | 70002384 | 630894592 | 630894592 |
| iso4017:M14x80 | step | 1 | ok | ok: 1 | 3.080 | 3.080 | 0.115 | 0.115 | 2605504 | 2605504 | 246702080 | 246702080 |
| iso4017:M16x65 | stl-preview | 1 | ok | ok: 1 | 2.809 | 2.809 | 0.906 | 0.906 | 5228384 | 5228384 | 248352768 | 248352768 |
| iso4017:M18x45 | stl-fine | 1 | ok | ok: 1 | 1.993 | 1.993 | 5.995 | 5.995 | 31515384 | 31515384 | 547414016 | 547414016 |
| iso4017:M18x150 | step | 1 | ok | ok: 1 | 4.262 | 4.262 | 0.164 | 0.164 | 3855000 | 3855000 | 273145856 | 273145856 |
| iso4017:M20x120 | stl-preview | 1 | ok | ok: 1 | 3.551 | 3.551 | 1.550 | 1.550 | 13743284 | 13743284 | 268013568 | 268013568 |
| iso4014:M3x25 | stl-fine | 1 | ok | ok: 1 | 3.593 | 3.593 | 1.785 | 1.785 | 9669384 | 9669384 | 305655808 | 305655808 |
| iso4014:M5x40 | step | 1 | ok | ok: 1 | 2.441 | 2.441 | 0.057 | 0.057 | 1307958 | 1307958 | 221167616 | 221167616 |
| iso4014:M7x55 | stl-preview | 1 | ok | ok: 1 | 2.230 | 2.230 | 0.207 | 0.207 | 1646684 | 1646684 | 225665024 | 225665024 |
| iso4014:M10x50 | stl-fine | 1 | ok | ok: 1 | 2.322 | 2.322 | 3.796 | 3.796 | 21537884 | 21537884 | 472727552 | 472727552 |
| iso4014:M12x80 | step | 1 | ok | ok: 1 | 2.340 | 2.340 | 0.053 | 0.053 | 1187166 | 1187166 | 222969856 | 222969856 |
| iso4014:M14x130 | stl-preview | 1 | ok | ok: 1 | 2.593 | 2.593 | 0.346 | 0.346 | 2141584 | 2141584 | 240340992 | 240340992 |
| iso4014:M18x70 | stl-fine | 1 | ok | ok: 1 | 2.400 | 2.400 | 5.489 | 5.489 | 29404684 | 29404684 | 532537344 | 532537344 |
| iso4014:M20x100 | step | 1 | ok | ok: 1 | 2.326 | 2.326 | 0.060 | 0.060 | 1334004 | 1334004 | 223760384 | 223760384 |
| iso4032:M5 | stl-preview | 1 | ok | ok: 1 | 2.485 | 2.485 | 0.057 | 0.057 | 390284 | 390284 | 217595904 | 217595904 |
| bolt-d1-p0.1-n240-right | stl-fine | 1 | ok | ok: 1 | 24.164 | 24.164 | 12.602 | 12.602 | 72432184 | 72432184 | 500801536 | 500801536 |
| bolt-d3-p0.1-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.1-n3-left | stl-preview | 1 | ok | ok: 1 | 1.520 | 1.520 | 0.041 | 0.041 | 234184 | 234184 | 212459520 | 212459520 |
| bolt-d10-p1-n30-right | stl-fine | 1 | ok | ok: 1 | 2.698 | 2.698 | 6.650 | 6.650 | 37376084 | 37376084 | 477470720 | 477470720 |
| bolt-d30-p0.1-n30-left | step | 1 | ok | ok: 1 | 4.381 | 4.381 | 0.093 | 0.093 | 2107890 | 2107890 | 254488576 | 254488576 |
| bolt-d30-p1-n240-left | stl-preview | 1 | ok | ok: 1 | 12.169 | 12.169 | 7.466 | 7.466 | 60726584 | 60726584 | 552075264 | 552075264 |
| bolt-d100-p0.1-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n3-left | step | 1 | ok | ok: 1 | 1.665 | 1.665 | 0.024 | 0.024 | 446759 | 446759 | 211116032 | 211116032 |
| bolt-d100-p10-n30-left | stl-preview | 1 | ok | ok: 1 | 2.431 | 2.431 | 4.575 | 4.575 | 30135084 | 30135084 | 350064640 | 350064640 |
| bolt-d300-p0.35-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n240-left | step | 1 | ok | ok: 1 | 12.741 | 12.741 | 0.918 | 0.918 | 20744512 | 20744512 | 465195008 | 465195008 |
| bolt-d1000-p0.35-n3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n30-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p0.35-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 5.617 | 5.617 | 0.074 | 0.074 | 1695413 | 1695413 | 230096896 | 230096896 |
| nut-d10-p1-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 5.526 | 5.526 | 0.348 | 0.348 | 2645884 | 2645884 | 238383104 | 238383104 |
| nut-d30-p1-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 5.771 | 5.771 | 11.625 | 11.625 | 53887784 | 53887784 | 806612992 | 806612992 |
| nut-d30-p3.5-m3d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 4.959 | 4.959 | 0.091 | 0.091 | 1947831 | 1947831 | 271712256 | 271712256 |
| nut-d100-p3.5-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 5.967 | 5.967 | 4.288 | 4.288 | 27853884 | 27853884 | 425250816 | 425250816 |
| nut-d10-p3.5-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 1.517 | 1.517 | 0.306 | 0.306 | 1681184 | 1681184 | 274599936 | 274599936 |
| iso4017:M2x16 | stl-preview | 1 | ok | ok: 1 | 2.845 | 2.845 | 0.163 | 0.163 | 1526584 | 1526584 | 228081664 | 228081664 |
| iso4017:M3x12 | stl-fine | 1 | ok | ok: 1 | 2.006 | 2.006 | 1.384 | 1.384 | 9242784 | 9242784 | 295686144 | 295686144 |
| iso4017:M4x8 | step | 1 | ok | ok: 1 | 1.194 | 1.194 | 0.033 | 0.033 | 775256 | 775256 | 214667264 | 214667264 |
| iso4017:M5x30 | stl-preview | 1 | ok | ok: 1 | 2.134 | 2.134 | 0.274 | 0.274 | 2803384 | 2803384 | 237821952 | 237821952 |
| iso4017:M6x50 | stl-fine | 1 | ok | ok: 1 | 2.718 | 2.718 | 3.848 | 3.848 | 25775684 | 25775684 | 366858240 | 366858240 |
| iso4017:M7x65 | step | 1 | ok | ok: 1 | 3.363 | 3.363 | 0.150 | 0.150 | 4006191 | 4006191 | 262217728 | 262217728 |
| iso4017:M8x80 | stl-preview | 1 | ok | ok: 1 | 3.151 | 3.151 | 0.617 | 0.617 | 5421984 | 5421984 | 275800064 | 275800064 |
| iso4017:M10x90 | stl-fine | 1 | ok | ok: 1 | 3.063 | 3.063 | 10.445 | 10.445 | 74570684 | 74570684 | 602255360 | 602255360 |
| iso4017:M12x90 | step | 1 | ok | ok: 1 | 2.697 | 2.697 | 0.111 | 0.111 | 3271327 | 3271327 | 260730880 | 260730880 |
| iso4017:M14x90 | stl-preview | 1 | ok | ok: 1 | 2.542 | 2.542 | 0.523 | 0.523 | 4605684 | 4605684 | 247959552 | 247959552 |
| iso4017:M16x65 | stl-fine | 1 | ok | ok: 1 | 2.130 | 2.130 | 8.716 | 8.716 | 56926584 | 56926584 | 643325952 | 643325952 |
| iso4017:M18x45 | step | 1 | ok | ok: 1 | 1.520 | 1.520 | 0.048 | 0.048 | 1270501 | 1270501 | 223268864 | 223268864 |
| iso4017:M18x160 | stl-preview | 1 | ok | ok: 1 | 3.369 | 3.369 | 1.674 | 1.674 | 16307884 | 16307884 | 297496576 | 297496576 |
| iso4017:M20x120 | stl-fine | 1 | ok | ok: 1 | 2.760 | 2.760 | 12.292 | 12.292 | 85754884 | 85754884 | 690454528 | 690454528 |
| iso4014:M3x25 | step | 1 | ok | ok: 1 | 2.717 | 2.717 | 0.051 | 0.051 | 1402139 | 1402139 | 218427392 | 218427392 |
| iso4014:M5x45 | stl-preview | 1 | ok | ok: 1 | 1.877 | 1.877 | 0.148 | 0.148 | 1481784 | 1481784 | 224591872 | 224591872 |
| iso4014:M7x55 | stl-fine | 1 | ok | ok: 1 | 1.716 | 1.716 | 1.610 | 1.610 | 11039884 | 11039884 | 328806400 | 328806400 |
| iso4014:M10x50 | step | 1 | ok | ok: 1 | 1.778 | 1.778 | 0.041 | 0.041 | 1096241 | 1096241 | 221405184 | 221405184 |
| iso4014:M12x90 | stl-preview | 1 | ok | ok: 1 | 1.818 | 1.818 | 0.187 | 0.187 | 1735684 | 1735684 | 225357824 | 225357824 |
| iso4014:M14x130 | stl-fine | 1 | ok | ok: 1 | 2.020 | 2.020 | 5.021 | 5.021 | 32917384 | 32917384 | 584171520 | 584171520 |
| iso4014:M18x70 | step | 1 | ok | ok: 1 | 1.852 | 1.852 | 0.047 | 0.047 | 1195905 | 1195905 | 221696000 | 221696000 |
| iso4014:M20x110 | stl-preview | 1 | ok | ok: 1 | 1.794 | 1.794 | 0.473 | 0.473 | 5248684 | 5248684 | 237748224 | 237748224 |
| iso4032:M5 | stl-fine | 1 | ok | ok: 1 | 1.966 | 1.966 | 0.388 | 0.388 | 2555484 | 2555484 | 292016128 | 292016128 |
| bolt-d1-p0.1-n240-right | step | 1 | ok | ok: 1 | 18.374 | 18.374 | 0.452 | 0.452 | 12291896 | 12291896 | 359243776 | 359243776 |
| bolt-d3-p0.35-n3-right | stl-preview | 1 | ok | ok: 1 | 0.685 | 0.685 | 0.023 | 0.023 | 133084 | 133084 | 210780160 | 210780160 |
| bolt-d10-p0.1-n3-left | stl-fine | 1 | ok | ok: 1 | 1.256 | 1.256 | 0.573 | 0.573 | 3155384 | 3155384 | 366469120 | 366469120 |
| bolt-d10-p1-n30-right | step | 1 | ok | ok: 1 | 2.070 | 2.070 | 0.072 | 0.072 | 1935117 | 1935117 | 233185280 | 233185280 |
| bolt-d30-p0.1-n240-right | stl-preview | 1 | ok | ok: 1 | 14.965 | 14.965 | 7.377 | 7.377 | 78461084 | 78461084 | 585793536 | 585793536 |
| bolt-d30-p1-n240-left | stl-fine | 1 | ok | ok: 1 | 9.499 | 9.499 | 108.035 | 108.035 | 627962984 | 627962984 | 2207281152 | 2207281152 |
| bolt-d100-p0.1-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n30-right | stl-preview | 1 | ok | ok: 1 | 2.759 | 2.759 | 4.601 | 4.601 | 39345684 | 39345684 | 442806272 | 442806272 |
| bolt-d100-p10-n30-left | stl-fine | 1 | ok | ok: 1 | 1.842 | 1.842 | 46.254 | 46.254 | 176195384 | 176195384 | 2816028672 | 2816028672 |
| bolt-d300-p0.35-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n3-right | stl-preview | 1 | ok | ok: 1 | 1.116 | 1.116 | 2.402 | 2.402 | 13049984 | 13049984 | 759922688 | 759922688 |
| bolt-d1000-p0.35-n3-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n30-right | step | 1 | ok | ok: 1 | 3.385 | 3.385 | 0.138 | 0.138 | 3859425 | 3859425 | 255291392 | 255291392 |
| nut-d3-p1-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 1.233 | 1.233 | 0.016 | 0.016 | 112884 | 112884 | 214159360 | 214159360 |
| nut-d10-p1-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 4.229 | 4.229 | 5.123 | 5.123 | 35898084 | 35898084 | 539791360 | 539791360 |
| nut-d30-p1-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 4.506 | 4.506 | 0.062 | 0.062 | 1672895 | 1672895 | 235884544 | 235884544 |
| nut-d30-p3.5-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 3.289 | 3.289 | 0.850 | 0.850 | 7824384 | 7824384 | 254115840 | 254115840 |
| nut-d100-p3.5-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 4.633 | 4.633 | 41.582 | 41.582 | 161422184 | 161422184 | 3052130304 | 3052130304 |
| nut-d10-p3.5-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 1.153 | 1.153 | 0.021 | 0.021 | 499112 | 499112 | 211779584 | 211779584 |
| iso4017:M2x4 | stl-fine | 1 | ok | ok: 1 | 1.061 | 1.061 | 0.455 | 0.455 | 3196784 | 3196784 | 268226560 | 268226560 |
| iso4017:M2.5x16 | step | 1 | ok | ok: 1 | 2.908 | 2.908 | 0.063 | 0.063 | 1947361 | 1947361 | 227266560 | 227266560 |
| iso4017:M3.5x16 | stl-preview | 1 | ok | ok: 1 | 1.778 | 1.778 | 0.144 | 0.144 | 1240584 | 1240584 | 222253056 | 222253056 |
| iso4017:M4x40 | stl-fine | 1 | ok | ok: 1 | 2.833 | 2.833 | 4.060 | 4.060 | 27023684 | 27023684 | 342466560 | 342466560 |
| iso4017:M6x20 | step | 1 | ok | ok: 1 | 1.527 | 1.527 | 0.043 | 0.043 | 1304431 | 1304431 | 221286400 | 221286400 |
| iso4017:M7x40 | stl-preview | 1 | ok | ok: 1 | 2.388 | 2.388 | 0.311 | 0.311 | 3344484 | 3344484 | 242302976 | 242302976 |
| iso4017:M8x45 | stl-fine | 1 | ok | ok: 1 | 2.230 | 2.230 | 4.263 | 4.263 | 30645384 | 30645384 | 392204288 | 392204288 |
| iso4017:M10x50 | step | 1 | ok | ok: 1 | 2.083 | 2.083 | 0.066 | 0.066 | 1977219 | 1977219 | 240799744 | 240799744 |
| iso4017:M12x55 | stl-preview | 1 | ok | ok: 1 | 2.020 | 2.020 | 0.320 | 0.320 | 3036284 | 3036284 | 240267264 | 240267264 |
| iso4017:M14x50 | stl-fine | 1 | ok | ok: 1 | 1.831 | 1.831 | 6.601 | 6.601 | 41365384 | 41365384 | 630255616 | 630255616 |
| iso4017:M16x35 | step | 1 | ok | ok: 1 | 1.587 | 1.587 | 0.042 | 0.042 | 1245896 | 1245896 | 222433280 | 222433280 |
| iso4017:M16x140 | stl-preview | 1 | ok | ok: 1 | 3.768 | 3.768 | 1.236 | 1.236 | 11541584 | 11541584 | 296030208 | 296030208 |
| iso4017:M18x100 | stl-fine | 1 | ok | ok: 1 | 2.511 | 2.511 | 9.158 | 9.158 | 70515384 | 70515384 | 662523904 | 662523904 |
| iso4017:M20x65 | step | 1 | ok | ok: 1 | 1.896 | 1.896 | 0.056 | 0.056 | 1766890 | 1766890 | 231141376 | 231141376 |
| iso4014:M2x20 | stl-preview | 1 | ok | ok: 1 | 2.786 | 2.786 | 0.100 | 0.100 | 978184 | 978184 | 221433856 | 221433856 |
| iso4014:M4x35 | stl-fine | 1 | ok | ok: 1 | 1.893 | 1.893 | 1.345 | 1.345 | 9752984 | 9752984 | 323596288 | 323596288 |
| iso4014:M6x55 | step | 1 | ok | ok: 1 | 1.875 | 1.875 | 0.039 | 0.039 | 1211679 | 1211679 | 222404608 | 222404608 |
| iso4014:M8x60 | stl-preview | 1 | ok | ok: 1 | 1.957 | 1.957 | 0.153 | 0.153 | 1541284 | 1541284 | 223662080 | 223662080 |
| iso4014:M12x50 | stl-fine | 1 | ok | ok: 1 | 1.928 | 1.928 | 3.335 | 3.335 | 23581884 | 23581884 | 492367872 | 492367872 |
| iso4014:M14x70 | step | 1 | ok | ok: 1 | 1.999 | 1.999 | 0.039 | 0.039 | 1203647 | 1203647 | 223911936 | 223911936 |
| iso4014:M16x120 | stl-preview | 1 | ok | ok: 1 | 1.930 | 1.930 | 0.339 | 0.339 | 3143384 | 3143384 | 237613056 | 237613056 |
| iso4014:M18x150 | stl-fine | 1 | ok | ok: 1 | 1.983 | 1.983 | 4.527 | 4.527 | 34477384 | 34477384 | 581558272 | 581558272 |
| iso4014:M20x200 | step | 1 | ok | ok: 1 | 2.244 | 2.244 | 0.048 | 0.048 | 1465962 | 1465962 | 225980416 | 225980416 |
| iso4032:M20 | stl-preview | 1 | ok | ok: 1 | 2.214 | 2.214 | 0.154 | 0.154 | 1613384 | 1613384 | 227672064 | 227672064 |
| bolt-d3-p0.1-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n3-left | step | 1 | ok | ok: 1 | 0.672 | 0.672 | 0.013 | 0.013 | 280722 | 280722 | 209498112 | 209498112 |
| bolt-d10-p0.35-n30-left | stl-preview | 1 | ok | ok: 1 | 2.597 | 2.597 | 0.229 | 0.229 | 2255584 | 2255584 | 238419968 | 238419968 |
| bolt-d10-p3-n240-right | stl-fine | 1 | ok | ok: 1 | 10.976 | 10.976 | 33.762 | 33.762 | 277752984 | 277752984 | 1082486784 | 1082486784 |
| bolt-d30-p0.35-n240-left | step | 1 | ok | ok: 1 | 11.623 | 11.623 | 0.494 | 0.494 | 15430392 | 15430392 | 422862848 | 422862848 |
| bolt-d30-p10-n3-left | stl-preview | 1 | ok | ok: 1 | 0.726 | 0.726 | 0.086 | 0.086 | 769484 | 769484 | 225325056 | 225325056 |
| bolt-d100-p0.35-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n30-left | step | 1 | ok | ok: 1 | 2.437 | 2.437 | 0.072 | 0.072 | 2218984 | 2218984 | 232722432 | 232722432 |
| bolt-d300-p0.1-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n3-right | stl-fine | 1 | ok | ok: 1 | 1.390 | 1.390 | 42.547 | 42.547 | 70389184 | 70389184 | 8468439040 | 8468439040 |
| bolt-d1000-p0.1-n3-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n30-left | stl-preview | 1 | ok | ok: 1 | 4.610 | 4.610 | 105.503 | 105.503 | 364558084 | 364558084 | 4959764480 | 4959764480 |
| bolt-d1000-p10-n240-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d10-p0.35-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 10.278 | 10.278 | 0.171 | 0.171 | 5512332 | 5512332 | 262627328 | 262627328 |
| nut-d10-p3.5-m3d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 1.367 | 1.367 | 0.255 | 0.255 | 2464784 | 2464784 | 227516416 | 227516416 |
| nut-d30-p3.5-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 2.117 | 2.117 | 2.680 | 2.680 | 16074384 | 16074384 | 562622464 | 562622464 |
| nut-d100-p1-m0.8d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 11.985 | 11.985 | 0.184 | 0.184 | 5546218 | 5546218 | 263647232 | 263647232 |
| nut-d3-p1-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 2.451 | 2.451 | 0.045 | 0.045 | 368884 | 368884 | 221130752 | 221130752 |
| nut-d100-p1-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 10.811 | 10.811 | 116.991 | 116.991 | 354009184 | 354009184 | 2859495424 | 2859495424 |
| iso4017:M2x16 | stl-fine | 1 | ok | ok: 1 | 3.879 | 3.879 | 2.268 | 2.268 | 12449784 | 12449784 | 274296832 | 274296832 |
| iso4017:M3x12 | step | 1 | ok | ok: 1 | 2.687 | 2.687 | 0.062 | 0.062 | 1393802 | 1393802 | 219865088 | 219865088 |
| iso4017:M4x10 | stl-preview | 1 | ok | ok: 1 | 1.464 | 1.464 | 0.117 | 0.117 | 744084 | 744084 | 217763840 | 217763840 |
| iso4017:M5x30 | stl-fine | 1 | ok | ok: 1 | 2.751 | 2.751 | 3.311 | 3.311 | 17967184 | 17967184 | 340025344 | 340025344 |
| iso4017:M6x50 | step | 1 | ok | ok: 1 | 3.482 | 3.482 | 0.128 | 0.128 | 3095429 | 3095429 | 248803328 | 248803328 |
| iso4017:M7x70 | stl-preview | 1 | ok | ok: 1 | 4.478 | 4.478 | 0.711 | 0.711 | 5843784 | 5843784 | 269422592 | 269422592 |
| iso4017:M8x80 | stl-fine | 1 | ok | ok: 1 | 4.166 | 4.166 | 9.388 | 9.388 | 54713884 | 54713884 | 467689472 | 467689472 |
| iso4017:M10x90 | step | 1 | ok | ok: 1 | 4.217 | 4.217 | 0.144 | 0.144 | 3385091 | 3385091 | 266870784 | 266870784 |
| iso4017:M12x100 | stl-preview | 1 | ok | ok: 1 | 3.816 | 3.816 | 0.754 | 0.754 | 5517384 | 5517384 | 272400384 | 272400384 |
| iso4017:M14x90 | stl-fine | 1 | ok | ok: 1 | 3.342 | 3.342 | 13.502 | 13.502 | 74588684 | 74588684 | 682311680 | 682311680 |
| iso4017:M16x65 | step | 1 | ok | ok: 1 | 2.784 | 2.784 | 0.097 | 0.097 | 2167362 | 2167362 | 234369024 | 234369024 |
| iso4017:M18x50 | stl-preview | 1 | ok | ok: 1 | 2.055 | 2.055 | 0.655 | 0.655 | 4920584 | 4920584 | 241324032 | 241324032 |
| iso4017:M18x160 | stl-fine | 1 | ok | ok: 1 | 4.405 | 4.405 | 20.007 | 20.007 | 112882184 | 112882184 | 819417088 | 819417088 |
| iso4017:M20x120 | step | 1 | ok | ok: 1 | 3.555 | 3.555 | 0.134 | 0.134 | 3116584 | 3116584 | 258650112 | 258650112 |
| iso4014:M3x30 | stl-preview | 1 | ok | ok: 1 | 3.614 | 3.614 | 0.156 | 0.156 | 1081984 | 1081984 | 231792640 | 231792640 |
| iso4014:M5x45 | stl-fine | 1 | ok | ok: 1 | 2.448 | 2.448 | 1.885 | 1.885 | 10190184 | 10190184 | 331526144 | 331526144 |
| iso4014:M7x55 | step | 1 | ok | ok: 1 | 2.215 | 2.215 | 0.058 | 0.058 | 1327433 | 1327433 | 225136640 | 225136640 |
| iso4014:M10x55 | stl-preview | 1 | ok | ok: 1 | 2.303 | 2.303 | 0.223 | 0.223 | 1621384 | 1621384 | 224034816 | 224034816 |
| iso4014:M12x90 | stl-fine | 1 | ok | ok: 1 | 2.340 | 2.340 | 4.378 | 4.378 | 23581884 | 23581884 | 490962944 | 490962944 |
| iso4014:M14x130 | step | 1 | ok | ok: 1 | 2.591 | 2.591 | 0.065 | 0.065 | 1386368 | 1386368 | 227586048 | 227586048 |
| iso4014:M18x80 | stl-preview | 1 | ok | ok: 1 | 2.392 | 2.392 | 0.610 | 0.610 | 4191184 | 4191184 | 250814464 | 250814464 |
| iso4014:M20x110 | stl-fine | 1 | ok | ok: 1 | 2.288 | 2.288 | 5.864 | 5.864 | 33255884 | 33255884 | 619274240 | 619274240 |
| iso4032:M5 | step | 1 | ok | ok: 1 | 2.464 | 2.464 | 0.035 | 0.035 | 722425 | 722425 | 213639168 | 213639168 |
| bolt-d1-p0.1-n240-left | stl-preview | 1 | ok | ok: 1 | 24.169 | 24.169 | 1.313 | 1.313 | 10114384 | 10114384 | 334184448 | 334184448 |
| bolt-d3-p0.35-n3-right | stl-fine | 1 | ok | ok: 1 | 0.898 | 0.898 | 0.247 | 0.247 | 1179984 | 1179984 | 275501056 | 275501056 |
| bolt-d10-p0.1-n3-left | step | 1 | ok | ok: 1 | 1.536 | 1.536 | 0.021 | 0.021 | 384355 | 384355 | 210358272 | 210358272 |
| bolt-d10-p1-n30-left | stl-preview | 1 | ok | ok: 1 | 2.689 | 2.689 | 0.350 | 0.350 | 2228984 | 2228984 | 239706112 | 239706112 |
| bolt-d30-p0.1-n240-right | stl-fine | 1 | ok | ok: 1 | 19.157 | 19.157 | 151.055 | 151.055 | 839336384 | 839336384 | 2872549376 | 2872549376 |
| bolt-d30-p1-n240-left | step | 1 | ok | ok: 1 | 12.112 | 12.112 | 0.696 | 0.696 | 15350004 | 15350004 | 452374528 | 452374528 |
| bolt-d100-p0.1-n3-left | stl-preview | 1 | ok | ok: 1 | 3.773 | 3.773 | 0.659 | 0.659 | 3197784 | 3197784 | 310829056 | 310829056 |
| bolt-d100-p1-n30-right | stl-fine | 1 | ok | ok: 1 | 3.711 | 3.711 | 64.812 | 64.812 | 200264684 | 200264684 | 2681618432 | 2681618432 |
| bolt-d100-p10-n30-left | step | 1 | ok | ok: 1 | 2.417 | 2.417 | 0.098 | 0.098 | 2245842 | 2245842 | 235368448 | 235368448 |
| bolt-d300-p0.35-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n3-right | stl-fine | 1 | ok | ok: 1 | 1.409 | 1.409 | 47.574 | 47.574 | 81350884 | 81350884 | 8436121600 | 8436121600 |
| bolt-d1000-p0.35-n3-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n30-left | stl-preview | 1 | ok | ok: 1 | 4.105 | 4.105 | 122.673 | 122.673 | 362274784 | 362274784 | 4480495616 | 4480495616 |
| nut-d3-p1-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.592 | 1.592 | 0.176 | 0.176 | 1015084 | 1015084 | 251531264 | 251531264 |
| nut-d10-p1-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 5.539 | 5.539 | 0.091 | 0.091 | 2175690 | 2175690 | 237883392 | 237883392 |
| nut-d30-p1-m0.8d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 4.763 | 4.763 | 1.228 | 1.228 | 8843584 | 8843584 | 280461312 | 280461312 |
| nut-d30-p3.5-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 4.137 | 4.137 | 14.648 | 14.648 | 76502684 | 76502684 | 957173760 | 957173760 |
| nut-d100-p3.5-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 5.965 | 5.965 | 0.098 | 0.098 | 2082034 | 2082034 | 228188160 | 228188160 |
| nut-d10-p3.5-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 2.567 | 2.567 | 0.094 | 0.094 | 648784 | 648784 | 218120192 | 218120192 |
| iso4017:M2x16 | step | 1 | ok | ok: 1 | 3.794 | 3.794 | 0.094 | 0.094 | 2216414 | 2216414 | 240275456 | 240275456 |
| iso4017:M3x16 | stl-preview | 1 | ok | ok: 1 | 3.209 | 3.209 | 0.212 | 0.212 | 1412684 | 1412684 | 235634688 | 235634688 |
| iso4017:M4x10 | stl-fine | 1 | ok | ok: 1 | 1.458 | 1.458 | 1.287 | 1.287 | 6796984 | 6796984 | 312864768 | 312864768 |
| iso4017:M5x30 | step | 1 | ok | ok: 1 | 2.746 | 2.746 | 0.095 | 0.095 | 2373023 | 2373023 | 237363200 | 237363200 |
| iso4017:M6x55 | stl-preview | 1 | ok | ok: 1 | 3.645 | 3.645 | 0.542 | 0.542 | 4447984 | 4447984 | 258678784 | 258678784 |
| iso4017:M7x70 | stl-fine | 1 | ok | ok: 1 | 4.477 | 4.477 | 6.605 | 6.605 | 37246684 | 37246684 | 400035840 | 400035840 |
| iso4017:M8x80 | step | 1 | ok | ok: 1 | 4.195 | 4.195 | 0.157 | 0.157 | 3984708 | 3984708 | 267743232 | 267743232 |
| iso4017:M10x100 | stl-preview | 1 | ok | ok: 1 | 4.478 | 4.478 | 0.786 | 0.786 | 6011484 | 6011484 | 286277632 | 286277632 |
| iso4017:M12x100 | stl-fine | 1 | ok | ok: 1 | 3.798 | 3.798 | 12.985 | 12.985 | 77795884 | 77795884 | 666517504 | 666517504 |
| iso4017:M14x90 | step | 1 | ok | ok: 1 | 3.343 | 3.343 | 0.116 | 0.116 | 2896346 | 2896346 | 255881216 | 255881216 |
| iso4017:M16x70 | stl-preview | 1 | ok | ok: 1 | 2.913 | 2.913 | 0.953 | 0.953 | 5703684 | 5703684 | 254107648 | 254107648 |
| iso4017:M18x50 | stl-fine | 1 | ok | ok: 1 | 2.053 | 2.053 | 5.984 | 5.984 | 35218584 | 35218584 | 590622720 | 590622720 |
| iso4017:M18x160 | step | 1 | ok | ok: 1 | 4.394 | 4.394 | 0.172 | 0.172 | 4113636 | 4113636 | 272416768 | 272416768 |
| iso4017:M20x130 | stl-preview | 1 | ok | ok: 1 | 3.742 | 3.742 | 1.653 | 1.653 | 14898684 | 14898684 | 277524480 | 277524480 |
| iso4014:M3x30 | stl-fine | 1 | ok | ok: 1 | 3.602 | 3.602 | 1.696 | 1.696 | 9669384 | 9669384 | 299819008 | 299819008 |
| iso4014:M5x45 | step | 1 | ok | ok: 1 | 2.414 | 2.414 | 0.055 | 0.055 | 1307911 | 1307911 | 221753344 | 221753344 |
| iso4014:M7x60 | stl-preview | 1 | ok | ok: 1 | 2.223 | 2.223 | 0.204 | 0.204 | 1646684 | 1646684 | 223346688 | 223346688 |
| iso4014:M10x55 | stl-fine | 1 | ok | ok: 1 | 2.303 | 2.303 | 3.731 | 3.731 | 21537884 | 21537884 | 487329792 | 487329792 |
| iso4014:M12x90 | step | 1 | ok | ok: 1 | 2.323 | 2.323 | 0.052 | 0.052 | 1187153 | 1187153 | 222519296 | 222519296 |
| iso4014:M14x140 | stl-preview | 1 | ok | ok: 1 | 2.599 | 2.599 | 0.313 | 0.313 | 2141584 | 2141584 | 227098624 | 227098624 |
| iso4014:M18x80 | stl-fine | 1 | ok | ok: 1 | 2.371 | 2.371 | 5.109 | 5.109 | 29404684 | 29404684 | 550182912 | 550182912 |
| iso4014:M20x110 | step | 1 | ok | ok: 1 | 2.277 | 2.277 | 0.058 | 0.058 | 1334347 | 1334347 | 222978048 | 222978048 |
| iso4032:M6 | stl-preview | 1 | ok | ok: 1 | 2.431 | 2.431 | 0.060 | 0.060 | 354384 | 354384 | 215474176 | 215474176 |
| bolt-d1-p0.1-n240-left | stl-fine | 1 | ok | ok: 1 | 24.193 | 24.193 | 10.817 | 10.817 | 65523884 | 65523884 | 488673280 | 488673280 |
| bolt-d3-p0.35-n3-right | step | 1 | ok | ok: 1 | 0.892 | 0.892 | 0.017 | 0.017 | 301705 | 301705 | 209858560 | 209858560 |
| bolt-d10-p0.1-n30-right | stl-preview | 1 | ok | ok: 1 | 3.447 | 3.447 | 0.372 | 0.372 | 2784584 | 2784584 | 248127488 | 248127488 |
| bolt-d10-p1-n30-left | stl-fine | 1 | ok | ok: 1 | 2.680 | 2.680 | 5.559 | 5.559 | 29161784 | 29161784 | 461266944 | 461266944 |
| bolt-d30-p0.1-n240-right | step | 1 | ok | ok: 1 | 19.099 | 19.099 | 0.657 | 0.657 | 15219204 | 15219204 | 450166784 | 450166784 |
| bolt-d30-p3-n3-right | stl-preview | 1 | ok | ok: 1 | 1.057 | 1.057 | 0.141 | 0.141 | 930284 | 930284 | 230031360 | 230031360 |
| bolt-d100-p0.1-n3-left | stl-fine | 1 | ok | ok: 1 | 3.735 | 3.735 | 8.593 | 8.593 | 25940984 | 25940984 | 1760141312 | 1760141312 |
| bolt-d100-p1-n30-right | step | 1 | ok | ok: 1 | 3.707 | 3.707 | 0.097 | 0.097 | 2243240 | 2243240 | 244740096 | 244740096 |
| bolt-d100-p10-n240-right | stl-preview | 1 | ok | ok: 1 | 10.416 | 10.416 | 42.279 | 42.279 | 314884584 | 314884584 | 1166905344 | 1166905344 |
| bolt-d300-p0.35-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n3-right | step | 1 | ok | ok: 1 | 1.400 | 1.400 | 0.025 | 0.025 | 481319 | 481319 | 213258240 | 213258240 |
| bolt-d1000-p0.35-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n30-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p1-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 1.577 | 1.577 | 0.023 | 0.023 | 441340 | 441340 | 214257664 | 214257664 |
| nut-d10-p1-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 4.931 | 4.931 | 0.345 | 0.345 | 2654284 | 2654284 | 232873984 | 232873984 |
| nut-d30-p1-m0.8d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 4.653 | 4.653 | 26.864 | 26.864 | 132130084 | 132130084 | 1375866880 | 1375866880 |
| nut-d30-p3.5-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 4.101 | 4.101 | 0.093 | 0.093 | 2100808 | 2100808 | 229457920 | 229457920 |
| nut-d100-p3.5-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 13.492 | 13.492 | 15.401 | 15.401 | 107559584 | 107559584 | 627265536 | 627265536 |
| nut-d10-p3.5-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 2.528 | 2.528 | 1.505 | 1.505 | 7579684 | 7579684 | 389931008 | 389931008 |
| iso4017:M2x20 | stl-preview | 1 | ok | ok: 1 | 3.576 | 3.576 | 0.172 | 0.172 | 1899984 | 1899984 | 244350976 | 244350976 |
| iso4017:M3x16 | stl-fine | 1 | ok | ok: 1 | 2.330 | 2.330 | 1.977 | 1.977 | 12196284 | 12196284 | 325230592 | 325230592 |
| iso4017:M4x10 | step | 1 | ok | ok: 1 | 1.070 | 1.070 | 0.035 | 0.035 | 951719 | 951719 | 214892544 | 214892544 |
| iso4017:M5x35 | stl-preview | 1 | ok | ok: 1 | 2.242 | 2.242 | 0.284 | 0.284 | 3253884 | 3253884 | 239722496 | 239722496 |
| iso4017:M6x55 | stl-fine | 1 | ok | ok: 1 | 2.761 | 2.761 | 4.296 | 4.296 | 27926784 | 27926784 | 378658816 | 378658816 |
| iso4017:M7x70 | step | 1 | ok | ok: 1 | 3.281 | 3.281 | 0.150 | 0.150 | 4322910 | 4322910 | 273235968 | 273235968 |
| iso4017:M10x20 | stl-preview | 1 | ok | ok: 1 | 1.130 | 1.130 | 0.114 | 0.114 | 1208284 | 1208284 | 222142464 | 222142464 |
| iso4017:M10x100 | stl-fine | 1 | ok | ok: 1 | 3.115 | 3.115 | 11.777 | 11.777 | 82864684 | 82864684 | 634355712 | 634355712 |
| iso4017:M12x100 | step | 1 | ok | ok: 1 | 2.889 | 2.889 | 0.128 | 0.128 | 3618655 | 3618655 | 252919808 | 252919808 |
| iso4017:M14x100 | stl-preview | 1 | ok | ok: 1 | 2.788 | 2.788 | 0.596 | 0.596 | 5176084 | 5176084 | 274722816 | 274722816 |
| iso4017:M16x70 | stl-fine | 1 | ok | ok: 1 | 2.149 | 2.149 | 9.237 | 9.237 | 60049484 | 60049484 | 652730368 | 652730368 |
| iso4017:M18x50 | step | 1 | ok | ok: 1 | 1.477 | 1.477 | 0.051 | 0.051 | 1395646 | 1395646 | 229171200 | 229171200 |
| iso4017:M18x180 | stl-preview | 1 | ok | ok: 1 | 3.568 | 3.568 | 1.647 | 1.647 | 18388484 | 18388484 | 300584960 | 300584960 |
| iso4017:M20x130 | stl-fine | 1 | ok | ok: 1 | 2.613 | 2.613 | 13.264 | 13.264 | 93073484 | 93073484 | 727433216 | 727433216 |
| iso4014:M3x30 | step | 1 | ok | ok: 1 | 2.699 | 2.699 | 0.046 | 0.046 | 1402355 | 1402355 | 218562560 | 218562560 |
| iso4014:M5x50 | stl-preview | 1 | ok | ok: 1 | 1.716 | 1.716 | 0.141 | 0.141 | 1481784 | 1481784 | 223498240 | 223498240 |
| iso4014:M7x60 | stl-fine | 1 | ok | ok: 1 | 1.573 | 1.573 | 1.615 | 1.615 | 11039884 | 11039884 | 324182016 | 324182016 |
| iso4014:M10x55 | step | 1 | ok | ok: 1 | 1.684 | 1.684 | 0.041 | 0.041 | 1096241 | 1096241 | 221937664 | 221937664 |
| iso4014:M12x100 | stl-preview | 1 | ok | ok: 1 | 1.603 | 1.603 | 0.157 | 0.157 | 1735684 | 1735684 | 224493568 | 224493568 |
| iso4014:M14x140 | stl-fine | 1 | ok | ok: 1 | 1.817 | 1.817 | 4.888 | 4.888 | 32917384 | 32917384 | 613699584 | 613699584 |
| iso4014:M18x80 | step | 1 | ok | ok: 1 | 1.683 | 1.683 | 0.039 | 0.039 | 1195905 | 1195905 | 224464896 | 224464896 |
| iso4014:M20x120 | stl-preview | 1 | ok | ok: 1 | 1.579 | 1.579 | 0.388 | 0.388 | 5248684 | 5248684 | 240377856 | 240377856 |
| iso4032:M6 | stl-fine | 1 | ok | ok: 1 | 1.647 | 1.647 | 0.406 | 0.406 | 2422184 | 2422184 | 287592448 | 287592448 |
| bolt-d1-p0.1-n240-left | step | 1 | ok | ok: 1 | 16.587 | 16.587 | 0.397 | 0.397 | 12285686 | 12285686 | 354967552 | 354967552 |
| bolt-d3-p0.35-n3-left | stl-preview | 1 | ok | ok: 1 | 0.599 | 0.599 | 0.015 | 0.015 | 120584 | 120584 | 210657280 | 210657280 |
| bolt-d10-p0.1-n30-right | stl-fine | 1 | ok | ok: 1 | 2.299 | 2.299 | 5.417 | 5.417 | 40712284 | 40712284 | 523657216 | 523657216 |
| bolt-d10-p1-n30-left | step | 1 | ok | ok: 1 | 1.874 | 1.874 | 0.061 | 0.061 | 1933506 | 1933506 | 228364288 | 228364288 |
| bolt-d30-p0.1-n240-left | stl-preview | 1 | ok | ok: 1 | 13.256 | 13.256 | 4.966 | 4.966 | 60546784 | 60546784 | 539205632 | 539205632 |
| bolt-d30-p3-n3-right | stl-fine | 1 | ok | ok: 1 | 0.731 | 0.731 | 1.647 | 1.647 | 7960684 | 7960684 | 467759104 | 467759104 |
| bolt-d100-p0.1-n3-left | step | 1 | ok | ok: 1 | 2.433 | 2.433 | 0.026 | 0.026 | 792141 | 792141 | 212955136 | 212955136 |
| bolt-d100-p1-n30-left | stl-preview | 1 | ok | ok: 1 | 2.472 | 2.472 | 3.383 | 3.383 | 30530384 | 30530384 | 370102272 | 370102272 |
| bolt-d100-p10-n240-right | stl-fine | 1 | ok | ok: 1 | 6.881 | 6.881 | 491.105 | 491.105 | 2108578184 | 2108578184 | 6602854400 | 6602854400 |
| bolt-d300-p0.35-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n3-left | stl-preview | 1 | ok | ok: 1 | 0.904 | 0.904 | 2.197 | 2.197 | 10217084 | 10217084 | 714850304 | 714850304 |
| bolt-d1000-p0.35-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n30-left | step | 1 | ok | ok: 1 | 2.751 | 2.751 | 0.122 | 0.122 | 3963169 | 3963169 | 253763584 | 253763584 |
| nut-d3-p1-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 0.976 | 0.976 | 0.013 | 0.013 | 112884 | 112884 | 209829888 | 209829888 |
| nut-d10-p1-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 3.477 | 3.477 | 4.756 | 4.756 | 35924484 | 35924484 | 523223040 | 523223040 |
| nut-d30-p1-m0.8d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 3.200 | 3.200 | 0.065 | 0.065 | 1874589 | 1874589 | 269017088 | 269017088 |
| nut-d30-p3.5-m3d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 2.400 | 2.400 | 0.866 | 0.866 | 9129184 | 9129184 | 247750656 | 247750656 |
| nut-d100-p3.5-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 9.403 | 9.403 | 157.320 | 157.320 | 603446484 | 603446484 | 3838287872 | 3838287872 |
| nut-d10-p3.5-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 1.751 | 1.751 | 0.031 | 0.031 | 862735 | 862735 | 214237184 | 214237184 |
| iso4017:M2x20 | stl-fine | 1 | ok | ok: 1 | 4.823 | 4.823 | 2.753 | 2.753 | 15454584 | 15454584 | 282542080 | 282542080 |
| iso4017:M3x16 | step | 1 | ok | ok: 1 | 3.212 | 3.212 | 0.086 | 0.086 | 1815233 | 1815233 | 238350336 | 238350336 |
| iso4017:M4x12 | stl-preview | 1 | ok | ok: 1 | 1.788 | 1.788 | 0.134 | 0.134 | 897684 | 897684 | 218554368 | 218554368 |
| iso4017:M5x35 | stl-fine | 1 | ok | ok: 1 | 3.061 | 3.061 | 3.719 | 3.719 | 20868084 | 20868084 | 344944640 | 344944640 |
| iso4017:M6x55 | step | 1 | ok | ok: 1 | 3.611 | 3.611 | 0.141 | 0.141 | 3414421 | 3414421 | 261795840 | 261795840 |
| iso4017:M8x16 | stl-preview | 1 | ok | ok: 1 | 1.458 | 1.458 | 0.148 | 0.148 | 1088384 | 1088384 | 221360128 | 221360128 |
| iso4017:M10x20 | stl-fine | 1 | ok | ok: 1 | 1.526 | 1.526 | 2.937 | 2.937 | 16353284 | 16353284 | 464347136 | 464347136 |
| iso4017:M10x100 | step | 1 | ok | ok: 1 | 4.244 | 4.244 | 0.162 | 0.162 | 3773553 | 3773553 | 274358272 | 274358272 |
| iso4017:M12x110 | stl-preview | 1 | ok | ok: 1 | 4.194 | 4.194 | 0.812 | 0.812 | 6073184 | 6073184 | 268750848 | 268750848 |
| iso4017:M14x100 | stl-fine | 1 | ok | ok: 1 | 3.578 | 3.578 | 14.619 | 14.619 | 82395384 | 82395384 | 701063168 | 701063168 |
| iso4017:M16x70 | step | 1 | ok | ok: 1 | 2.882 | 2.882 | 0.120 | 0.120 | 2316274 | 2316274 | 249139200 | 249139200 |
| iso4017:M18x55 | stl-preview | 1 | ok | ok: 1 | 2.143 | 2.143 | 0.722 | 0.722 | 5547084 | 5547084 | 244838400 | 244838400 |
| iso4017:M18x180 | stl-fine | 1 | ok | ok: 1 | 4.803 | 4.803 | 20.740 | 20.740 | 126856584 | 126856584 | 870244352 | 870244352 |
| iso4017:M20x130 | step | 1 | ok | ok: 1 | 3.736 | 3.736 | 0.142 | 0.142 | 3375084 | 3375084 | 262426624 | 262426624 |
| iso4014:M3.5x20 | stl-preview | 1 | ok | ok: 1 | 2.423 | 2.423 | 0.154 | 0.154 | 1028084 | 1028084 | 219537408 | 219537408 |
| iso4014:M5x50 | stl-fine | 1 | ok | ok: 1 | 2.415 | 2.415 | 1.878 | 1.878 | 10190184 | 10190184 | 317591552 | 317591552 |
| iso4014:M7x60 | step | 1 | ok | ok: 1 | 2.200 | 2.200 | 0.058 | 0.058 | 1327428 | 1327428 | 224219136 | 224219136 |
| iso4014:M10x60 | stl-preview | 1 | ok | ok: 1 | 2.237 | 2.237 | 0.220 | 0.220 | 1621384 | 1621384 | 225644544 | 225644544 |
| iso4014:M12x100 | stl-fine | 1 | ok | ok: 1 | 2.341 | 2.341 | 4.087 | 4.087 | 23581884 | 23581884 | 514981888 | 514981888 |
| iso4014:M14x140 | step | 1 | ok | ok: 1 | 2.581 | 2.581 | 0.059 | 0.059 | 1386368 | 1386368 | 222720000 | 222720000 |
| iso4014:M18x90 | stl-preview | 1 | ok | ok: 1 | 2.388 | 2.388 | 0.559 | 0.559 | 4191184 | 4191184 | 237088768 | 237088768 |
| iso4014:M20x120 | stl-fine | 1 | ok | ok: 1 | 2.294 | 2.294 | 5.599 | 5.599 | 33255884 | 33255884 | 617545728 | 617545728 |
| iso4032:M6 | step | 1 | ok | ok: 1 | 2.412 | 2.412 | 0.030 | 0.030 | 622442 | 622442 | 214278144 | 214278144 |
| bolt-d1-p0.35-n3-right | stl-preview | 1 | ok | ok: 1 | 0.768 | 0.768 | 0.021 | 0.021 | 132384 | 132384 | 210567168 | 210567168 |
| bolt-d3-p0.35-n3-left | stl-fine | 1 | ok | ok: 1 | 0.888 | 0.888 | 0.243 | 0.243 | 994684 | 994684 | 269602816 | 269602816 |
| bolt-d10-p0.1-n30-right | step | 1 | ok | ok: 1 | 3.424 | 3.424 | 0.081 | 0.081 | 1972335 | 1972335 | 246005760 | 246005760 |
| bolt-d10-p1-n240-right | stl-preview | 1 | ok | ok: 1 | 13.166 | 13.166 | 2.879 | 2.879 | 21593384 | 21593384 | 426209280 | 426209280 |
| bolt-d30-p0.1-n240-left | stl-fine | 1 | ok | ok: 1 | 19.013 | 19.013 | 125.639 | 125.639 | 692508584 | 692508584 | 2460119040 | 2460119040 |
| bolt-d30-p3-n3-right | step | 1 | ok | ok: 1 | 1.066 | 1.066 | 0.021 | 0.021 | 377813 | 377813 | 210751488 | 210751488 |
| bolt-d100-p0.1-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n30-left | stl-fine | 1 | ok | ok: 1 | 3.601 | 3.601 | 54.936 | 54.936 | 162595084 | 162595084 | 2688434176 | 2688434176 |
| bolt-d100-p10-n240-right | step | 1 | ok | ok: 1 | 10.211 | 10.211 | 0.742 | 0.742 | 16967942 | 16967942 | 456200192 | 456200192 |
| bolt-d300-p1-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n3-left | stl-fine | 1 | ok | ok: 1 | 1.334 | 1.334 | 40.457 | 40.457 | 59227684 | 59227684 | 8139444224 | 8139444224 |
| bolt-d1000-p0.35-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n240-right | stl-preview | 1 | killed | killed: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p1-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.400 | 1.400 | 0.179 | 0.179 | 1024684 | 1024684 | 252522496 | 252522496 |
| nut-d10-p1-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 4.958 | 4.958 | 0.093 | 0.093 | 2176118 | 2176118 | 232652800 | 232652800 |
| nut-d30-p1-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 5.349 | 5.349 | 0.853 | 0.853 | 6383584 | 6383584 | 246665216 | 246665216 |
| nut-d30-p3.5-m3d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 3.571 | 3.571 | 27.638 | 27.638 | 129721484 | 129721484 | 1469353984 | 1469353984 |
| nut-d100-p3.5-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 13.675 | 13.675 | 0.283 | 0.283 | 6102617 | 6102617 | 263426048 | 263426048 |
| nut-d30-p0.35-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| iso4017:M2x20 | step | 1 | ok | ok: 1 | 3.916 | 3.916 | 0.089 | 0.089 | 2729382 | 2729382 | 245510144 | 245510144 |
| iso4017:M3x20 | stl-preview | 1 | ok | ok: 1 | 2.944 | 2.944 | 0.192 | 0.192 | 1763284 | 1763284 | 228618240 | 228618240 |
| iso4017:M4x12 | stl-fine | 1 | ok | ok: 1 | 1.460 | 1.460 | 1.236 | 1.236 | 8196684 | 8196684 | 317472768 | 317472768 |
| iso4017:M5x35 | step | 1 | ok | ok: 1 | 2.458 | 2.458 | 0.088 | 0.088 | 2733540 | 2733540 | 241397760 | 241397760 |
| iso4017:M6x60 | stl-preview | 1 | ok | ok: 1 | 3.189 | 3.189 | 0.521 | 0.521 | 4855784 | 4855784 | 272977920 | 272977920 |
| iso4017:M8x16 | stl-fine | 1 | ok | ok: 1 | 1.174 | 1.174 | 1.527 | 1.527 | 10672984 | 10672984 | 354803712 | 354803712 |
| iso4017:M10x20 | step | 1 | ok | ok: 1 | 1.210 | 1.210 | 0.032 | 0.032 | 896996 | 896996 | 219549696 | 219549696 |
| iso4017:M12x25 | stl-preview | 1 | ok | ok: 1 | 1.322 | 1.322 | 0.150 | 0.150 | 1416184 | 1416184 | 224014336 | 224014336 |
| iso4017:M12x110 | stl-fine | 1 | ok | ok: 1 | 3.486 | 3.486 | 11.463 | 11.463 | 85715984 | 85715984 | 648605696 | 648605696 |
| iso4017:M14x100 | step | 1 | ok | ok: 1 | 2.847 | 2.847 | 0.098 | 0.098 | 3203913 | 3203913 | 251314176 | 251314176 |
| iso4017:M16x80 | stl-preview | 1 | ok | ok: 1 | 2.515 | 2.515 | 0.713 | 0.713 | 6581584 | 6581584 | 252342272 | 252342272 |
| iso4017:M18x55 | stl-fine | 1 | ok | ok: 1 | 1.707 | 1.707 | 5.292 | 5.292 | 38720884 | 38720884 | 576274432 | 576274432 |
| iso4017:M18x180 | step | 1 | ok | ok: 1 | 3.868 | 3.868 | 0.140 | 0.140 | 4590924 | 4590924 | 276877312 | 276877312 |
| iso4017:M20x140 | stl-preview | 1 | ok | ok: 1 | 3.155 | 3.155 | 1.482 | 1.482 | 15903584 | 15903584 | 289628160 | 289628160 |
| iso4014:M3.5x20 | stl-fine | 1 | ok | ok: 1 | 1.920 | 1.920 | 1.417 | 1.417 | 9105084 | 9105084 | 316203008 | 316203008 |
| iso4014:M5x50 | step | 1 | ok | ok: 1 | 1.956 | 1.956 | 0.042 | 0.042 | 1307911 | 1307911 | 221560832 | 221560832 |
| iso4014:M7x65 | stl-preview | 1 | ok | ok: 1 | 1.772 | 1.772 | 0.159 | 0.159 | 1646684 | 1646684 | 223903744 | 223903744 |
| iso4014:M10x60 | stl-fine | 1 | ok | ok: 1 | 1.832 | 1.832 | 3.045 | 3.045 | 21537884 | 21537884 | 494153728 | 494153728 |
| iso4014:M12x100 | step | 1 | ok | ok: 1 | 1.867 | 1.867 | 0.039 | 0.039 | 1187171 | 1187171 | 225529856 | 225529856 |
| iso4014:M16x65 | stl-preview | 1 | ok | ok: 1 | 2.015 | 2.015 | 0.345 | 0.345 | 3143384 | 3143384 | 229507072 | 229507072 |
| iso4014:M18x90 | stl-fine | 1 | ok | ok: 1 | 1.927 | 1.927 | 4.171 | 4.171 | 29404684 | 29404684 | 574361600 | 574361600 |
| iso4014:M20x120 | step | 1 | ok | ok: 1 | 1.826 | 1.826 | 0.045 | 0.045 | 1333996 | 1333996 | 219340800 | 219340800 |
| iso4032:M8 | stl-preview | 1 | ok | ok: 1 | 1.974 | 1.974 | 0.046 | 0.046 | 380584 | 380584 | 216293376 | 216293376 |
| bolt-d1-p0.35-n3-right | stl-fine | 1 | ok | ok: 1 | 0.605 | 0.605 | 0.145 | 0.145 | 949084 | 949084 | 245882880 | 245882880 |
| bolt-d3-p0.35-n3-left | step | 1 | ok | ok: 1 | 0.706 | 0.706 | 0.014 | 0.014 | 300068 | 300068 | 210067456 | 210067456 |
| bolt-d10-p0.1-n30-left | stl-preview | 1 | ok | ok: 1 | 2.763 | 2.763 | 0.237 | 0.237 | 2222684 | 2222684 | 233902080 | 233902080 |
| bolt-d10-p1-n240-right | stl-fine | 1 | ok | ok: 1 | 10.751 | 10.751 | 39.315 | 39.315 | 300460084 | 300460084 | 1135730688 | 1135730688 |
| bolt-d30-p0.1-n240-left | step | 1 | ok | ok: 1 | 15.398 | 15.398 | 0.520 | 0.520 | 15255913 | 15255913 | 458588160 | 458588160 |
| bolt-d30-p3-n3-left | stl-preview | 1 | ok | ok: 1 | 0.895 | 0.895 | 0.086 | 0.086 | 741684 | 741684 | 227958784 | 227958784 |
| bolt-d100-p0.1-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n30-left | step | 1 | ok | ok: 1 | 2.959 | 2.959 | 0.077 | 0.077 | 2243156 | 2243156 | 231276544 | 231276544 |
| bolt-d100-p10-n240-left | stl-preview | 1 | ok | ok: 1 | 8.373 | 8.373 | 27.207 | 27.207 | 241905884 | 241905884 | 984629248 | 984629248 |
| bolt-d300-p1-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n3-left | step | 1 | ok | ok: 1 | 1.077 | 1.077 | 0.020 | 0.020 | 481243 | 481243 | 212836352 | 212836352 |
| bolt-d1000-p0.35-n30-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n240-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p1-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 1.103 | 1.103 | 0.019 | 0.019 | 440750 | 440750 | 209739776 | 209739776 |
| nut-d10-p1-m3d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 3.151 | 3.151 | 0.925 | 0.925 | 9384084 | 9384084 | 253165568 | 253165568 |
| nut-d30-p1-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 4.367 | 4.367 | 8.826 | 8.826 | 53953784 | 53953784 | 875429888 | 875429888 |
| nut-d30-p3.5-m3d-s4d-c5-right | step | 1 | ok | ok: 1 | 2.785 | 2.785 | 0.069 | 0.069 | 1947635 | 1947635 | 221442048 | 221442048 |
| nut-d100-p3.5-m3d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 10.764 | 10.764 | 12.609 | 12.609 | 112558484 | 112558484 | 697663488 | 697663488 |
| nut-d30-p0.35-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| iso4017:M2.5x5 | stl-preview | 1 | ok | ok: 1 | 1.464 | 1.464 | 0.069 | 0.069 | 460684 | 460684 | 213270528 | 213270528 |
| iso4017:M3x20 | stl-fine | 1 | ok | ok: 1 | 3.552 | 3.552 | 3.028 | 3.028 | 15457684 | 15457684 | 310738944 | 310738944 |
| iso4017:M4x12 | step | 1 | ok | ok: 1 | 1.750 | 1.750 | 0.052 | 0.052 | 1117869 | 1117869 | 217255936 | 217255936 |
| iso4017:M5x40 | stl-preview | 1 | ok | ok: 1 | 3.382 | 3.382 | 0.484 | 0.484 | 3709884 | 3709884 | 249999360 | 249999360 |
| iso4017:M6x60 | stl-fine | 1 | ok | ok: 1 | 3.883 | 3.883 | 5.874 | 5.874 | 30385684 | 30385684 | 389246976 | 389246976 |
| iso4017:M8x16 | step | 1 | ok | ok: 1 | 1.446 | 1.446 | 0.046 | 0.046 | 923224 | 923224 | 216907776 | 216907776 |
| iso4017:M10x25 | stl-preview | 1 | ok | ok: 1 | 1.779 | 1.779 | 0.206 | 0.206 | 1492484 | 1492484 | 223838208 | 223838208 |
| iso4017:M12x25 | stl-fine | 1 | ok | ok: 1 | 1.646 | 1.646 | 3.990 | 3.990 | 19188384 | 19188384 | 500600832 | 500600832 |
| iso4017:M12x110 | step | 1 | ok | ok: 1 | 4.093 | 4.093 | 0.176 | 0.176 | 3943750 | 3943750 | 259694592 | 259694592 |
| iso4017:M14x110 | stl-preview | 1 | ok | ok: 1 | 3.751 | 3.751 | 0.865 | 0.865 | 5643784 | 5643784 | 273383424 | 273383424 |
| iso4017:M16x80 | stl-fine | 1 | ok | ok: 1 | 3.094 | 3.094 | 13.342 | 13.342 | 69553584 | 69553584 | 673075200 | 673075200 |
| iso4017:M18x55 | step | 1 | ok | ok: 1 | 2.116 | 2.116 | 0.071 | 0.071 | 1530308 | 1530308 | 229572608 | 229572608 |
| iso4017:M20x40 | stl-preview | 1 | ok | ok: 1 | 1.791 | 1.791 | 0.544 | 0.544 | 4541784 | 4541784 | 234393600 | 234393600 |
| iso4017:M20x140 | stl-fine | 1 | ok | ok: 1 | 3.909 | 3.909 | 18.405 | 18.405 | 101636184 | 101636184 | 730464256 | 730464256 |
| iso4014:M3.5x20 | step | 1 | ok | ok: 1 | 2.326 | 2.326 | 0.064 | 0.064 | 1291442 | 1291442 | 218767360 | 218767360 |
| iso4014:M6x30 | stl-preview | 1 | ok | ok: 1 | 2.344 | 2.344 | 0.186 | 0.186 | 1476484 | 1476484 | 222117888 | 222117888 |
| iso4014:M7x65 | stl-fine | 1 | ok | ok: 1 | 2.155 | 2.155 | 2.211 | 2.211 | 11039884 | 11039884 | 341909504 | 341909504 |
| iso4014:M10x60 | step | 1 | ok | ok: 1 | 2.208 | 2.208 | 0.053 | 0.053 | 1096248 | 1096248 | 222171136 | 222171136 |
| iso4014:M12x110 | stl-preview | 1 | ok | ok: 1 | 2.296 | 2.296 | 0.245 | 0.245 | 1735684 | 1735684 | 225173504 | 225173504 |
| iso4014:M16x65 | stl-fine | 1 | ok | ok: 1 | 2.484 | 2.484 | 6.547 | 6.547 | 33383384 | 33383384 | 607830016 | 607830016 |
| iso4014:M18x90 | step | 1 | ok | ok: 1 | 2.343 | 2.343 | 0.059 | 0.059 | 1195942 | 1195942 | 225271808 | 225271808 |
| iso4014:M20x130 | stl-preview | 1 | ok | ok: 1 | 2.748 | 2.748 | 0.813 | 0.813 | 6015484 | 6015484 | 249815040 | 249815040 |
| iso4032:M8 | stl-fine | 1 | ok | ok: 1 | 2.456 | 2.456 | 0.918 | 0.918 | 4128684 | 4128684 | 320819200 | 320819200 |
| bolt-d1-p0.35-n3-right | step | 1 | ok | ok: 1 | 0.752 | 0.752 | 0.017 | 0.017 | 276038 | 276038 | 209707008 | 209707008 |
| bolt-d3-p0.35-n30-right | stl-preview | 1 | ok | ok: 1 | 3.079 | 3.079 | 0.253 | 0.253 | 1314984 | 1314984 | 238837760 | 238837760 |
| bolt-d10-p0.1-n30-left | stl-fine | 1 | ok | ok: 1 | 3.332 | 3.332 | 6.133 | 6.133 | 31483684 | 31483684 | 465465344 | 465465344 |
| bolt-d10-p1-n240-right | step | 1 | ok | ok: 1 | 12.854 | 12.854 | 0.661 | 0.661 | 14623285 | 14623285 | 437940224 | 437940224 |
| bolt-d30-p0.35-n3-right | stl-preview | 1 | ok | ok: 1 | 1.545 | 1.545 | 0.167 | 0.167 | 948984 | 948984 | 229699584 | 229699584 |
| bolt-d30-p3-n3-left | stl-fine | 1 | ok | ok: 1 | 1.116 | 1.116 | 1.797 | 1.797 | 6304484 | 6304484 | 458514432 | 458514432 |
| bolt-d100-p0.1-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p10-n240-left | stl-fine | 1 | ok | ok: 1 | 10.213 | 10.213 | 488.197 | 488.197 | 1410575284 | 1410575284 | 5178314752 | 5178314752 |
| bolt-d300-p1-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n30-right | stl-preview | 1 | ok | ok: 1 | 2.688 | 2.688 | 29.912 | 29.912 | 143030684 | 143030684 | 1348022272 | 1348022272 |
| bolt-d1000-p0.35-n30-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n240-right | step | 1 | ok | ok: 1 | 16.260 | 16.260 | 1.274 | 1.274 | 26897137 | 26897137 | 496107520 | 496107520 |
| nut-d3-p1-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 3.009 | 3.009 | 0.084 | 0.084 | 414384 | 414384 | 233160704 | 233160704 |
| nut-d10-p1-m3d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 3.819 | 3.819 | 9.352 | 9.352 | 47932384 | 47932384 | 628236288 | 628236288 |
| nut-d30-p1-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 5.240 | 5.240 | 0.083 | 0.083 | 1672879 | 1672879 | 231268352 | 231268352 |
| nut-d100-p0.35-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 33.519 | 33.519 | 35.232 | 35.232 | 244036284 | 244036284 | 973058048 | 973058048 |
| nut-d100-p3.5-m3d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 13.107 | 13.107 | 216.498 | 216.498 | 638679284 | 638679284 | 3948199936 | 3948199936 |
| nut-d30-p0.35-m0.8d-s1.6d-c0.15-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| iso4017:M2.5x5 | stl-fine | 1 | ok | ok: 1 | 1.199 | 1.199 | 0.611 | 0.611 | 4196584 | 4196584 | 281976832 | 281976832 |
| iso4017:M3x20 | step | 1 | ok | ok: 1 | 2.975 | 2.975 | 0.073 | 0.073 | 2258065 | 2258065 | 230080512 | 230080512 |
| iso4017:M4x16 | stl-preview | 1 | ok | ok: 1 | 1.659 | 1.659 | 0.134 | 0.134 | 1205884 | 1205884 | 220499968 | 220499968 |
| iso4017:M5x40 | stl-fine | 1 | ok | ok: 1 | 2.777 | 2.777 | 3.447 | 3.447 | 24140184 | 24140184 | 369082368 | 369082368 |
| iso4017:M6x60 | step | 1 | ok | ok: 1 | 3.201 | 3.201 | 0.120 | 0.120 | 3710842 | 3710842 | 261115904 | 261115904 |
| iso4017:M8x20 | stl-preview | 1 | ok | ok: 1 | 1.391 | 1.391 | 0.141 | 0.141 | 1356084 | 1356084 | 223301632 | 223301632 |
| iso4017:M10x25 | stl-fine | 1 | ok | ok: 1 | 1.472 | 1.472 | 2.939 | 2.939 | 20298184 | 20298184 | 464625664 | 464625664 |
| iso4017:M12x25 | step | 1 | ok | ok: 1 | 1.338 | 1.338 | 0.035 | 0.035 | 1006850 | 1006850 | 219295744 | 219295744 |
| iso4017:M12x120 | stl-preview | 1 | ok | ok: 1 | 3.592 | 3.592 | 0.680 | 0.680 | 6637584 | 6637584 | 276537344 | 276537344 |
| iso4017:M14x110 | stl-fine | 1 | ok | ok: 1 | 3.068 | 3.068 | 12.988 | 12.988 | 91269584 | 91269584 | 730083328 | 730083328 |
| iso4017:M16x80 | step | 1 | ok | ok: 1 | 2.502 | 2.502 | 0.082 | 0.082 | 2634256 | 2634256 | 246063104 | 246063104 |
| iso4017:M18x60 | stl-preview | 1 | ok | ok: 1 | 1.831 | 1.831 | 0.610 | 0.610 | 6086684 | 6086684 | 242221056 | 242221056 |
| iso4017:M20x40 | stl-fine | 1 | ok | ok: 1 | 1.438 | 1.438 | 4.121 | 4.121 | 28556384 | 28556384 | 598790144 | 598790144 |
| iso4017:M20x140 | step | 1 | ok | ok: 1 | 3.194 | 3.194 | 0.118 | 0.118 | 3609621 | 3609621 | 258347008 | 258347008 |
| iso4014:M3.5x25 | stl-preview | 1 | ok | ok: 1 | 1.951 | 1.951 | 0.120 | 0.120 | 1028084 | 1028084 | 219148288 | 219148288 |
| iso4014:M6x30 | stl-fine | 1 | ok | ok: 1 | 1.923 | 1.923 | 1.379 | 1.379 | 9559584 | 9559584 | 341749760 | 341749760 |
| iso4014:M7x65 | step | 1 | ok | ok: 1 | 1.771 | 1.771 | 0.043 | 0.043 | 1327428 | 1327428 | 222035968 | 222035968 |
| iso4014:M10x65 | stl-preview | 1 | ok | ok: 1 | 1.808 | 1.808 | 0.169 | 0.169 | 1621384 | 1621384 | 225009664 | 225009664 |
| iso4014:M12x110 | stl-fine | 1 | ok | ok: 1 | 1.879 | 1.879 | 3.466 | 3.466 | 23581884 | 23581884 | 475770880 | 475770880 |
| iso4014:M16x65 | step | 1 | ok | ok: 1 | 2.014 | 2.014 | 0.045 | 0.045 | 1352615 | 1352615 | 225570816 | 225570816 |
| iso4014:M18x100 | stl-preview | 1 | ok | ok: 1 | 1.882 | 1.882 | 0.419 | 0.419 | 4191184 | 4191184 | 237379584 | 237379584 |
| iso4014:M20x130 | stl-fine | 1 | ok | ok: 1 | 2.235 | 2.235 | 5.228 | 5.228 | 37736784 | 37736784 | 615006208 | 615006208 |
| iso4032:M8 | step | 1 | ok | ok: 1 | 1.963 | 1.963 | 0.026 | 0.026 | 715222 | 715222 | 214433792 | 214433792 |
| bolt-d1-p0.35-n3-left | stl-preview | 1 | ok | ok: 1 | 0.618 | 0.618 | 0.021 | 0.021 | 133184 | 133184 | 210149376 | 210149376 |
| bolt-d3-p0.35-n30-right | stl-fine | 1 | ok | ok: 1 | 2.491 | 2.491 | 1.808 | 1.808 | 11599184 | 11599184 | 315670528 | 315670528 |
| bolt-d10-p0.1-n30-left | step | 1 | ok | ok: 1 | 2.728 | 2.728 | 0.060 | 0.060 | 1972216 | 1972216 | 232292352 | 232292352 |
| bolt-d10-p1-n240-left | stl-preview | 1 | ok | ok: 1 | 10.857 | 10.857 | 1.742 | 1.742 | 17780284 | 17780284 | 432877568 | 432877568 |
| bolt-d30-p0.35-n3-right | stl-fine | 1 | ok | ok: 1 | 1.252 | 1.252 | 1.791 | 1.791 | 9811684 | 9811684 | 618704896 | 618704896 |
| bolt-d30-p3-n3-left | step | 1 | ok | ok: 1 | 0.919 | 0.919 | 0.016 | 0.016 | 379174 | 379174 | 210423808 | 210423808 |
| bolt-d100-p0.1-n30-left | stl-preview | 1 | ok | ok: 1 | 4.478 | 4.478 | 3.813 | 3.813 | 32677484 | 32677484 | 386166784 | 386166784 |
| bolt-d100-p1-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p10-n240-left | step | 1 | ok | ok: 1 | 8.187 | 8.187 | 0.564 | 0.564 | 16970466 | 16970466 | 434933760 | 434933760 |
| bolt-d300-p1-n3-left | stl-preview | 1 | ok | ok: 1 | 1.915 | 1.915 | 2.916 | 2.916 | 11970884 | 11970884 | 805941248 | 805941248 |
| bolt-d300-p10-n30-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.35-n30-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n240-left | stl-preview | 1 | killed | killed: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p1-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 2.456 | 2.456 | 0.568 | 0.568 | 3904884 | 3904884 | 285831168 | 285831168 |
| nut-d10-p1-m3d-s4d-c5-right | step | 1 | ok | ok: 1 | 3.125 | 3.125 | 0.071 | 0.071 | 2150535 | 2150535 | 227639296 | 227639296 |
| nut-d30-p1-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 2.498 | 2.498 | 0.990 | 0.990 | 8859184 | 8859184 | 261750784 | 261750784 |
| nut-d100-p0.35-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 27.733 | 27.733 | 341.605 | 341.605 | 1228615684 | 1228615684 | 5491482624 | 5491482624 |
| nut-d100-p3.5-m3d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 10.788 | 10.788 | 0.212 | 0.212 | 6379510 | 6379510 | 262483968 | 262483968 |
| nut-d30-p1-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 4.582 | 4.582 | 0.492 | 0.492 | 5008884 | 5008884 | 244469760 | 244469760 |
| iso4017:M2.5x5 | step | 1 | ok | ok: 1 | 1.205 | 1.205 | 0.024 | 0.024 | 681359 | 681359 | 211730432 | 211730432 |
| iso4017:M3x25 | stl-preview | 1 | ok | ok: 1 | 3.828 | 3.828 | 0.237 | 0.237 | 2205884 | 2205884 | 243044352 | 243044352 |
| iso4017:M4x16 | stl-fine | 1 | ok | ok: 1 | 1.685 | 1.685 | 1.539 | 1.539 | 10700184 | 10700184 | 325722112 | 325722112 |
| iso4017:M5x40 | step | 1 | ok | ok: 1 | 2.763 | 2.763 | 0.093 | 0.093 | 3088099 | 3088099 | 247779328 | 247779328 |
| iso4017:M7x16 | stl-preview | 1 | ok | ok: 1 | 1.374 | 1.374 | 0.131 | 0.131 | 1336284 | 1336284 | 223879168 | 223879168 |
| iso4017:M8x20 | stl-fine | 1 | ok | ok: 1 | 1.380 | 1.380 | 1.836 | 1.836 | 13646284 | 13646284 | 369401856 | 369401856 |
| iso4017:M10x25 | step | 1 | ok | ok: 1 | 1.446 | 1.446 | 0.035 | 0.035 | 1059197 | 1059197 | 221880320 | 221880320 |
| iso4017:M12x30 | stl-preview | 1 | ok | ok: 1 | 1.480 | 1.480 | 0.183 | 0.183 | 1702684 | 1702684 | 225886208 | 225886208 |
| iso4017:M12x120 | stl-fine | 1 | ok | ok: 1 | 3.577 | 3.577 | 12.084 | 12.084 | 93819084 | 93819084 | 685625344 | 685625344 |
| iso4017:M14x110 | step | 1 | ok | ok: 1 | 3.046 | 3.046 | 0.106 | 0.106 | 3516935 | 3516935 | 257748992 | 257748992 |
| iso4017:M16x90 | stl-preview | 1 | ok | ok: 1 | 2.824 | 2.824 | 0.848 | 0.848 | 7415884 | 7415884 | 265043968 | 265043968 |
| iso4017:M18x60 | stl-fine | 1 | ok | ok: 1 | 1.828 | 1.828 | 5.661 | 5.661 | 42112984 | 42112984 | 545935360 | 545935360 |
| iso4017:M20x40 | step | 1 | ok | ok: 1 | 1.432 | 1.432 | 0.038 | 0.038 | 1162137 | 1162137 | 222674944 | 222674944 |
| iso4017:M20x150 | stl-preview | 1 | ok | ok: 1 | 3.315 | 3.315 | 1.522 | 1.522 | 17195584 | 17195584 | 283758592 | 283758592 |
| iso4014:M3.5x25 | stl-fine | 1 | ok | ok: 1 | 1.951 | 1.951 | 1.363 | 1.363 | 9105084 | 9105084 | 315547648 | 315547648 |
| iso4014:M6x30 | step | 1 | ok | ok: 1 | 1.917 | 1.917 | 0.038 | 0.038 | 1211690 | 1211690 | 220729344 | 220729344 |
| iso4014:M7x70 | stl-preview | 1 | ok | ok: 1 | 1.770 | 1.770 | 0.158 | 0.158 | 1646684 | 1646684 | 223539200 | 223539200 |
| iso4014:M10x65 | stl-fine | 1 | ok | ok: 1 | 1.790 | 1.790 | 2.908 | 2.908 | 21537884 | 21537884 | 459517952 | 459517952 |
| iso4014:M12x110 | step | 1 | ok | ok: 1 | 1.868 | 1.868 | 0.039 | 0.039 | 1187185 | 1187185 | 221110272 | 221110272 |
| iso4014:M16x70 | stl-preview | 1 | ok | ok: 1 | 1.998 | 1.998 | 0.340 | 0.340 | 3143384 | 3143384 | 235720704 | 235720704 |
| iso4014:M18x100 | stl-fine | 1 | ok | ok: 1 | 1.893 | 1.893 | 4.032 | 4.032 | 29404684 | 29404684 | 551292928 | 551292928 |
| iso4014:M20x130 | step | 1 | ok | ok: 1 | 2.244 | 2.244 | 0.047 | 0.047 | 1465961 | 1465961 | 225116160 | 225116160 |
| iso4032:M10 | stl-preview | 1 | ok | ok: 1 | 1.808 | 1.808 | 0.050 | 0.050 | 413484 | 413484 | 216461312 | 216461312 |
| bolt-d1-p0.35-n3-left | stl-fine | 1 | ok | ok: 1 | 0.616 | 0.616 | 0.129 | 0.129 | 883684 | 883684 | 247664640 | 247664640 |
| bolt-d3-p0.35-n30-right | step | 1 | ok | ok: 1 | 2.514 | 2.514 | 0.055 | 0.055 | 1728213 | 1728213 | 227479552 | 227479552 |
| bolt-d10-p0.1-n240-right | stl-preview | 1 | ok | ok: 1 | 14.378 | 14.378 | 2.145 | 2.145 | 22334984 | 22334984 | 444776448 | 444776448 |
| bolt-d10-p1-n240-left | stl-fine | 1 | ok | ok: 1 | 10.782 | 10.782 | 31.228 | 31.228 | 233823984 | 233823984 | 978202624 | 978202624 |
| bolt-d30-p0.35-n3-right | step | 1 | ok | ok: 1 | 1.251 | 1.251 | 0.017 | 0.017 | 413353 | 413353 | 210714624 | 210714624 |
| bolt-d30-p3-n30-right | stl-preview | 1 | ok | ok: 1 | 1.946 | 1.946 | 0.895 | 0.895 | 9724584 | 9724584 | 256581632 | 256581632 |
| bolt-d100-p0.1-n30-left | stl-fine | 1 | ok | ok: 1 | 4.450 | 4.450 | 63.242 | 63.242 | 262200384 | 262200384 | 3404754944 | 3404754944 |
| bolt-d100-p1-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p0.1-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n3-left | stl-fine | 1 | ok | ok: 1 | 1.896 | 1.896 | 41.229 | 41.229 | 65886884 | 65886884 | 8330854400 | 8330854400 |
| bolt-d300-p10-n30-right | step | 1 | ok | ok: 1 | 2.140 | 2.140 | 0.090 | 0.090 | 2749280 | 2749280 | 236924928 | 236924928 |
| bolt-d1000-p0.35-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n240-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p1-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 2.432 | 2.432 | 0.028 | 0.028 | 790724 | 790724 | 222584832 | 222584832 |
| nut-d10-p3.5-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 1.244 | 1.244 | 0.021 | 0.021 | 176884 | 176884 | 213336064 | 213336064 |
| nut-d30-p1-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 2.471 | 2.471 | 20.942 | 20.942 | 132196084 | 132196084 | 1480900608 | 1480900608 |
| nut-d100-p0.35-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 27.582 | 27.582 | 0.434 | 0.434 | 13269426 | 13269426 | 335781888 | 335781888 |
| nut-d100-p3.5-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 10.244 | 10.244 | 11.496 | 11.496 | 107595584 | 107595584 | 620945408 | 620945408 |
| nut-d30-p1-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 4.555 | 4.555 | 9.098 | 9.098 | 54761584 | 54761584 | 863358976 | 863358976 |
| iso4017:M2.5x6 | stl-preview | 1 | ok | ok: 1 | 1.282 | 1.282 | 0.064 | 0.064 | 555784 | 555784 | 215429120 | 215429120 |
| iso4017:M3x25 | stl-fine | 1 | ok | ok: 1 | 3.823 | 3.823 | 2.816 | 2.816 | 19112184 | 19112184 | 312426496 | 312426496 |
| iso4017:M4x16 | step | 1 | ok | ok: 1 | 1.660 | 1.660 | 0.048 | 0.048 | 1467792 | 1467792 | 220594176 | 220594176 |
| iso4017:M5x45 | stl-preview | 1 | ok | ok: 1 | 3.013 | 3.013 | 0.478 | 0.478 | 4168884 | 4168884 | 260227072 | 260227072 |
| iso4017:M7x16 | stl-fine | 1 | ok | ok: 1 | 1.383 | 1.383 | 1.297 | 1.297 | 8729984 | 8729984 | 316137472 | 316137472 |
| iso4017:M8x20 | step | 1 | ok | ok: 1 | 1.465 | 1.465 | 0.037 | 0.037 | 1105324 | 1105324 | 222699520 | 222699520 |
| iso4017:M10x30 | stl-preview | 1 | ok | ok: 1 | 1.606 | 1.606 | 0.193 | 0.193 | 1866384 | 1866384 | 225808384 | 225808384 |
| iso4017:M12x30 | stl-fine | 1 | ok | ok: 1 | 1.502 | 1.502 | 3.727 | 3.727 | 23155084 | 23155084 | 492695552 | 492695552 |
| iso4017:M12x120 | step | 1 | ok | ok: 1 | 3.592 | 3.592 | 0.135 | 0.135 | 4274939 | 4274939 | 285876224 | 285876224 |
| iso4017:M14x120 | stl-preview | 1 | ok | ok: 1 | 3.313 | 3.313 | 0.750 | 0.750 | 6141184 | 6141184 | 267165696 | 267165696 |
| iso4017:M16x90 | stl-fine | 1 | ok | ok: 1 | 2.729 | 2.729 | 11.923 | 11.923 | 78141584 | 78141584 | 682688512 | 682688512 |
| iso4017:M18x60 | step | 1 | ok | ok: 1 | 1.836 | 1.836 | 0.054 | 0.054 | 1640995 | 1640995 | 227704832 | 227704832 |
| iso4017:M20x45 | stl-preview | 1 | ok | ok: 1 | 1.577 | 1.577 | 0.470 | 0.470 | 5112784 | 5112784 | 237658112 | 237658112 |
| iso4017:M20x150 | stl-fine | 1 | ok | ok: 1 | 3.423 | 3.423 | 14.761 | 14.761 | 107260584 | 107260584 | 792883200 | 792883200 |
| iso4014:M3.5x25 | step | 1 | ok | ok: 1 | 1.953 | 1.953 | 0.046 | 0.046 | 1291453 | 1291453 | 219299840 | 219299840 |
| iso4014:M6x35 | stl-preview | 1 | ok | ok: 1 | 1.925 | 1.925 | 0.141 | 0.141 | 1476484 | 1476484 | 221671424 | 221671424 |
| iso4014:M7x70 | stl-fine | 1 | ok | ok: 1 | 1.776 | 1.776 | 1.735 | 1.735 | 11039884 | 11039884 | 325660672 | 325660672 |
| iso4014:M10x65 | step | 1 | ok | ok: 1 | 1.824 | 1.824 | 0.040 | 0.040 | 1096249 | 1096249 | 222019584 | 222019584 |
| iso4014:M12x120 | stl-preview | 1 | ok | ok: 1 | 1.875 | 1.875 | 0.187 | 0.187 | 1735684 | 1735684 | 225112064 | 225112064 |
| iso4014:M16x70 | stl-fine | 1 | ok | ok: 1 | 2.048 | 2.048 | 5.360 | 5.360 | 33383384 | 33383384 | 640532480 | 640532480 |
| iso4014:M18x100 | step | 1 | ok | ok: 1 | 1.883 | 1.883 | 0.041 | 0.041 | 1195969 | 1195969 | 224272384 | 224272384 |
| iso4014:M20x140 | stl-preview | 1 | ok | ok: 1 | 2.327 | 2.327 | 0.540 | 0.540 | 6015484 | 6015484 | 238583808 | 238583808 |
| iso4032:M10 | stl-fine | 1 | ok | ok: 1 | 1.828 | 1.828 | 0.951 | 0.951 | 5450784 | 5450784 | 344682496 | 344682496 |
| bolt-d1-p0.35-n3-left | step | 1 | ok | ok: 1 | 0.635 | 0.635 | 0.015 | 0.015 | 276100 | 276100 | 209707008 | 209707008 |
| bolt-d3-p0.35-n30-left | stl-preview | 1 | ok | ok: 1 | 2.598 | 2.598 | 0.129 | 0.129 | 1146384 | 1146384 | 223395840 | 223395840 |
| bolt-d10-p0.1-n240-right | stl-fine | 1 | ok | ok: 1 | 14.472 | 14.472 | 45.284 | 45.284 | 326820084 | 326820084 | 1283031040 | 1283031040 |
| bolt-d10-p1-n240-left | step | 1 | ok | ok: 1 | 10.910 | 10.910 | 0.472 | 0.472 | 14622598 | 14622598 | 423907328 | 423907328 |
| bolt-d30-p0.35-n3-left | stl-preview | 1 | ok | ok: 1 | 1.218 | 1.218 | 0.107 | 0.107 | 768084 | 768084 | 228876288 | 228876288 |
| bolt-d30-p3-n30-right | stl-fine | 1 | ok | ok: 1 | 1.962 | 1.962 | 13.519 | 13.519 | 87710484 | 87710484 | 1021014016 | 1021014016 |
| bolt-d100-p0.1-n30-left | step | 1 | ok | ok: 1 | 4.479 | 4.479 | 0.084 | 0.084 | 2562441 | 2562441 | 255508480 | 255508480 |
| bolt-d100-p1-n240-left | stl-preview | 1 | ok | ok: 1 | 11.699 | 11.699 | 28.054 | 28.054 | 244702384 | 244702384 | 989044736 | 989044736 |
| bolt-d300-p0.1-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n3-left | step | 1 | ok | ok: 1 | 1.901 | 1.901 | 0.021 | 0.021 | 526100 | 526100 | 212762624 | 212762624 |
| bolt-d300-p10-n30-left | stl-preview | 1 | ok | ok: 1 | 2.161 | 2.161 | 21.761 | 21.761 | 109037084 | 109037084 | 1095122944 | 1095122944 |
| bolt-d1000-p0.35-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p3-n240-left | step | 1 | ok | ok: 1 | 12.864 | 12.864 | 0.943 | 0.943 | 27005746 | 27005746 | 592257024 | 592257024 |
| nut-d3-p1-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 2.159 | 2.159 | 0.049 | 0.049 | 414384 | 414384 | 212762624 | 212762624 |
| nut-d10-p3.5-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.249 | 1.249 | 0.274 | 0.274 | 1922084 | 1922084 | 270004224 | 270004224 |
| nut-d30-p1-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 2.491 | 2.491 | 0.066 | 0.066 | 1874594 | 1874594 | 220880896 | 220880896 |
| nut-d100-p0.35-m0.8d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 30.515 | 30.515 | 30.135 | 30.135 | 281672284 | 281672284 | 1036431360 | 1036431360 |
| nut-d100-p3.5-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 10.256 | 10.256 | 151.698 | 151.698 | 603580284 | 603580284 | 3634495488 | 3634495488 |
| nut-d30-p1-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 4.550 | 4.550 | 0.055 | 0.055 | 1666452 | 1666452 | 235679744 | 235679744 |
| iso4017:M2.5x6 | stl-fine | 1 | ok | ok: 1 | 1.468 | 1.468 | 0.847 | 0.847 | 5012084 | 5012084 | 287457280 | 287457280 |
| iso4017:M3x25 | step | 1 | ok | ok: 1 | 4.372 | 4.372 | 0.119 | 0.119 | 2778435 | 2778435 | 242790400 | 242790400 |
| iso4017:M4x20 | stl-preview | 1 | ok | ok: 1 | 2.110 | 2.110 | 0.191 | 0.191 | 1495684 | 1495684 | 223723520 | 223723520 |
| iso4017:M5x45 | stl-fine | 1 | ok | ok: 1 | 3.478 | 3.478 | 4.692 | 4.692 | 27223884 | 27223884 | 364257280 | 364257280 |
| iso4017:M7x16 | step | 1 | ok | ok: 1 | 1.592 | 1.592 | 0.049 | 0.049 | 1101795 | 1101795 | 221941760 | 221941760 |
| iso4017:M8x25 | stl-preview | 1 | ok | ok: 1 | 1.851 | 1.851 | 0.205 | 0.205 | 1669584 | 1669584 | 225361920 | 225361920 |
| iso4017:M10x30 | stl-fine | 1 | ok | ok: 1 | 1.837 | 1.837 | 4.246 | 4.246 | 24570184 | 24570184 | 497635328 | 497635328 |
| iso4017:M12x30 | step | 1 | ok | ok: 1 | 1.717 | 1.717 | 0.051 | 0.051 | 1179448 | 1179448 | 222023680 | 222023680 |
| iso4017:M14x30 | stl-preview | 1 | ok | ok: 1 | 1.631 | 1.631 | 0.214 | 0.214 | 1534684 | 1534684 | 225751040 | 225751040 |
| iso4017:M14x120 | stl-fine | 1 | ok | ok: 1 | 3.815 | 3.815 | 17.640 | 17.640 | 99539084 | 99539084 | 755654656 | 755654656 |
| iso4017:M16x90 | step | 1 | ok | ok: 1 | 3.158 | 3.158 | 0.123 | 0.123 | 2928577 | 2928577 | 256401408 | 256401408 |
| iso4017:M18x65 | stl-preview | 1 | ok | ok: 1 | 2.211 | 2.211 | 0.760 | 0.760 | 6455984 | 6455984 | 244121600 | 244121600 |
| iso4017:M20x45 | stl-fine | 1 | ok | ok: 1 | 1.813 | 1.813 | 5.632 | 5.632 | 31989584 | 31989584 | 607547392 | 607547392 |
| iso4017:M20x150 | step | 1 | ok | ok: 1 | 3.868 | 3.868 | 0.162 | 0.162 | 3851941 | 3851941 | 268427264 | 268427264 |
| iso4014:M3.5x30 | stl-preview | 1 | ok | ok: 1 | 2.168 | 2.168 | 0.142 | 0.142 | 1028084 | 1028084 | 220188672 | 220188672 |
| iso4014:M6x35 | stl-fine | 1 | ok | ok: 1 | 2.216 | 2.216 | 1.792 | 1.792 | 9559584 | 9559584 | 339079168 | 339079168 |
| iso4014:M7x70 | step | 1 | ok | ok: 1 | 2.042 | 2.042 | 0.057 | 0.057 | 1327425 | 1327425 | 218517504 | 218517504 |
| iso4014:M10x70 | stl-preview | 1 | ok | ok: 1 | 2.077 | 2.077 | 0.200 | 0.200 | 1621384 | 1621384 | 224436224 | 224436224 |
| iso4014:M12x120 | stl-fine | 1 | ok | ok: 1 | 2.170 | 2.170 | 4.222 | 4.222 | 23581884 | 23581884 | 514154496 | 514154496 |
| iso4014:M16x70 | step | 1 | ok | ok: 1 | 2.320 | 2.320 | 0.059 | 0.059 | 1352615 | 1352615 | 228114432 | 228114432 |
| iso4014:M18x110 | stl-preview | 1 | ok | ok: 1 | 2.164 | 2.164 | 0.504 | 0.504 | 4191184 | 4191184 | 236044288 | 236044288 |
| iso4014:M20x140 | stl-fine | 1 | ok | ok: 1 | 2.576 | 2.576 | 6.583 | 6.583 | 37736784 | 37736784 | 580853760 | 580853760 |
| iso4032:M10 | step | 1 | ok | ok: 1 | 2.151 | 2.151 | 0.035 | 0.035 | 691831 | 691831 | 213925888 | 213925888 |
| bolt-d1-p0.35-n30-right | stl-preview | 1 | ok | ok: 1 | 2.914 | 2.914 | 0.151 | 0.151 | 1329384 | 1329384 | 227528704 | 227528704 |
| bolt-d3-p0.35-n30-left | stl-fine | 1 | ok | ok: 1 | 2.945 | 2.945 | 2.056 | 2.056 | 9301084 | 9301084 | 312336384 | 312336384 |
| bolt-d10-p0.1-n240-right | step | 1 | ok | ok: 1 | 16.419 | 16.419 | 0.696 | 0.696 | 14633131 | 14633131 | 424312832 | 424312832 |
| bolt-d10-p3-n3-right | stl-preview | 1 | ok | ok: 1 | 0.774 | 0.774 | 0.050 | 0.050 | 307284 | 307284 | 213336064 | 213336064 |
| bolt-d30-p0.35-n3-left | stl-fine | 1 | ok | ok: 1 | 1.422 | 1.422 | 1.885 | 1.885 | 8244284 | 8244284 | 543776768 | 543776768 |
| bolt-d30-p3-n30-right | step | 1 | ok | ok: 1 | 2.249 | 2.249 | 0.091 | 0.091 | 2051111 | 2051111 | 234295296 | 234295296 |
| bolt-d100-p0.1-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n240-left | stl-fine | 1 | ok | ok: 1 | 13.178 | 13.178 | 481.658 | 481.658 | 1298093084 | 1298093084 | 5353664512 | 5353664512 |
| bolt-d300-p0.1-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n30-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.35-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n3-right | stl-preview | 1 | ok | ok: 1 | 1.894 | 1.894 | 14.290 | 14.290 | 38443884 | 38443884 | 2836348928 | 2836348928 |
| nut-d3-p1-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 2.485 | 2.485 | 0.721 | 0.721 | 3914484 | 3914484 | 286285824 | 286285824 |
| nut-d10-p3.5-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 1.456 | 1.456 | 0.026 | 0.026 | 500828 | 500828 | 212312064 | 212312064 |
| nut-d30-p1-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 12.302 | 12.302 | 3.242 | 3.242 | 27951284 | 27951284 | 320716800 | 320716800 |
| nut-d100-p0.35-m0.8d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 34.844 | 34.844 | 516.420 | 516.420 | 1475720184 | 1475720184 | 5946900480 | 5946900480 |
| nut-d100-p3.5-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 11.467 | 11.467 | 0.272 | 0.272 | 6102635 | 6102635 | 260177920 | 260177920 |
| nut-d30-p1-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 12.254 | 12.254 | 2.578 | 2.578 | 21736084 | 21736084 | 294141952 | 294141952 |
| iso4017:M2x4 | step | 1 | ok | ok: 1 | 1.287 | 1.287 | 0.033 | 0.033 | 648065 | 648065 | 215027712 | 215027712 |
| iso4017:M2.5x20 | stl-preview | 1 | ok | ok: 1 | 4.017 | 4.017 | 0.258 | 0.258 | 1848284 | 1848284 | 240128000 | 240128000 |
| iso4017:M3.5x16 | stl-fine | 1 | ok | ok: 1 | 2.116 | 2.116 | 2.368 | 2.368 | 10646984 | 10646984 | 328208384 | 328208384 |
| iso4017:M4x40 | step | 1 | ok | ok: 1 | 3.399 | 3.399 | 0.157 | 0.157 | 3561527 | 3561527 | 246329344 | 246329344 |
| iso4017:M6x25 | stl-preview | 1 | ok | ok: 1 | 2.002 | 2.002 | 0.253 | 0.253 | 2017884 | 2017884 | 229998592 | 229998592 |
| iso4017:M7x40 | stl-fine | 1 | ok | ok: 1 | 2.862 | 2.862 | 4.168 | 4.168 | 21404184 | 21404184 | 333799424 | 333799424 |
| iso4017:M8x45 | step | 1 | ok | ok: 1 | 2.691 | 2.691 | 0.101 | 0.101 | 2298715 | 2298715 | 233488384 | 233488384 |
| iso4017:M10x55 | stl-preview | 1 | ok | ok: 1 | 2.629 | 2.629 | 0.444 | 0.444 | 3309384 | 3309384 | 234852352 | 234852352 |
| iso4017:M12x55 | stl-fine | 1 | ok | ok: 1 | 2.454 | 2.454 | 7.927 | 7.927 | 42760084 | 42760084 | 564178944 | 564178944 |
| iso4017:M14x50 | step | 1 | ok | ok: 1 | 2.225 | 2.225 | 0.076 | 0.076 | 1692698 | 1692698 | 233082880 | 233082880 |
| iso4017:M16x40 | stl-preview | 1 | ok | ok: 1 | 2.055 | 2.055 | 0.485 | 0.485 | 3219384 | 3219384 | 233943040 | 233943040 |
| iso4017:M16x140 | stl-fine | 1 | ok | ok: 1 | 4.602 | 4.602 | 22.465 | 22.465 | 121922084 | 121922084 | 845905920 | 845905920 |
| iso4017:M18x100 | step | 1 | ok | ok: 1 | 3.064 | 3.064 | 0.125 | 0.125 | 2641732 | 2641732 | 251240448 | 251240448 |
| iso4017:M20x70 | stl-preview | 1 | ok | ok: 1 | 2.396 | 2.396 | 0.978 | 0.978 | 7994084 | 7994084 | 257396736 | 257396736 |
| iso4014:M2x20 | stl-fine | 1 | ok | ok: 1 | 3.301 | 3.301 | 1.508 | 1.508 | 8250284 | 8250284 | 278433792 | 278433792 |
| iso4014:M4x35 | step | 1 | ok | ok: 1 | 2.271 | 2.271 | 0.059 | 0.059 | 1298277 | 1298277 | 219414528 | 219414528 |
| iso4014:M6x60 | stl-preview | 1 | ok | ok: 1 | 2.265 | 2.265 | 0.184 | 0.184 | 1476484 | 1476484 | 221655040 | 221655040 |
| iso4014:M8x60 | stl-fine | 1 | ok | ok: 1 | 2.389 | 2.389 | 2.730 | 2.730 | 14707484 | 14707484 | 380030976 | 380030976 |
| iso4014:M12x50 | step | 1 | ok | ok: 1 | 2.329 | 2.329 | 0.056 | 0.056 | 1187156 | 1187156 | 223002624 | 223002624 |
| iso4014:M14x80 | stl-preview | 1 | ok | ok: 1 | 2.348 | 2.348 | 0.272 | 0.272 | 1835884 | 1835884 | 226062336 | 226062336 |
| iso4014:M16x120 | stl-fine | 1 | ok | ok: 1 | 2.355 | 2.355 | 6.152 | 6.152 | 33383384 | 33383384 | 590499840 | 590499840 |
| iso4014:M18x150 | step | 1 | ok | ok: 1 | 2.433 | 2.433 | 0.064 | 0.064 | 1368870 | 1368870 | 224362496 | 224362496 |
| iso4032:M2 | stl-preview | 1 | ok | ok: 1 | 2.247 | 2.247 | 0.029 | 0.029 | 176384 | 176384 | 212713472 | 212713472 |
| iso4032:M20 | stl-fine | 1 | ok | ok: 1 | 2.717 | 2.717 | 2.020 | 2.020 | 10583284 | 10583284 | 459890688 | 459890688 |
| bolt-d3-p0.1-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n30-right | stl-preview | 1 | ok | ok: 1 | 3.146 | 3.146 | 0.238 | 0.238 | 1281384 | 1281384 | 233197568 | 233197568 |
| bolt-d10-p0.35-n30-left | stl-fine | 1 | ok | ok: 1 | 3.103 | 3.103 | 6.058 | 6.058 | 31212484 | 31212484 | 468570112 | 468570112 |
| bolt-d10-p3-n240-right | step | 1 | ok | ok: 1 | 12.859 | 12.859 | 0.619 | 0.619 | 13362313 | 13362313 | 405192704 | 405192704 |
| bolt-d30-p1-n3-right | stl-preview | 1 | ok | ok: 1 | 1.271 | 1.271 | 0.158 | 0.158 | 940484 | 940484 | 230555648 | 230555648 |
| bolt-d30-p10-n3-left | stl-fine | 1 | ok | ok: 1 | 0.903 | 0.903 | 1.506 | 1.506 | 6016484 | 6016484 | 482213888 | 482213888 |
| bolt-d100-p0.35-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n240-right | stl-preview | 1 | ok | ok: 1 | 11.406 | 11.406 | 45.638 | 45.638 | 318477984 | 318477984 | 1118269440 | 1118269440 |
| bolt-d300-p0.1-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n3-right | step | 1 | ok | ok: 1 | 1.699 | 1.699 | 0.027 | 0.027 | 496563 | 496563 | 213209088 | 213209088 |
| bolt-d1000-p0.1-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n30-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n240-right | step | 1 | ok | ok: 1 | 12.649 | 12.649 | 1.329 | 1.329 | 28836791 | 28836791 | 602935296 | 602935296 |
| nut-d10-p0.35-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 11.154 | 11.154 | 0.969 | 0.969 | 7503484 | 7503484 | 253968384 | 253968384 |
| nut-d10-p3.5-m3d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 1.680 | 1.680 | 3.473 | 3.473 | 17494884 | 17494884 | 541024256 | 541024256 |
| nut-d30-p3.5-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 2.626 | 2.626 | 0.046 | 0.046 | 919161 | 919161 | 212979712 | 212979712 |
| nut-d100-p1-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 11.377 | 11.377 | 12.205 | 12.205 | 84501884 | 84501884 | 570310656 | 570310656 |
| nut-d3-p1-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 2.928 | 2.928 | 0.754 | 0.754 | 3260284 | 3260284 | 300015616 | 300015616 |
| nut-d100-p1-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 12.955 | 12.955 | 0.235 | 0.235 | 5061318 | 5061318 | 261595136 | 261595136 |
| iso4017:M2.5x6 | step | 1 | ok | ok: 1 | 1.474 | 1.474 | 0.037 | 0.037 | 809548 | 809548 | 214081536 | 214081536 |
| iso4017:M3x30 | stl-preview | 1 | ok | ok: 1 | 5.249 | 5.249 | 0.344 | 0.344 | 2645184 | 2645184 | 246030336 | 246030336 |
| iso4017:M4x20 | stl-fine | 1 | ok | ok: 1 | 2.103 | 2.103 | 2.610 | 2.610 | 13490484 | 13490484 | 332152832 | 332152832 |
| iso4017:M5x45 | step | 1 | ok | ok: 1 | 3.438 | 3.438 | 0.142 | 0.142 | 3469842 | 3469842 | 261189632 | 261189632 |
| iso4017:M7x20 | stl-preview | 1 | ok | ok: 1 | 1.864 | 1.864 | 0.189 | 0.189 | 1641684 | 1641684 | 224464896 | 224464896 |
| iso4017:M8x25 | stl-fine | 1 | ok | ok: 1 | 1.785 | 1.785 | 2.907 | 2.907 | 16806684 | 16806684 | 373350400 | 373350400 |
| iso4017:M10x30 | step | 1 | ok | ok: 1 | 1.812 | 1.812 | 0.054 | 0.054 | 1227919 | 1227919 | 227323904 | 227323904 |
| iso4017:M12x35 | stl-preview | 1 | ok | ok: 1 | 1.825 | 1.825 | 0.254 | 0.254 | 1988384 | 1988384 | 228323328 | 228323328 |
| iso4017:M14x30 | stl-fine | 1 | ok | ok: 1 | 1.602 | 1.602 | 4.682 | 4.682 | 24680284 | 24680284 | 594464768 | 594464768 |
| iso4017:M14x120 | step | 1 | ok | ok: 1 | 3.733 | 3.733 | 0.156 | 0.156 | 3805464 | 3805464 | 266145792 | 266145792 |
| iso4017:M16x100 | stl-preview | 1 | ok | ok: 1 | 3.319 | 3.319 | 1.060 | 1.060 | 8183184 | 8183184 | 261885952 | 261885952 |
| iso4017:M18x65 | stl-fine | 1 | ok | ok: 1 | 2.164 | 2.164 | 7.810 | 7.810 | 45816184 | 45816184 | 578228224 | 578228224 |
| iso4017:M20x45 | step | 1 | ok | ok: 1 | 1.780 | 1.780 | 0.055 | 0.055 | 1272545 | 1272545 | 225775616 | 225775616 |
| iso4017:M20x160 | stl-preview | 1 | ok | ok: 1 | 4.006 | 4.006 | 1.820 | 1.820 | 18350484 | 18350484 | 306364416 | 306364416 |
| iso4014:M3.5x30 | stl-fine | 1 | ok | ok: 1 | 2.116 | 2.116 | 1.852 | 1.852 | 9105084 | 9105084 | 325095424 | 325095424 |
| iso4014:M6x35 | step | 1 | ok | ok: 1 | 2.172 | 2.172 | 0.052 | 0.052 | 1211687 | 1211687 | 221446144 | 221446144 |
| iso4014:M8x40 | stl-preview | 1 | ok | ok: 1 | 2.289 | 2.289 | 0.177 | 0.177 | 1541284 | 1541284 | 222326784 | 222326784 |
| iso4014:M10x70 | stl-fine | 1 | ok | ok: 1 | 2.034 | 2.034 | 3.715 | 3.715 | 21537884 | 21537884 | 491065344 | 491065344 |
| iso4014:M12x120 | step | 1 | ok | ok: 1 | 2.107 | 2.107 | 0.050 | 0.050 | 1187175 | 1187175 | 222244864 | 222244864 |
| iso4014:M16x80 | stl-preview | 1 | ok | ok: 1 | 2.223 | 2.223 | 0.403 | 0.403 | 3143384 | 3143384 | 227885056 | 227885056 |
| iso4014:M18x110 | stl-fine | 1 | ok | ok: 1 | 2.127 | 2.127 | 5.022 | 5.022 | 29404684 | 29404684 | 551374848 | 551374848 |
| iso4014:M20x140 | step | 1 | ok | ok: 1 | 2.513 | 2.513 | 0.062 | 0.062 | 1465961 | 1465961 | 226689024 | 226689024 |
| iso4032:M12 | stl-preview | 1 | ok | ok: 1 | 2.334 | 2.334 | 0.065 | 0.065 | 505384 | 505384 | 217522176 | 217522176 |
| bolt-d1-p0.35-n30-right | stl-fine | 1 | ok | ok: 1 | 2.830 | 2.830 | 1.548 | 1.548 | 9200484 | 9200484 | 271405056 | 271405056 |
| bolt-d3-p0.35-n30-left | step | 1 | ok | ok: 1 | 2.867 | 2.867 | 0.070 | 0.070 | 1726441 | 1726441 | 224894976 | 224894976 |
| bolt-d10-p0.1-n240-left | stl-preview | 1 | ok | ok: 1 | 16.164 | 16.164 | 2.088 | 2.088 | 17703384 | 17703384 | 432197632 | 432197632 |
| bolt-d10-p3-n3-right | stl-fine | 1 | ok | ok: 1 | 0.764 | 0.764 | 0.654 | 0.654 | 3249184 | 3249184 | 322088960 | 322088960 |
| bolt-d30-p0.35-n3-left | step | 1 | ok | ok: 1 | 1.371 | 1.371 | 0.021 | 0.021 | 413620 | 413620 | 210452480 | 210452480 |
| bolt-d30-p3-n30-left | stl-preview | 1 | ok | ok: 1 | 2.210 | 2.210 | 0.851 | 0.851 | 7486284 | 7486284 | 247578624 | 247578624 |
| bolt-d100-p0.1-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p1-n240-left | step | 1 | ok | ok: 1 | 12.975 | 12.975 | 0.749 | 0.749 | 16464992 | 16464992 | 486645760 | 486645760 |
| bolt-d300-p0.1-n3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n30-left | step | 1 | ok | ok: 1 | 2.435 | 2.435 | 0.117 | 0.117 | 2748102 | 2748102 | 240029696 | 240029696 |
| bolt-d1000-p0.35-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n3-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p1-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 2.443 | 2.443 | 0.037 | 0.037 | 790372 | 790372 | 211120128 | 211120128 |
| nut-d10-p3.5-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 1.355 | 1.355 | 0.025 | 0.025 | 185284 | 185284 | 211943424 | 211943424 |
| nut-d30-p1-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 12.022 | 12.022 | 46.134 | 46.134 | 238009584 | 238009584 | 1351204864 | 1351204864 |
| nut-d100-p0.35-m0.8d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 34.477 | 34.477 | 0.665 | 0.665 | 15018980 | 15018980 | 345104384 | 345104384 |
| nut-d100-p3.5-m3d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 10.953 | 10.953 | 15.493 | 15.493 | 112594484 | 112594484 | 693886976 | 693886976 |
| nut-d30-p1-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 12.045 | 12.045 | 51.260 | 51.260 | 241336084 | 241336084 | 1390944256 | 1390944256 |
| iso4017:M2.5x8 | stl-preview | 1 | ok | ok: 1 | 1.797 | 1.797 | 0.095 | 0.095 | 742584 | 742584 | 216084480 | 216084480 |
| iso4017:M3x30 | stl-fine | 1 | ok | ok: 1 | 5.195 | 5.195 | 4.295 | 4.295 | 23072584 | 23072584 | 336199680 | 336199680 |
| iso4017:M4x20 | step | 1 | ok | ok: 1 | 2.092 | 2.092 | 0.075 | 0.075 | 1830801 | 1830801 | 225038336 | 225038336 |
| iso4017:M5x50 | stl-preview | 1 | ok | ok: 1 | 3.769 | 3.769 | 0.542 | 0.542 | 4632084 | 4632084 | 271413248 | 271413248 |
| iso4017:M7x20 | stl-fine | 1 | ok | ok: 1 | 1.813 | 1.813 | 2.111 | 2.111 | 11016384 | 11016384 | 339468288 | 339468288 |
| iso4017:M8x25 | step | 1 | ok | ok: 1 | 1.785 | 1.785 | 0.058 | 0.058 | 1328615 | 1328615 | 222748672 | 222748672 |
| iso4017:M10x35 | stl-preview | 1 | ok | ok: 1 | 1.945 | 1.945 | 0.254 | 0.254 | 2136184 | 2136184 | 231223296 | 231223296 |
| iso4017:M12x35 | stl-fine | 1 | ok | ok: 1 | 1.838 | 1.838 | 5.038 | 5.038 | 27078884 | 27078884 | 555511808 | 555511808 |
| iso4017:M14x30 | step | 1 | ok | ok: 1 | 1.606 | 1.606 | 0.048 | 0.048 | 1070390 | 1070390 | 220090368 | 220090368 |
| iso4017:M14x130 | stl-preview | 1 | ok | ok: 1 | 3.949 | 3.949 | 0.896 | 0.896 | 6711984 | 6711984 | 271613952 | 271613952 |
| iso4017:M16x100 | stl-fine | 1 | ok | ok: 1 | 3.360 | 3.360 | 16.019 | 16.019 | 86231284 | 86231284 | 705515520 | 705515520 |
| iso4017:M18x65 | step | 1 | ok | ok: 1 | 2.157 | 2.157 | 0.077 | 0.077 | 1766093 | 1766093 | 231976960 | 231976960 |
| iso4017:M20x50 | stl-preview | 1 | ok | ok: 1 | 1.871 | 1.871 | 0.593 | 0.593 | 5547684 | 5547684 | 239403008 | 239403008 |
| iso4017:M20x160 | stl-fine | 1 | ok | ok: 1 | 3.923 | 3.923 | 19.553 | 19.553 | 114581284 | 114581284 | 774619136 | 774619136 |
| iso4014:M3.5x30 | step | 1 | ok | ok: 1 | 2.125 | 2.125 | 0.058 | 0.058 | 1291410 | 1291410 | 217997312 | 217997312 |
| iso4014:M6x40 | stl-preview | 1 | ok | ok: 1 | 2.163 | 2.163 | 0.165 | 0.165 | 1476484 | 1476484 | 222429184 | 222429184 |
| iso4014:M8x40 | stl-fine | 1 | ok | ok: 1 | 2.322 | 2.322 | 2.606 | 2.606 | 14707484 | 14707484 | 399323136 | 399323136 |
| iso4014:M10x70 | step | 1 | ok | ok: 1 | 2.043 | 2.043 | 0.048 | 0.048 | 1096224 | 1096224 | 223162368 | 223162368 |
| iso4014:M14x55 | stl-preview | 1 | ok | ok: 1 | 2.226 | 2.226 | 0.241 | 0.241 | 1835884 | 1835884 | 226516992 | 226516992 |
| iso4014:M16x80 | stl-fine | 1 | ok | ok: 1 | 2.253 | 2.253 | 6.272 | 6.272 | 33383384 | 33383384 | 617594880 | 617594880 |
| iso4014:M18x110 | step | 1 | ok | ok: 1 | 2.160 | 2.160 | 0.053 | 0.053 | 1195973 | 1195973 | 223645696 | 223645696 |
| iso4014:M20x150 | stl-preview | 1 | ok | ok: 1 | 2.519 | 2.519 | 0.627 | 0.627 | 6015484 | 6015484 | 235139072 | 235139072 |
| iso4032:M12 | stl-fine | 1 | ok | ok: 1 | 2.299 | 2.299 | 1.481 | 1.481 | 7107584 | 7107584 | 408682496 | 408682496 |
| bolt-d1-p0.35-n30-right | step | 1 | ok | ok: 1 | 2.832 | 2.832 | 0.071 | 0.071 | 1631516 | 1631516 | 223776768 | 223776768 |
| bolt-d3-p0.35-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.1-n240-left | stl-fine | 1 | ok | ok: 1 | 16.132 | 16.132 | 46.845 | 46.845 | 251806684 | 251806684 | 1006366720 | 1006366720 |
| bolt-d10-p3-n3-right | step | 1 | ok | ok: 1 | 0.756 | 0.756 | 0.018 | 0.018 | 309060 | 309060 | 209813504 | 209813504 |
| bolt-d30-p0.35-n30-right | stl-preview | 1 | ok | ok: 1 | 3.264 | 3.264 | 1.152 | 1.152 | 9763584 | 9763584 | 255090688 | 255090688 |
| bolt-d30-p3-n30-left | stl-fine | 1 | ok | ok: 1 | 2.203 | 2.203 | 13.817 | 13.817 | 65884484 | 65884484 | 883408896 | 883408896 |
| bolt-d100-p0.1-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n3-right | stl-preview | 1 | ok | ok: 1 | 1.217 | 1.217 | 0.644 | 0.644 | 3726184 | 3726184 | 314576896 | 314576896 |
| bolt-d300-p0.1-n3-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n240-right | stl-preview | 1 | ok | ok: 1 | 10.517 | 10.517 | 223.564 | 223.564 | 1153862984 | 1153862984 | 3675201536 | 3675201536 |
| bolt-d1000-p0.35-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n3-right | step | 1 | ok | ok: 1 | 1.847 | 1.847 | 0.034 | 0.034 | 685519 | 685519 | 217350144 | 217350144 |
| nut-d10-p0.35-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 4.699 | 4.699 | 0.211 | 0.211 | 1776884 | 1776884 | 233799680 | 233799680 |
| nut-d10-p3.5-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.378 | 1.378 | 0.344 | 0.344 | 1948484 | 1948484 | 273424384 | 273424384 |
| nut-d30-p1-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 11.946 | 11.946 | 0.266 | 0.266 | 5848457 | 5848457 | 262459392 | 262459392 |
| nut-d100-p0.35-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 27.725 | 27.725 | 32.378 | 32.378 | 244072284 | 244072284 | 950439936 | 950439936 |
| nut-d100-p3.5-m3d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 10.809 | 10.809 | 210.379 | 210.379 | 638817284 | 638817284 | 4110000128 | 4110000128 |
| nut-d30-p1-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 12.414 | 12.414 | 0.271 | 0.271 | 5836211 | 5836211 | 263393280 | 263393280 |
| iso4017:M2.5x8 | stl-fine | 1 | ok | ok: 1 | 1.291 | 1.291 | 0.745 | 0.745 | 6699184 | 6699184 | 294989824 | 294989824 |
| iso4017:M3x30 | step | 1 | ok | ok: 1 | 3.800 | 3.800 | 0.097 | 0.097 | 3319831 | 3319831 | 246816768 | 246816768 |
| iso4017:M4x25 | stl-preview | 1 | ok | ok: 1 | 1.694 | 1.694 | 0.158 | 0.158 | 1851984 | 1851984 | 226840576 | 226840576 |
| iso4017:M5x50 | stl-fine | 1 | ok | ok: 1 | 2.705 | 2.705 | 3.576 | 3.576 | 30119884 | 30119884 | 363851776 | 363851776 |
| iso4017:M7x20 | step | 1 | ok | ok: 1 | 1.341 | 1.341 | 0.040 | 0.040 | 1322009 | 1322009 | 223977472 | 223977472 |
| iso4017:M8x30 | stl-preview | 1 | ok | ok: 1 | 1.414 | 1.414 | 0.160 | 0.160 | 2031584 | 2031584 | 228503552 | 228503552 |
| iso4017:M10x35 | stl-fine | 1 | ok | ok: 1 | 1.419 | 1.419 | 3.343 | 3.343 | 28586084 | 28586084 | 506691584 | 506691584 |
| iso4017:M12x35 | step | 1 | ok | ok: 1 | 1.324 | 1.324 | 0.040 | 0.040 | 1346939 | 1346939 | 228216832 | 228216832 |
| iso4017:M14x35 | stl-preview | 1 | ok | ok: 1 | 1.249 | 1.249 | 0.165 | 0.165 | 1816284 | 1816284 | 225656832 | 225656832 |
| iso4017:M14x130 | stl-fine | 1 | ok | ok: 1 | 2.880 | 2.880 | 12.681 | 12.681 | 107349284 | 107349284 | 810590208 | 810590208 |
| iso4017:M16x100 | step | 1 | ok | ok: 1 | 2.396 | 2.396 | 0.095 | 0.095 | 3237972 | 3237972 | 258224128 | 258224128 |
| iso4017:M18x70 | stl-preview | 1 | ok | ok: 1 | 1.590 | 1.590 | 0.584 | 0.584 | 7082584 | 7082584 | 245911552 | 245911552 |
| iso4017:M20x50 | stl-fine | 1 | ok | ok: 1 | 1.357 | 1.357 | 4.625 | 4.625 | 37121284 | 37121284 | 610861056 | 610861056 |
| iso4017:M20x160 | step | 1 | ok | ok: 1 | 2.892 | 2.892 | 0.123 | 0.123 | 4110427 | 4110427 | 262447104 | 262447104 |
| iso4014:M3.5x35 | stl-preview | 1 | ok | ok: 1 | 1.558 | 1.558 | 0.097 | 0.097 | 1028084 | 1028084 | 219836416 | 219836416 |
| iso4014:M6x40 | stl-fine | 1 | ok | ok: 1 | 1.535 | 1.535 | 1.087 | 1.087 | 9559584 | 9559584 | 340627456 | 340627456 |
| iso4014:M8x40 | step | 1 | ok | ok: 1 | 1.697 | 1.697 | 0.035 | 0.035 | 1209363 | 1209363 | 222392320 | 222392320 |
| iso4014:M10x80 | stl-preview | 1 | ok | ok: 1 | 1.483 | 1.483 | 0.133 | 0.133 | 1621384 | 1621384 | 224141312 | 224141312 |
| iso4014:M14x55 | stl-fine | 1 | ok | ok: 1 | 1.615 | 1.615 | 3.325 | 3.325 | 27923284 | 27923284 | 559239168 | 559239168 |
| iso4014:M16x80 | step | 1 | ok | ok: 1 | 1.611 | 1.611 | 0.040 | 0.040 | 1352615 | 1352615 | 224980992 | 224980992 |
| iso4014:M18x120 | stl-preview | 1 | ok | ok: 1 | 1.503 | 1.503 | 0.319 | 0.319 | 4191184 | 4191184 | 242663424 | 242663424 |
| iso4014:M20x150 | stl-fine | 1 | ok | ok: 1 | 1.818 | 1.818 | 4.353 | 4.353 | 37736784 | 37736784 | 602796032 | 602796032 |
| iso4032:M12 | step | 1 | ok | ok: 1 | 1.628 | 1.628 | 0.024 | 0.024 | 789753 | 789753 | 215420928 | 215420928 |
| bolt-d1-p0.35-n30-left | stl-preview | 1 | ok | ok: 1 | 2.079 | 2.079 | 0.089 | 0.089 | 1330184 | 1330184 | 224239616 | 224239616 |
| bolt-d3-p0.35-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.1-n240-left | step | 1 | ok | ok: 1 | 11.711 | 11.711 | 0.420 | 0.420 | 14633958 | 14633958 | 422748160 | 422748160 |
| bolt-d10-p3-n3-left | stl-preview | 1 | ok | ok: 1 | 0.550 | 0.550 | 0.024 | 0.024 | 243184 | 243184 | 213004288 | 213004288 |
| bolt-d30-p0.35-n30-right | stl-fine | 1 | ok | ok: 1 | 2.338 | 2.338 | 12.088 | 12.088 | 103579084 | 103579084 | 1013551104 | 1013551104 |
| bolt-d30-p3-n30-left | step | 1 | ok | ok: 1 | 1.560 | 1.560 | 0.059 | 0.059 | 2049442 | 2049442 | 230264832 | 230264832 |
| bolt-d100-p0.1-n240-left | stl-preview | 1 | ok | ok: 1 | 13.749 | 13.749 | 23.377 | 23.377 | 261956884 | 261956884 | 992321536 | 992321536 |
| bolt-d100-p3-n3-right | stl-fine | 1 | ok | ok: 1 | 0.869 | 0.869 | 6.510 | 6.510 | 18156884 | 18156884 | 1523499008 | 1523499008 |
| bolt-d300-p0.1-n3-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n30-left | stl-preview | 1 | ok | ok: 1 | 2.244 | 2.244 | 20.230 | 20.230 | 124613084 | 124613084 | 1143123968 | 1143123968 |
| bolt-d300-p10-n240-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.35-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n3-left | stl-preview | 1 | ok | ok: 1 | 1.311 | 1.311 | 12.513 | 12.513 | 31652784 | 31652784 | 2486272000 | 2486272000 |
| nut-d10-p0.35-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 3.415 | 3.415 | 3.050 | 3.050 | 25562484 | 25562484 | 500883456 | 500883456 |
| nut-d10-p3.5-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 0.945 | 0.945 | 0.018 | 0.018 | 501312 | 501312 | 212221952 | 212221952 |
| nut-d30-p1-m3d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 7.034 | 7.034 | 2.594 | 2.594 | 32037184 | 32037184 | 450641920 | 450641920 |
| nut-d100-p0.35-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 20.573 | 20.573 | 326.297 | 326.297 | 1228749484 | 1228749484 | 5013757952 | 5013757952 |
| nut-d100-p3.5-m3d-s4d-c5-right | step | 1 | ok | ok: 1 | 8.111 | 8.111 | 0.202 | 0.202 | 6379570 | 6379570 | 261300224 | 261300224 |
| nut-d30-p3.5-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 1.799 | 1.799 | 0.133 | 0.133 | 1403984 | 1403984 | 231993344 | 231993344 |
| iso4017:M2.5x8 | step | 1 | ok | ok: 1 | 1.272 | 1.272 | 0.031 | 0.031 | 1035954 | 1035954 | 215347200 | 215347200 |
| iso4017:M3.5x8 | stl-preview | 1 | ok | ok: 1 | 0.892 | 0.892 | 0.058 | 0.058 | 624584 | 624584 | 215625728 | 215625728 |
| iso4017:M4x25 | stl-fine | 1 | ok | ok: 1 | 1.620 | 1.620 | 1.901 | 1.901 | 16959284 | 16959284 | 328167424 | 328167424 |
| iso4017:M5x50 | step | 1 | ok | ok: 1 | 2.586 | 2.586 | 0.099 | 0.099 | 3835801 | 3835801 | 247775232 | 247775232 |
| iso4017:M7x25 | stl-preview | 1 | ok | ok: 1 | 1.406 | 1.406 | 0.154 | 0.154 | 2090284 | 2090284 | 230993920 | 230993920 |
| iso4017:M8x30 | stl-fine | 1 | ok | ok: 1 | 1.370 | 1.370 | 2.323 | 2.323 | 20378584 | 20378584 | 383225856 | 383225856 |
| iso4017:M10x35 | step | 1 | ok | ok: 1 | 1.355 | 1.355 | 0.042 | 0.042 | 1412673 | 1412673 | 228220928 | 228220928 |
| iso4017:M12x40 | stl-preview | 1 | ok | ok: 1 | 1.397 | 1.397 | 0.172 | 0.172 | 2278384 | 2278384 | 231649280 | 231649280 |
| iso4017:M14x35 | stl-fine | 1 | ok | ok: 1 | 1.171 | 1.171 | 3.366 | 3.366 | 28765784 | 28765784 | 582676480 | 582676480 |
| iso4017:M14x130 | step | 1 | ok | ok: 1 | 2.801 | 2.801 | 0.111 | 0.111 | 4111915 | 4111915 | 275230720 | 275230720 |
| iso4017:M16x110 | stl-preview | 1 | ok | ok: 1 | 2.508 | 2.508 | 0.749 | 0.749 | 9061284 | 9061284 | 270151680 | 270151680 |
| iso4017:M18x70 | stl-fine | 1 | ok | ok: 1 | 1.573 | 1.573 | 5.278 | 5.278 | 49319884 | 49319884 | 624820224 | 624820224 |
| iso4017:M20x50 | step | 1 | ok | ok: 1 | 1.282 | 1.282 | 0.039 | 0.039 | 1397830 | 1397830 | 225857536 | 225857536 |
| iso4017:M20x180 | stl-preview | 1 | ok | ok: 1 | 2.988 | 2.988 | 1.356 | 1.356 | 20646884 | 20646884 | 314736640 | 314736640 |
| iso4014:M3.5x35 | stl-fine | 1 | ok | ok: 1 | 1.465 | 1.465 | 1.041 | 1.041 | 9105084 | 9105084 | 316121088 | 316121088 |
| iso4014:M6x40 | step | 1 | ok | ok: 1 | 1.428 | 1.428 | 0.033 | 0.033 | 1211679 | 1211679 | 220336128 | 220336128 |
| iso4014:M8x45 | stl-preview | 1 | ok | ok: 1 | 1.528 | 1.528 | 0.115 | 0.115 | 1541284 | 1541284 | 224358400 | 224358400 |
| iso4014:M10x80 | stl-fine | 1 | ok | ok: 1 | 1.391 | 1.391 | 2.196 | 2.196 | 21537884 | 21537884 | 463286272 | 463286272 |
| iso4014:M14x55 | step | 1 | ok | ok: 1 | 1.571 | 1.571 | 0.034 | 0.034 | 1203770 | 1203770 | 225300480 | 225300480 |
| iso4014:M16x90 | stl-preview | 1 | ok | ok: 1 | 1.545 | 1.545 | 0.257 | 0.257 | 3143384 | 3143384 | 232534016 | 232534016 |
| iso4014:M18x120 | stl-fine | 1 | ok | ok: 1 | 1.464 | 1.464 | 3.151 | 3.151 | 29404684 | 29404684 | 557711360 | 557711360 |
| iso4014:M20x150 | step | 1 | ok | ok: 1 | 1.771 | 1.771 | 0.041 | 0.041 | 1465970 | 1465970 | 224526336 | 224526336 |
| iso4032:M14 | stl-preview | 1 | ok | ok: 1 | 1.531 | 1.531 | 0.050 | 0.050 | 599284 | 599284 | 218968064 | 218968064 |
| bolt-d1-p0.35-n30-left | stl-fine | 1 | ok | ok: 1 | 2.108 | 2.108 | 0.863 | 0.863 | 8338784 | 8338784 | 269107200 | 269107200 |
| bolt-d3-p0.35-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.35-n3-right | stl-preview | 1 | ok | ok: 1 | 0.823 | 0.823 | 0.031 | 0.031 | 273584 | 273584 | 213327872 | 213327872 |
| bolt-d10-p3-n3-left | stl-fine | 1 | ok | ok: 1 | 0.541 | 0.541 | 0.376 | 0.376 | 2676384 | 2676384 | 320167936 | 320167936 |
| bolt-d30-p0.35-n30-right | step | 1 | ok | ok: 1 | 2.311 | 2.311 | 0.061 | 0.061 | 2078518 | 2078518 | 240316416 | 240316416 |
| bolt-d30-p3-n240-right | stl-preview | 1 | ok | ok: 1 | 6.801 | 6.801 | 5.667 | 5.667 | 78161484 | 78161484 | 576847872 | 576847872 |
| bolt-d100-p0.1-n240-left | stl-fine | 1 | ok | ok: 1 | 13.356 | 13.356 | 478.919 | 478.919 | 2099449084 | 2099449084 | 8360972288 | 8360972288 |
| bolt-d100-p3-n3-right | step | 1 | ok | ok: 1 | 0.885 | 0.885 | 0.016 | 0.016 | 418530 | 418530 | 210976768 | 210976768 |
| bolt-d300-p0.1-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n30-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n240-right | step | 1 | ok | ok: 1 | 7.471 | 7.471 | 0.608 | 0.608 | 21116341 | 21116341 | 479903744 | 479903744 |
| bolt-d1000-p1-n3-right | stl-preview | 1 | ok | ok: 1 | 3.439 | 3.439 | 13.342 | 13.342 | 41419384 | 41419384 | 2822721536 | 2822721536 |
| bolt-d1000-p10-n3-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d10-p0.35-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 3.294 | 3.294 | 0.044 | 0.044 | 1718630 | 1718630 | 223866880 | 223866880 |
| nut-d10-p3.5-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 0.628 | 0.628 | 0.066 | 0.066 | 665784 | 665784 | 221499392 | 221499392 |
| nut-d30-p1-m3d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 6.912 | 6.912 | 72.821 | 72.821 | 498369284 | 498369284 | 2276937728 | 2276937728 |
| nut-d100-p0.35-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 20.506 | 20.506 | 0.397 | 0.397 | 13269658 | 13269658 | 334782464 | 334782464 |
| nut-d3-p0.35-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 1.870 | 1.870 | 0.029 | 0.029 | 273084 | 273084 | 218177536 | 218177536 |
| nut-d30-p3.5-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 1.771 | 1.771 | 1.939 | 1.939 | 13224984 | 13224984 | 553500672 | 553500672 |
| iso4017:M2.5x10 | stl-preview | 1 | ok | ok: 1 | 1.953 | 1.953 | 0.100 | 0.100 | 919784 | 919784 | 219267072 | 219267072 |
| iso4017:M3.5x8 | stl-fine | 1 | ok | ok: 1 | 1.143 | 1.143 | 0.916 | 0.916 | 5371884 | 5371884 | 305602560 | 305602560 |
| iso4017:M4x25 | step | 1 | ok | ok: 1 | 2.087 | 2.087 | 0.074 | 0.074 | 2241104 | 2241104 | 229019648 | 229019648 |
| iso4017:M6x12 | stl-preview | 1 | ok | ok: 1 | 1.275 | 1.275 | 0.097 | 0.097 | 966384 | 966384 | 219987968 | 219987968 |
| iso4017:M7x25 | stl-fine | 1 | ok | ok: 1 | 1.777 | 1.777 | 2.125 | 2.125 | 13482984 | 13482984 | 338804736 | 338804736 |
| iso4017:M8x30 | step | 1 | ok | ok: 1 | 1.755 | 1.755 | 0.052 | 0.052 | 1578935 | 1578935 | 225607680 | 225607680 |
| iso4017:M10x40 | stl-preview | 1 | ok | ok: 1 | 1.835 | 1.835 | 0.247 | 0.247 | 2419384 | 2419384 | 231292928 | 231292928 |
| iso4017:M12x40 | stl-fine | 1 | ok | ok: 1 | 1.768 | 1.768 | 4.637 | 4.637 | 31058484 | 31058484 | 546750464 | 546750464 |
| iso4017:M14x35 | step | 1 | ok | ok: 1 | 1.543 | 1.543 | 0.041 | 0.041 | 1230797 | 1230797 | 222625792 | 222625792 |
| iso4017:M14x140 | stl-preview | 1 | ok | ok: 1 | 3.696 | 3.696 | 0.802 | 0.802 | 7175484 | 7175484 | 284262400 | 284262400 |
| iso4017:M16x110 | stl-fine | 1 | ok | ok: 1 | 3.182 | 3.182 | 13.420 | 13.420 | 95742484 | 95742484 | 788594688 | 788594688 |
| iso4017:M18x70 | step | 1 | ok | ok: 1 | 1.964 | 1.964 | 0.059 | 0.059 | 1900718 | 1900718 | 233717760 | 233717760 |
| iso4017:M20x55 | stl-preview | 1 | ok | ok: 1 | 1.692 | 1.692 | 0.552 | 0.552 | 6267784 | 6267784 | 244211712 | 244211712 |
| iso4017:M20x180 | stl-fine | 1 | ok | ok: 1 | 3.880 | 3.880 | 16.861 | 16.861 | 128770484 | 128770484 | 879579136 | 879579136 |
| iso4014:M3.5x35 | step | 1 | ok | ok: 1 | 1.856 | 1.856 | 0.044 | 0.044 | 1291471 | 1291471 | 218009600 | 218009600 |
| iso4014:M6x45 | stl-preview | 1 | ok | ok: 1 | 1.874 | 1.874 | 0.139 | 0.139 | 1476484 | 1476484 | 223494144 | 223494144 |
| iso4014:M8x45 | stl-fine | 1 | ok | ok: 1 | 1.986 | 1.986 | 2.073 | 2.073 | 14707484 | 14707484 | 386342912 | 386342912 |
| iso4014:M10x80 | step | 1 | ok | ok: 1 | 1.810 | 1.810 | 0.037 | 0.037 | 1096224 | 1096224 | 222134272 | 222134272 |
| iso4014:M14x60 | stl-preview | 1 | ok | ok: 1 | 1.964 | 1.964 | 0.200 | 0.200 | 1835884 | 1835884 | 226836480 | 226836480 |
| iso4014:M16x90 | stl-fine | 1 | ok | ok: 1 | 1.948 | 1.948 | 4.799 | 4.799 | 33383384 | 33383384 | 606240768 | 606240768 |
| iso4014:M18x120 | step | 1 | ok | ok: 1 | 1.886 | 1.886 | 0.040 | 0.040 | 1195983 | 1195983 | 223236096 | 223236096 |
| iso4014:M20x160 | stl-preview | 1 | ok | ok: 1 | 2.235 | 2.235 | 0.532 | 0.532 | 6015484 | 6015484 | 239517696 | 239517696 |
| iso4032:M14 | stl-fine | 1 | ok | ok: 1 | 1.955 | 1.955 | 1.292 | 1.292 | 8530284 | 8530284 | 418361344 | 418361344 |
| bolt-d1-p0.35-n30-left | step | 1 | ok | ok: 1 | 2.614 | 2.614 | 0.052 | 0.052 | 1631730 | 1631730 | 223932416 | 223932416 |
| bolt-d3-p0.35-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.35-n3-right | stl-fine | 1 | ok | ok: 1 | 0.996 | 0.996 | 0.652 | 0.652 | 3896884 | 3896884 | 373698560 | 373698560 |
| bolt-d10-p3-n3-left | step | 1 | ok | ok: 1 | 0.686 | 0.686 | 0.014 | 0.014 | 307487 | 307487 | 210735104 | 210735104 |
| bolt-d30-p0.35-n30-left | stl-preview | 1 | ok | ok: 1 | 2.873 | 2.873 | 0.824 | 0.824 | 7651484 | 7651484 | 266096640 | 266096640 |
| bolt-d30-p3-n240-right | stl-fine | 1 | ok | ok: 1 | 8.739 | 8.739 | 99.267 | 99.267 | 708231184 | 708231184 | 2554187776 | 2554187776 |
| bolt-d100-p0.1-n240-left | step | 1 | ok | ok: 1 | 16.980 | 16.980 | 0.546 | 0.546 | 16580188 | 16580188 | 424681472 | 424681472 |
| bolt-d100-p3-n3-left | stl-preview | 1 | ok | ok: 1 | 1.089 | 1.089 | 0.488 | 0.488 | 2927184 | 2927184 | 310960128 | 310960128 |
| bolt-d300-p0.1-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n30-left | step | 1 | ok | ok: 1 | 2.802 | 2.802 | 0.091 | 0.091 | 2805052 | 2805052 | 242524160 | 242524160 |
| bolt-d300-p10-n240-left | stl-preview | 1 | ok | ok: 1 | 9.450 | 9.450 | 148.560 | 148.560 | 877650384 | 877650384 | 3121176576 | 3121176576 |
| bolt-d1000-p1-n3-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n3-left | step | 1 | ok | ok: 1 | 1.651 | 1.651 | 0.024 | 0.024 | 641360 | 641360 | 217448448 | 217448448 |
| nut-d10-p0.35-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 3.854 | 3.854 | 0.179 | 0.179 | 1785284 | 1785284 | 229769216 | 229769216 |
| nut-d10-p3.5-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 0.823 | 0.823 | 0.760 | 0.760 | 5175184 | 5175184 | 369446912 | 369446912 |
| nut-d30-p1-m3d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 8.932 | 8.932 | 0.211 | 0.211 | 6059237 | 6059237 | 431927296 | 431927296 |
| nut-d100-p0.35-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 28.074 | 28.074 | 30.462 | 30.462 | 281708284 | 281708284 | 1030283264 | 1030283264 |
| nut-d3-p0.35-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 2.319 | 2.319 | 0.364 | 0.364 | 2186884 | 2186884 | 283283456 | 283283456 |
| nut-d30-p3.5-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 2.209 | 2.209 | 0.032 | 0.032 | 911576 | 911576 | 213700608 | 213700608 |
| iso4017:M2.5x10 | stl-fine | 1 | ok | ok: 1 | 2.434 | 2.434 | 1.578 | 1.578 | 8334484 | 8334484 | 298467328 | 298467328 |
| iso4017:M3.5x8 | step | 1 | ok | ok: 1 | 1.431 | 1.431 | 0.039 | 0.039 | 834287 | 834287 | 214687744 | 214687744 |
| iso4017:M4x30 | stl-preview | 1 | ok | ok: 1 | 2.811 | 2.811 | 0.351 | 0.351 | 2228384 | 2228384 | 239890432 | 239890432 |
| iso4017:M6x12 | stl-fine | 1 | ok | ok: 1 | 1.600 | 1.600 | 1.171 | 1.171 | 6094584 | 6094584 | 316108800 | 316108800 |
| iso4017:M7x25 | step | 1 | ok | ok: 1 | 2.188 | 2.188 | 0.069 | 0.069 | 1639088 | 1639088 | 228765696 | 228765696 |
| iso4017:M8x35 | stl-preview | 1 | ok | ok: 1 | 2.342 | 2.342 | 0.314 | 0.314 | 2374284 | 2374284 | 232894464 | 232894464 |
| iso4017:M10x40 | stl-fine | 1 | ok | ok: 1 | 2.286 | 2.286 | 5.540 | 5.540 | 32961784 | 32961784 | 508997632 | 508997632 |
| iso4017:M12x40 | step | 1 | ok | ok: 1 | 2.202 | 2.202 | 0.066 | 0.066 | 1520194 | 1520194 | 227672064 | 227672064 |
| iso4017:M14x40 | stl-preview | 1 | ok | ok: 1 | 1.996 | 1.996 | 0.317 | 0.317 | 2105484 | 2105484 | 230162432 | 230162432 |
| iso4017:M14x140 | stl-fine | 1 | ok | ok: 1 | 4.601 | 4.601 | 19.583 | 19.583 | 116206284 | 116206284 | 790929408 | 790929408 |
| iso4017:M16x110 | step | 1 | ok | ok: 1 | 3.913 | 3.913 | 0.144 | 0.144 | 3553421 | 3553421 | 265736192 | 265736192 |
| iso4017:M18x80 | stl-preview | 1 | ok | ok: 1 | 2.692 | 2.692 | 1.135 | 1.135 | 7991484 | 7991484 | 258097152 | 258097152 |
| iso4017:M20x55 | stl-fine | 1 | ok | ok: 1 | 2.105 | 2.105 | 7.174 | 7.174 | 39304184 | 39304184 | 627671040 | 627671040 |
| iso4017:M20x180 | step | 1 | ok | ok: 1 | 4.766 | 4.766 | 0.188 | 0.188 | 4587268 | 4587268 | 286760960 | 286760960 |
| iso4014:M4x25 | stl-preview | 1 | ok | ok: 1 | 2.320 | 2.320 | 0.150 | 0.150 | 1074884 | 1074884 | 219627520 | 219627520 |
| iso4014:M6x45 | stl-fine | 1 | ok | ok: 1 | 2.327 | 2.327 | 1.792 | 1.792 | 9559584 | 9559584 | 353910784 | 353910784 |
| iso4014:M8x45 | step | 1 | ok | ok: 1 | 2.471 | 2.471 | 0.053 | 0.053 | 1209363 | 1209363 | 221831168 | 221831168 |
| iso4014:M10x90 | stl-preview | 1 | ok | ok: 1 | 2.243 | 2.243 | 0.215 | 0.215 | 1621384 | 1621384 | 224231424 | 224231424 |
| iso4014:M14x60 | stl-fine | 1 | ok | ok: 1 | 2.429 | 2.429 | 4.926 | 4.926 | 27923284 | 27923284 | 611889152 | 611889152 |
| iso4014:M16x90 | step | 1 | ok | ok: 1 | 2.420 | 2.420 | 0.058 | 0.058 | 1352632 | 1352632 | 224595968 | 224595968 |
| iso4014:M18x130 | stl-preview | 1 | ok | ok: 1 | 2.489 | 2.489 | 0.686 | 0.686 | 4787684 | 4787684 | 255250432 | 255250432 |
| iso4014:M20x160 | stl-fine | 1 | ok | ok: 1 | 2.819 | 2.819 | 6.367 | 6.367 | 37736784 | 37736784 | 560623616 | 560623616 |
| iso4032:M14 | step | 1 | ok | ok: 1 | 2.461 | 2.461 | 0.038 | 0.038 | 826280 | 826280 | 213954560 | 213954560 |
| bolt-d1-p0.35-n240-right | stl-preview | 1 | ok | ok: 1 | 25.854 | 25.854 | 1.188 | 1.188 | 10639384 | 10639384 | 334733312 | 334733312 |
| bolt-d3-p0.35-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.35-n3-right | step | 1 | ok | ok: 1 | 1.251 | 1.251 | 0.021 | 0.021 | 378918 | 378918 | 210407424 | 210407424 |
| bolt-d10-p3-n30-right | stl-preview | 1 | ok | ok: 1 | 2.265 | 2.265 | 0.414 | 0.414 | 3226384 | 3226384 | 231550976 | 231550976 |
| bolt-d30-p0.35-n30-left | stl-fine | 1 | ok | ok: 1 | 3.564 | 3.564 | 15.820 | 15.820 | 85119584 | 85119584 | 953446400 | 953446400 |
| bolt-d30-p3-n240-right | step | 1 | ok | ok: 1 | 10.809 | 10.809 | 0.659 | 0.659 | 15202211 | 15202211 | 443842560 | 443842560 |
| bolt-d100-p0.35-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n3-left | stl-fine | 1 | ok | ok: 1 | 1.355 | 1.355 | 6.116 | 6.116 | 14978584 | 14978584 | 1507880960 | 1507880960 |
| bolt-d300-p0.1-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n240-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n3-right | step | 1 | ok | ok: 1 | 5.946 | 5.946 | 0.049 | 0.049 | 1121379 | 1121379 | 229130240 | 229130240 |
| bolt-d1000-p10-n30-right | stl-preview | 1 | ok | ok: 1 | 3.137 | 3.137 | 122.761 | 122.761 | 412582884 | 412582884 | 5138661376 | 5138661376 |
| nut-d10-p0.35-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 4.705 | 4.705 | 4.675 | 4.675 | 25588884 | 25588884 | 485548032 | 485548032 |
| nut-d10-p3.5-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 1.044 | 1.044 | 0.025 | 0.025 | 469677 | 469677 | 212983808 | 212983808 |
| nut-d30-p1-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 11.876 | 11.876 | 3.497 | 3.497 | 27966884 | 27966884 | 322355200 | 322355200 |
| nut-d100-p0.35-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 34.058 | 34.058 | 475.667 | 475.667 | 1475853984 | 1475853984 | 5755568128 | 5755568128 |
| nut-d3-p0.35-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 2.920 | 2.920 | 0.038 | 0.038 | 737028 | 737028 | 223420416 | 223420416 |
| nut-d30-p3.5-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 4.476 | 4.476 | 0.763 | 0.763 | 6111884 | 6111884 | 244133888 | 244133888 |
| iso4017:M2.5x10 | step | 1 | ok | ok: 1 | 2.426 | 2.426 | 0.057 | 0.057 | 1261976 | 1261976 | 218521600 | 218521600 |
| iso4017:M3.5x10 | stl-preview | 1 | ok | ok: 1 | 1.764 | 1.764 | 0.123 | 0.123 | 775984 | 775984 | 217260032 | 217260032 |
| iso4017:M4x30 | stl-fine | 1 | ok | ok: 1 | 2.801 | 2.801 | 3.720 | 3.720 | 20305384 | 20305384 | 336326656 | 336326656 |
| iso4017:M6x12 | step | 1 | ok | ok: 1 | 1.588 | 1.588 | 0.038 | 0.038 | 844796 | 844796 | 216866816 | 216866816 |
| iso4017:M7x30 | stl-preview | 1 | ok | ok: 1 | 2.517 | 2.517 | 0.309 | 0.309 | 2509284 | 2509284 | 231288832 | 231288832 |
| iso4017:M8x35 | stl-fine | 1 | ok | ok: 1 | 2.337 | 2.337 | 4.178 | 4.178 | 23915484 | 23915484 | 385822720 | 385822720 |
| iso4017:M10x40 | step | 1 | ok | ok: 1 | 2.284 | 2.284 | 0.070 | 0.070 | 1626010 | 1626010 | 225050624 | 225050624 |
| iso4017:M12x45 | stl-preview | 1 | ok | ok: 1 | 2.229 | 2.229 | 0.350 | 0.350 | 2522184 | 2522184 | 231530496 | 231530496 |
| iso4017:M14x40 | stl-fine | 1 | ok | ok: 1 | 2.011 | 2.011 | 6.146 | 6.146 | 32490484 | 32490484 | 613015552 | 613015552 |
| iso4017:M14x140 | step | 1 | ok | ok: 1 | 4.573 | 4.573 | 0.180 | 0.180 | 4424256 | 4424256 | 284221440 | 284221440 |
| iso4017:M16x120 | stl-preview | 1 | ok | ok: 1 | 4.248 | 4.248 | 1.424 | 1.424 | 9895984 | 9895984 | 265003008 | 265003008 |
| iso4017:M18x80 | stl-fine | 1 | ok | ok: 1 | 2.712 | 2.712 | 9.890 | 9.890 | 56413184 | 56413184 | 620453888 | 620453888 |
| iso4017:M20x55 | step | 1 | ok | ok: 1 | 2.100 | 2.100 | 0.068 | 0.068 | 1531497 | 1531497 | 227655680 | 227655680 |
| iso4017:M20x200 | stl-preview | 1 | ok | ok: 1 | 5.208 | 5.208 | 2.505 | 2.505 | 22807184 | 22807184 | 325459968 | 325459968 |
| iso4014:M4x25 | stl-fine | 1 | ok | ok: 1 | 2.326 | 2.326 | 1.861 | 1.861 | 9752984 | 9752984 | 335155200 | 335155200 |
| iso4014:M6x45 | step | 1 | ok | ok: 1 | 2.348 | 2.348 | 0.053 | 0.053 | 1211679 | 1211679 | 220372992 | 220372992 |
| iso4014:M8x50 | stl-preview | 1 | ok | ok: 1 | 2.478 | 2.478 | 0.203 | 0.203 | 1541284 | 1541284 | 223129600 | 223129600 |
| iso4014:M10x90 | stl-fine | 1 | ok | ok: 1 | 2.258 | 2.258 | 3.711 | 3.711 | 21537884 | 21537884 | 468901888 | 468901888 |
| iso4014:M14x60 | step | 1 | ok | ok: 1 | 2.438 | 2.438 | 0.053 | 0.053 | 1203648 | 1203648 | 222752768 | 222752768 |
| iso4014:M16x100 | stl-preview | 1 | ok | ok: 1 | 2.437 | 2.437 | 0.571 | 0.571 | 3143384 | 3143384 | 237780992 | 237780992 |
| iso4014:M18x130 | stl-fine | 1 | ok | ok: 1 | 2.487 | 2.487 | 5.912 | 5.912 | 34477384 | 34477384 | 567857152 | 567857152 |
| iso4014:M20x160 | step | 1 | ok | ok: 1 | 2.838 | 2.838 | 0.065 | 0.065 | 1465962 | 1465962 | 225718272 | 225718272 |
| iso4032:M16 | stl-preview | 1 | ok | ok: 1 | 2.756 | 2.756 | 0.193 | 0.193 | 1070084 | 1070084 | 228470784 | 228470784 |
| bolt-d1-p0.35-n240-right | stl-fine | 1 | ok | ok: 1 | 25.897 | 25.897 | 12.195 | 12.195 | 73314084 | 73314084 | 507490304 | 507490304 |
| bolt-d3-p0.35-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.35-n3-left | stl-preview | 1 | ok | ok: 1 | 1.149 | 1.149 | 0.038 | 0.038 | 232984 | 232984 | 212393984 | 212393984 |
| bolt-d10-p3-n30-right | stl-fine | 1 | ok | ok: 1 | 2.239 | 2.239 | 5.634 | 5.634 | 34545384 | 34545384 | 448729088 | 448729088 |
| bolt-d30-p0.35-n30-left | step | 1 | ok | ok: 1 | 3.575 | 3.575 | 0.092 | 0.092 | 2077851 | 2077851 | 250097664 | 250097664 |
| bolt-d30-p3-n240-left | stl-preview | 1 | ok | ok: 1 | 10.879 | 10.879 | 7.443 | 7.443 | 60000784 | 60000784 | 533475328 | 533475328 |
| bolt-d100-p0.35-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n3-left | step | 1 | ok | ok: 1 | 1.346 | 1.346 | 0.023 | 0.023 | 418487 | 418487 | 210464768 | 210464768 |
| bolt-d300-p0.1-n30-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p10-n240-left | step | 1 | ok | ok: 1 | 11.793 | 11.793 | 0.921 | 0.921 | 21111281 | 21111281 | 519372800 | 519372800 |
| bolt-d1000-p1-n3-left | stl-preview | 1 | ok | ok: 1 | 4.974 | 4.974 | 13.762 | 13.762 | 34702684 | 34702684 | 2794385408 | 2794385408 |
| bolt-d1000-p10-n30-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d10-p0.35-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 4.727 | 4.727 | 0.074 | 0.074 | 1719114 | 1719114 | 232759296 | 232759296 |
| nut-d10-p3.5-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 2.432 | 2.432 | 0.123 | 0.123 | 850884 | 850884 | 218157056 | 218157056 |
| nut-d30-p1-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 11.959 | 11.959 | 45.346 | 45.346 | 238075584 | 238075584 | 1309753344 | 1309753344 |
| nut-d100-p0.35-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 34.180 | 34.180 | 0.705 | 0.705 | 15019212 | 15019212 | 343150592 | 343150592 |
| nut-d3-p0.35-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 6.461 | 6.461 | 0.154 | 0.154 | 1020784 | 1020784 | 256454656 | 256454656 |
| nut-d30-p3.5-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 4.508 | 4.508 | 11.661 | 11.661 | 57905484 | 57905484 | 834445312 | 834445312 |
| iso4017:M2.5x12 | stl-preview | 1 | ok | ok: 1 | 2.844 | 2.844 | 0.185 | 0.185 | 1113684 | 1113684 | 228159488 | 228159488 |
| iso4017:M3.5x10 | stl-fine | 1 | ok | ok: 1 | 1.872 | 1.872 | 1.398 | 1.398 | 6570384 | 6570384 | 313225216 | 313225216 |
| iso4017:M4x30 | step | 1 | ok | ok: 1 | 2.822 | 2.822 | 0.113 | 0.113 | 2687149 | 2687149 | 234770432 | 234770432 |
| iso4017:M6x16 | stl-preview | 1 | ok | ok: 1 | 1.713 | 1.713 | 0.170 | 0.170 | 1287684 | 1287684 | 222982144 | 222982144 |
| iso4017:M7x30 | stl-fine | 1 | ok | ok: 1 | 2.516 | 2.516 | 3.020 | 3.020 | 15872084 | 15872084 | 329957376 | 329957376 |
| iso4017:M8x35 | step | 1 | ok | ok: 1 | 2.336 | 2.336 | 0.075 | 0.075 | 1825355 | 1825355 | 231985152 | 231985152 |
| iso4017:M10x45 | stl-preview | 1 | ok | ok: 1 | 2.487 | 2.487 | 0.353 | 0.353 | 2698584 | 2698584 | 233955328 | 233955328 |
| iso4017:M12x45 | stl-fine | 1 | ok | ok: 1 | 2.236 | 2.236 | 5.929 | 5.929 | 35070584 | 35070584 | 518303744 | 518303744 |
| iso4017:M14x40 | step | 1 | ok | ok: 1 | 2.021 | 2.021 | 0.058 | 0.058 | 1377972 | 1377972 | 223453184 | 223453184 |
| iso4017:M16x30 | stl-preview | 1 | ok | ok: 1 | 1.870 | 1.870 | 0.380 | 0.380 | 2450084 | 2450084 | 226234368 | 226234368 |
| iso4017:M16x120 | stl-fine | 1 | ok | ok: 1 | 4.259 | 4.259 | 17.673 | 17.673 | 104335984 | 104335984 | 752635904 | 752635904 |
| iso4017:M18x80 | step | 1 | ok | ok: 1 | 2.704 | 2.704 | 0.089 | 0.089 | 2136517 | 2136517 | 237404160 | 237404160 |
| iso4017:M20x60 | stl-preview | 1 | ok | ok: 1 | 2.267 | 2.267 | 0.807 | 0.807 | 6839184 | 6839184 | 252805120 | 252805120 |
| iso4017:M20x200 | stl-fine | 1 | ok | ok: 1 | 5.199 | 5.199 | 23.347 | 23.347 | 144651784 | 144651784 | 867192832 | 867192832 |
| iso4014:M4x25 | step | 1 | ok | ok: 1 | 2.319 | 2.319 | 0.057 | 0.057 | 1298275 | 1298275 | 218501120 | 218501120 |
| iso4014:M6x50 | stl-preview | 1 | ok | ok: 1 | 2.332 | 2.332 | 0.181 | 0.181 | 1476484 | 1476484 | 222760960 | 222760960 |
| iso4014:M8x50 | stl-fine | 1 | ok | ok: 1 | 2.455 | 2.455 | 2.628 | 2.628 | 14707484 | 14707484 | 375259136 | 375259136 |
| iso4014:M10x90 | step | 1 | ok | ok: 1 | 2.243 | 2.243 | 0.050 | 0.050 | 1096224 | 1096224 | 221347840 | 221347840 |
| iso4014:M14x65 | stl-preview | 1 | ok | ok: 1 | 2.446 | 2.446 | 0.263 | 0.263 | 1835884 | 1835884 | 226164736 | 226164736 |
| iso4014:M16x100 | stl-fine | 1 | ok | ok: 1 | 2.416 | 2.416 | 5.844 | 5.844 | 33383384 | 33383384 | 600596480 | 600596480 |
| iso4014:M18x130 | step | 1 | ok | ok: 1 | 2.481 | 2.481 | 0.060 | 0.060 | 1368891 | 1368891 | 225337344 | 225337344 |
| iso4014:M20x180 | stl-preview | 1 | ok | ok: 1 | 2.787 | 2.787 | 0.801 | 0.801 | 6015484 | 6015484 | 250687488 | 250687488 |
| iso4032:M16 | stl-fine | 1 | ok | ok: 1 | 2.818 | 2.818 | 2.148 | 2.148 | 10511584 | 10511584 | 447074304 | 447074304 |
| bolt-d1-p0.35-n240-right | step | 1 | ok | ok: 1 | 25.828 | 25.828 | 0.567 | 0.567 | 12611145 | 12611145 | 357249024 | 357249024 |
| bolt-d3-p1-n3-right | stl-preview | 1 | ok | ok: 1 | 0.843 | 0.843 | 0.023 | 0.023 | 131884 | 131884 | 210149376 | 210149376 |
| bolt-d10-p0.35-n3-left | stl-fine | 1 | ok | ok: 1 | 1.151 | 1.151 | 0.630 | 0.630 | 3093484 | 3093484 | 362565632 | 362565632 |
| bolt-d10-p3-n30-right | step | 1 | ok | ok: 1 | 2.241 | 2.241 | 0.077 | 0.077 | 1775152 | 1775152 | 229883904 | 229883904 |
| bolt-d30-p0.35-n240-right | stl-preview | 1 | ok | ok: 1 | 14.358 | 14.358 | 9.464 | 9.464 | 78306684 | 78306684 | 563490816 | 563490816 |
| bolt-d30-p3-n240-left | stl-fine | 1 | ok | ok: 1 | 10.826 | 10.826 | 91.242 | 91.242 | 529283384 | 529283384 | 2009796608 | 2009796608 |
| bolt-d100-p0.35-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n30-right | stl-preview | 1 | ok | ok: 1 | 3.004 | 3.004 | 5.622 | 5.622 | 39583984 | 39583984 | 447750144 | 447750144 |
| bolt-d300-p0.1-n30-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.1-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n3-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n30-right | step | 1 | ok | ok: 1 | 3.128 | 3.128 | 0.166 | 0.166 | 3811807 | 3811807 | 251949056 | 251949056 |
| nut-d10-p0.35-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 3.215 | 3.215 | 0.897 | 0.897 | 7251784 | 7251784 | 240566272 | 240566272 |
| nut-d10-p3.5-m3d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 2.420 | 2.420 | 1.760 | 1.760 | 9371084 | 9371084 | 398692352 | 398692352 |
| nut-d30-p1-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 11.876 | 11.876 | 0.254 | 0.254 | 5848272 | 5848272 | 258125824 | 258125824 |
| nut-d100-p1-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 12.999 | 12.999 | 11.654 | 11.654 | 84465884 | 84465884 | 585998336 | 585998336 |
| nut-d3-p0.35-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 6.392 | 6.392 | 1.606 | 1.606 | 8137184 | 8137184 | 315453440 | 315453440 |
| nut-d30-p3.5-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 4.478 | 4.478 | 0.091 | 0.091 | 2106174 | 2106174 | 234921984 | 234921984 |
| iso4017:M2.5x12 | stl-fine | 1 | ok | ok: 1 | 1.913 | 1.913 | 1.135 | 1.135 | 10005484 | 10005484 | 300343296 | 300343296 |
| iso4017:M3.5x10 | step | 1 | ok | ok: 1 | 1.174 | 1.174 | 0.033 | 0.033 | 1014623 | 1014623 | 215355392 | 215355392 |
| iso4017:M4x35 | stl-preview | 1 | ok | ok: 1 | 2.176 | 2.176 | 0.208 | 0.208 | 2607784 | 2607784 | 235347968 | 235347968 |
| iso4017:M6x16 | stl-fine | 1 | ok | ok: 1 | 1.128 | 1.128 | 1.052 | 1.052 | 8189584 | 8189584 | 345026560 | 345026560 |
| iso4017:M7x30 | step | 1 | ok | ok: 1 | 1.756 | 1.756 | 0.055 | 0.055 | 1932826 | 1932826 | 226496512 | 226496512 |
| iso4017:M8x40 | stl-preview | 1 | ok | ok: 1 | 1.724 | 1.724 | 0.210 | 0.210 | 2686784 | 2686784 | 235499520 | 235499520 |
| iso4017:M10x45 | stl-fine | 1 | ok | ok: 1 | 1.642 | 1.642 | 4.088 | 4.088 | 37165284 | 37165284 | 517091328 | 517091328 |
| iso4017:M12x45 | step | 1 | ok | ok: 1 | 1.453 | 1.453 | 0.049 | 0.049 | 1699375 | 1699375 | 234954752 | 234954752 |
| iso4017:M14x45 | stl-preview | 1 | ok | ok: 1 | 1.406 | 1.406 | 0.209 | 0.209 | 2304384 | 2304384 | 228818944 | 228818944 |
| iso4017:M16x30 | stl-fine | 1 | ok | ok: 1 | 1.243 | 1.243 | 3.222 | 3.222 | 25847384 | 25847384 | 610041856 | 610041856 |
| iso4017:M16x120 | step | 1 | ok | ok: 1 | 2.746 | 2.746 | 0.103 | 0.103 | 3844059 | 3844059 | 257806336 | 257806336 |
| iso4017:M18x90 | stl-preview | 1 | ok | ok: 1 | 1.960 | 1.960 | 0.701 | 0.701 | 9157484 | 9157484 | 258056192 | 258056192 |
| iso4017:M20x60 | stl-fine | 1 | ok | ok: 1 | 1.487 | 1.487 | 5.010 | 5.010 | 42741384 | 42741384 | 614998016 | 614998016 |
| iso4017:M20x200 | step | 1 | ok | ok: 1 | 3.442 | 3.442 | 0.153 | 0.153 | 5080293 | 5080293 | 286380032 | 286380032 |
| iso4014:M4x30 | stl-preview | 1 | ok | ok: 1 | 1.584 | 1.584 | 0.091 | 0.091 | 1074884 | 1074884 | 219742208 | 219742208 |
| iso4014:M6x50 | stl-fine | 1 | ok | ok: 1 | 1.546 | 1.546 | 1.075 | 1.075 | 9559584 | 9559584 | 326139904 | 326139904 |
| iso4014:M8x50 | step | 1 | ok | ok: 1 | 1.652 | 1.652 | 0.035 | 0.035 | 1209363 | 1209363 | 222408704 | 222408704 |
| iso4014:M10x100 | stl-preview | 1 | ok | ok: 1 | 1.487 | 1.487 | 0.138 | 0.138 | 1621384 | 1621384 | 224595968 | 224595968 |
| iso4014:M14x65 | stl-fine | 1 | ok | ok: 1 | 1.615 | 1.615 | 3.303 | 3.303 | 27923284 | 27923284 | 610217984 | 610217984 |
| iso4014:M16x100 | step | 1 | ok | ok: 1 | 1.566 | 1.566 | 0.040 | 0.040 | 1352659 | 1352659 | 219549696 | 219549696 |
| iso4014:M18x140 | stl-preview | 1 | ok | ok: 1 | 1.629 | 1.629 | 0.389 | 0.389 | 4787684 | 4787684 | 242036736 | 242036736 |
| iso4014:M20x180 | stl-fine | 1 | ok | ok: 1 | 1.852 | 1.852 | 4.319 | 4.319 | 37736784 | 37736784 | 581144576 | 581144576 |
| iso4032:M16 | step | 1 | ok | ok: 1 | 1.800 | 1.800 | 0.029 | 0.029 | 878845 | 878845 | 214798336 | 214798336 |
| bolt-d1-p0.35-n240-left | stl-preview | 1 | ok | ok: 1 | 17.553 | 17.553 | 0.689 | 0.689 | 10640184 | 10640184 | 332066816 | 332066816 |
| bolt-d3-p1-n3-right | stl-fine | 1 | ok | ok: 1 | 0.518 | 0.518 | 0.168 | 0.168 | 1169684 | 1169684 | 266469376 | 266469376 |
| bolt-d10-p0.35-n3-left | step | 1 | ok | ok: 1 | 0.746 | 0.746 | 0.014 | 0.014 | 379076 | 379076 | 210690048 | 210690048 |
| bolt-d10-p3-n30-left | stl-preview | 1 | ok | ok: 1 | 1.484 | 1.484 | 0.190 | 0.190 | 2392684 | 2392684 | 231362560 | 231362560 |
| bolt-d30-p0.35-n240-right | stl-fine | 1 | ok | ok: 1 | 9.732 | 9.732 | 93.551 | 93.551 | 833196184 | 833196184 | 2839588864 | 2839588864 |
| bolt-d30-p3-n240-left | step | 1 | ok | ok: 1 | 7.097 | 7.097 | 0.463 | 0.463 | 15186883 | 15186883 | 450461696 | 450461696 |
| bolt-d100-p0.35-n3-left | stl-preview | 1 | ok | ok: 1 | 1.525 | 1.525 | 0.328 | 0.328 | 3015284 | 3015284 | 313020416 | 313020416 |
| bolt-d100-p3-n30-right | stl-fine | 1 | ok | ok: 1 | 1.965 | 1.965 | 46.669 | 46.669 | 183620984 | 183620984 | 2405081088 | 2405081088 |
| bolt-d300-p0.1-n30-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n240-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.1-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n3-left | step | 1 | ok | ok: 1 | 3.127 | 3.127 | 0.040 | 0.040 | 1319371 | 1319371 | 220528640 | 220528640 |
| bolt-d1000-p10-n30-left | stl-preview | 1 | ok | ok: 1 | 2.042 | 2.042 | 93.291 | 93.291 | 338964084 | 338964084 | 4665397248 | 4665397248 |
| nut-d10-p0.35-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 2.074 | 2.074 | 4.763 | 4.763 | 37718784 | 37718784 | 584314880 | 584314880 |
| nut-d10-p3.5-m3d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 1.507 | 1.507 | 0.025 | 0.025 | 862351 | 862351 | 214761472 | 214761472 |
| nut-d30-p1-m3d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 4.629 | 4.629 | 2.515 | 2.515 | 32052784 | 32052784 | 319672320 | 319672320 |
| nut-d100-p1-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 8.625 | 8.625 | 103.178 | 103.178 | 432502984 | 432502984 | 3513790464 | 3513790464 |
| nut-d3-p0.35-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 4.208 | 4.208 | 0.047 | 0.047 | 1705938 | 1705938 | 246136832 | 246136832 |
| nut-d100-p0.35-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 21.897 | 21.897 | 17.004 | 17.004 | 185360784 | 185360784 | 805400576 | 805400576 |
| iso4017:M2.5x12 | step | 1 | ok | ok: 1 | 2.886 | 2.886 | 0.065 | 0.065 | 1485509 | 1485509 | 231792640 | 231792640 |
| iso4017:M3.5x12 | stl-preview | 1 | ok | ok: 1 | 1.857 | 1.857 | 0.149 | 0.149 | 947584 | 947584 | 218714112 | 218714112 |
| iso4017:M4x35 | stl-fine | 1 | ok | ok: 1 | 3.304 | 3.304 | 4.413 | 4.413 | 23490884 | 23490884 | 339537920 | 339537920 |
| iso4017:M6x16 | step | 1 | ok | ok: 1 | 1.725 | 1.725 | 0.048 | 0.048 | 1086066 | 1086066 | 222441472 | 222441472 |
| iso4017:M7x35 | stl-preview | 1 | ok | ok: 1 | 2.851 | 2.851 | 0.468 | 0.468 | 2898084 | 2898084 | 247914496 | 247914496 |
| iso4017:M8x40 | stl-fine | 1 | ok | ok: 1 | 2.608 | 2.608 | 4.842 | 4.842 | 27074484 | 27074484 | 391077888 | 391077888 |
| iso4017:M10x45 | step | 1 | ok | ok: 1 | 2.512 | 2.512 | 0.078 | 0.078 | 1764689 | 1764689 | 231677952 | 231677952 |
| iso4017:M12x50 | stl-preview | 1 | ok | ok: 1 | 2.452 | 2.452 | 0.417 | 0.417 | 2755384 | 2755384 | 244289536 | 244289536 |
| iso4017:M14x45 | stl-fine | 1 | ok | ok: 1 | 2.336 | 2.336 | 7.060 | 7.060 | 37181484 | 37181484 | 591986688 | 591986688 |
| iso4017:M16x30 | step | 1 | ok | ok: 1 | 1.872 | 1.872 | 0.049 | 0.049 | 1085465 | 1085465 | 220884992 | 220884992 |
| iso4017:M16x130 | stl-preview | 1 | ok | ok: 1 | 4.481 | 4.481 | 1.565 | 1.565 | 10663384 | 10663384 | 287674368 | 287674368 |
| iso4017:M18x90 | stl-fine | 1 | ok | ok: 1 | 2.959 | 2.959 | 10.801 | 10.801 | 63308184 | 63308184 | 656228352 | 656228352 |
| iso4017:M20x60 | step | 1 | ok | ok: 1 | 2.293 | 2.293 | 0.072 | 0.072 | 1641623 | 1641623 | 227491840 | 227491840 |
| iso4014:M2x16 | stl-preview | 1 | ok | ok: 1 | 3.442 | 3.442 | 0.134 | 0.134 | 978184 | 978184 | 233709568 | 233709568 |
| iso4014:M4x30 | stl-fine | 1 | ok | ok: 1 | 2.376 | 2.376 | 1.923 | 1.923 | 9752984 | 9752984 | 330272768 | 330272768 |
| iso4014:M6x50 | step | 1 | ok | ok: 1 | 2.351 | 2.351 | 0.053 | 0.053 | 1211687 | 1211687 | 222543872 | 222543872 |
| iso4014:M8x55 | stl-preview | 1 | ok | ok: 1 | 2.477 | 2.477 | 0.205 | 0.205 | 1541284 | 1541284 | 223805440 | 223805440 |
| iso4014:M10x100 | stl-fine | 1 | ok | ok: 1 | 2.255 | 2.255 | 3.864 | 3.864 | 21537884 | 21537884 | 469516288 | 469516288 |
| iso4014:M14x65 | step | 1 | ok | ok: 1 | 2.472 | 2.472 | 0.054 | 0.054 | 1203676 | 1203676 | 222003200 | 222003200 |
| iso4014:M16x110 | stl-preview | 1 | ok | ok: 1 | 2.433 | 2.433 | 0.479 | 0.479 | 3143384 | 3143384 | 242556928 | 242556928 |
| iso4014:M18x140 | stl-fine | 1 | ok | ok: 1 | 2.501 | 2.501 | 6.174 | 6.174 | 34477384 | 34477384 | 596918272 | 596918272 |
| iso4014:M20x180 | step | 1 | ok | ok: 1 | 2.804 | 2.804 | 0.068 | 0.068 | 1465962 | 1465962 | 238497792 | 238497792 |
| iso4032:M18 | stl-preview | 1 | ok | ok: 1 | 2.487 | 2.487 | 0.174 | 0.174 | 1268984 | 1268984 | 226324480 | 226324480 |
| bolt-d1-p0.35-n240-left | stl-fine | 1 | ok | ok: 1 | 26.207 | 26.207 | 11.003 | 11.003 | 66325084 | 66325084 | 493428736 | 493428736 |
| bolt-d3-p1-n3-right | step | 1 | ok | ok: 1 | 0.845 | 0.845 | 0.017 | 0.017 | 282268 | 282268 | 210108416 | 210108416 |
| bolt-d10-p0.35-n30-right | stl-preview | 1 | ok | ok: 1 | 3.315 | 3.315 | 0.369 | 0.369 | 2745484 | 2745484 | 250507264 | 250507264 |
| bolt-d10-p3-n30-left | stl-fine | 1 | ok | ok: 1 | 2.298 | 2.298 | 5.041 | 5.041 | 27809684 | 27809684 | 428564480 | 428564480 |
| bolt-d30-p0.35-n240-right | step | 1 | ok | ok: 1 | 14.481 | 14.481 | 0.686 | 0.686 | 15432480 | 15432480 | 442372096 | 442372096 |
| bolt-d30-p10-n3-right | stl-preview | 1 | ok | ok: 1 | 0.865 | 0.865 | 0.143 | 0.143 | 1013584 | 1013584 | 227672064 | 227672064 |
| bolt-d100-p0.35-n3-left | stl-fine | 1 | ok | ok: 1 | 2.367 | 2.367 | 6.715 | 6.715 | 12060184 | 12060184 | 1155690496 | 1155690496 |
| bolt-d100-p3-n30-right | step | 1 | ok | ok: 1 | 3.057 | 3.057 | 0.102 | 0.102 | 2219450 | 2219450 | 248537088 | 248537088 |
| bolt-d300-p0.1-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n240-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.1-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n30-right | stl-preview | 1 | ok | ok: 1 | 6.889 | 6.889 | 140.422 | 140.422 | 438926884 | 438926884 | 5445214208 | 5445214208 |
| bolt-d1000-p10-n30-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d10-p0.35-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 3.258 | 3.258 | 0.072 | 0.072 | 1685537 | 1685537 | 234176512 | 234176512 |
| nut-d10-p3.5-m3d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 2.180 | 2.180 | 0.120 | 0.120 | 859284 | 859284 | 218206208 | 218206208 |
| nut-d30-p1-m3d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 6.937 | 6.937 | 101.949 | 101.949 | 498435284 | 498435284 | 2552688640 | 2552688640 |
| nut-d100-p1-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 13.024 | 13.024 | 0.218 | 0.218 | 5062648 | 5062648 | 261967872 | 261967872 |
| nut-d3-p1-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 1.613 | 1.613 | 0.018 | 0.018 | 106184 | 106184 | 212918272 | 212918272 |
| nut-d100-p0.35-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 33.143 | 33.143 | 361.746 | 361.746 | 996189184 | 996189184 | 5110341632 | 5110341632 |
| iso4017:M2x5 | stl-preview | 1 | ok | ok: 1 | 0.962 | 0.962 | 0.040 | 0.040 | 479984 | 479984 | 216227840 | 216227840 |
| iso4017:M2.5x20 | stl-fine | 1 | ok | ok: 1 | 2.682 | 2.682 | 1.769 | 1.769 | 16594884 | 16594884 | 322871296 | 322871296 |
| iso4017:M3.5x16 | step | 1 | ok | ok: 1 | 1.337 | 1.337 | 0.043 | 0.043 | 1544300 | 1544300 | 222162944 | 222162944 |
| iso4017:M5x10 | stl-preview | 1 | ok | ok: 1 | 0.881 | 0.881 | 0.073 | 0.073 | 922084 | 922084 | 218963968 | 218963968 |
| iso4017:M6x25 | stl-fine | 1 | ok | ok: 1 | 1.261 | 1.261 | 1.397 | 1.397 | 12747784 | 12747784 | 324960256 | 324960256 |
| iso4017:M7x40 | step | 1 | ok | ok: 1 | 1.796 | 1.796 | 0.067 | 0.067 | 2533603 | 2533603 | 240193536 | 240193536 |
| iso4017:M8x50 | stl-preview | 1 | ok | ok: 1 | 1.800 | 1.800 | 0.242 | 0.242 | 3390584 | 3390584 | 245092352 | 245092352 |
| iso4017:M10x55 | stl-fine | 1 | ok | ok: 1 | 1.713 | 1.713 | 4.431 | 4.431 | 45458184 | 45458184 | 512872448 | 512872448 |
| iso4017:M12x55 | step | 1 | ok | ok: 1 | 1.549 | 1.549 | 0.054 | 0.054 | 2060299 | 2060299 | 241160192 | 241160192 |
| iso4017:M14x55 | stl-preview | 1 | ok | ok: 1 | 1.443 | 1.443 | 0.236 | 0.236 | 2828284 | 2828284 | 236994560 | 236994560 |
| iso4017:M16x40 | stl-fine | 1 | ok | ok: 1 | 1.293 | 1.293 | 3.737 | 3.737 | 33923084 | 33923084 | 617189376 | 617189376 |
| iso4017:M16x140 | step | 1 | ok | ok: 1 | 2.892 | 2.892 | 0.113 | 0.113 | 4466174 | 4466174 | 270753792 | 270753792 |
| iso4017:M18x110 | stl-preview | 1 | ok | ok: 1 | 2.064 | 2.064 | 0.815 | 0.815 | 11062184 | 11062184 | 264032256 | 264032256 |
| iso4017:M20x70 | stl-fine | 1 | ok | ok: 1 | 1.492 | 1.492 | 5.114 | 5.114 | 50062084 | 50062084 | 637526016 | 637526016 |
| iso4014:M2x20 | step | 1 | ok | ok: 1 | 2.162 | 2.162 | 0.039 | 0.039 | 1434053 | 1434053 | 222396416 | 222396416 |
| iso4014:M4x40 | stl-preview | 1 | ok | ok: 1 | 1.441 | 1.441 | 0.082 | 0.082 | 1074884 | 1074884 | 220016640 | 220016640 |
| iso4014:M6x60 | stl-fine | 1 | ok | ok: 1 | 1.434 | 1.434 | 1.007 | 1.007 | 9559584 | 9559584 | 333529088 | 333529088 |
| iso4014:M8x60 | step | 1 | ok | ok: 1 | 1.504 | 1.504 | 0.034 | 0.034 | 1209365 | 1209365 | 223010816 | 223010816 |
| iso4014:M12x55 | stl-preview | 1 | ok | ok: 1 | 1.469 | 1.469 | 0.143 | 0.143 | 1735684 | 1735684 | 223776768 | 223776768 |
| iso4014:M14x80 | stl-fine | 1 | ok | ok: 1 | 1.481 | 1.481 | 2.922 | 2.922 | 27923284 | 27923284 | 580513792 | 580513792 |
| iso4014:M16x120 | step | 1 | ok | ok: 1 | 1.454 | 1.454 | 0.036 | 0.036 | 1352673 | 1352673 | 224747520 | 224747520 |
| iso4014:M18x160 | stl-preview | 1 | ok | ok: 1 | 1.491 | 1.491 | 0.347 | 0.347 | 4787684 | 4787684 | 242606080 | 242606080 |
| iso4032:M2 | stl-fine | 1 | ok | ok: 1 | 1.360 | 1.360 | 0.168 | 0.168 | 1739484 | 1739484 | 253427712 | 253427712 |
| iso4032:M20 | step | 1 | ok | ok: 1 | 1.895 | 1.895 | 0.028 | 0.028 | 880932 | 880932 | 215838720 | 215838720 |
| bolt-d3-p0.1-n3-left | stl-preview | 1 | ok | ok: 1 | 0.718 | 0.718 | 0.013 | 0.013 | 121384 | 121384 | 210145280 | 210145280 |
| bolt-d3-p1-n30-right | stl-fine | 1 | ok | ok: 1 | 2.147 | 2.147 | 1.304 | 1.304 | 11493684 | 11493684 | 301760512 | 301760512 |
| bolt-d10-p0.35-n30-left | step | 1 | ok | ok: 1 | 2.048 | 2.048 | 0.051 | 0.051 | 1973393 | 1973393 | 229744640 | 229744640 |
| bolt-d10-p3-n240-left | stl-preview | 1 | ok | ok: 1 | 8.724 | 8.724 | 1.395 | 1.395 | 19084684 | 19084684 | 394579968 | 394579968 |
| bolt-d30-p1-n3-right | stl-fine | 1 | ok | ok: 1 | 0.823 | 0.823 | 1.193 | 1.193 | 7344884 | 7344884 | 479944704 | 479944704 |
| bolt-d30-p10-n3-left | step | 1 | ok | ok: 1 | 0.564 | 0.564 | 0.014 | 0.014 | 353792 | 353792 | 209096704 | 209096704 |
| bolt-d100-p0.35-n30-left | stl-preview | 1 | ok | ok: 1 | 2.671 | 2.671 | 2.659 | 2.659 | 30386384 | 30386384 | 363307008 | 363307008 |
| bolt-d100-p3-n240-right | stl-fine | 1 | ok | ok: 1 | 7.197 | 7.197 | 366.219 | 366.219 | 1470563984 | 1470563984 | 5550116864 | 5550116864 |
| bolt-d300-p0.1-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n3-left | stl-preview | 1 | ok | ok: 1 | 1.093 | 1.093 | 1.861 | 1.861 | 11153684 | 11153684 | 721723392 | 721723392 |
| bolt-d1000-p0.1-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n30-left | step | 1 | ok | ok: 1 | 3.648 | 3.648 | 0.125 | 0.125 | 4421315 | 4421315 | 257945600 | 257945600 |
| bolt-d1000-p10-n240-left | stl-preview | 1 | killed | killed: 1 | - | - | - | - | - | - | - | - |
| nut-d10-p0.35-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 7.907 | 7.907 | 11.289 | 11.289 | 111251684 | 111251684 | 760721408 | 760721408 |
| nut-d10-p3.5-m3d-s4d-c5-right | step | 1 | ok | ok: 1 | 1.107 | 1.107 | 0.027 | 0.027 | 846530 | 846530 | 216121344 | 216121344 |
| nut-d30-p3.5-m0.8d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 1.475 | 1.475 | 0.231 | 0.231 | 2599884 | 2599884 | 240967680 | 240967680 |
| nut-d100-p1-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 7.982 | 7.982 | 100.582 | 100.582 | 432636784 | 432636784 | 3336466432 | 3336466432 |
| nut-d3-p1-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 2.043 | 2.043 | 0.026 | 0.026 | 788677 | 788677 | 220303360 | 220303360 |
| nut-d100-p3.5-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 4.082 | 4.082 | 1.670 | 1.670 | 18363884 | 18363884 | 378355712 | 378355712 |
| iso4017:M2.5x16 | stl-preview | 1 | ok | ok: 1 | 2.370 | 2.370 | 0.118 | 0.118 | 1485084 | 1485084 | 224563200 | 224563200 |
| iso4017:M3.5x12 | stl-fine | 1 | ok | ok: 1 | 1.169 | 1.169 | 0.964 | 0.964 | 7943284 | 7943284 | 317431808 | 317431808 |
| iso4017:M4x35 | step | 1 | ok | ok: 1 | 2.122 | 2.122 | 0.086 | 0.086 | 3085070 | 3085070 | 239173632 | 239173632 |
| iso4017:M6x20 | stl-preview | 1 | ok | ok: 1 | 1.237 | 1.237 | 0.114 | 0.114 | 1587384 | 1587384 | 223260672 | 223260672 |
| iso4017:M7x35 | stl-fine | 1 | ok | ok: 1 | 1.843 | 1.843 | 2.135 | 2.135 | 18935484 | 18935484 | 332533760 | 332533760 |
| iso4017:M8x40 | step | 1 | ok | ok: 1 | 1.684 | 1.684 | 0.056 | 0.056 | 2048481 | 2048481 | 235925504 | 235925504 |
| iso4017:M10x50 | stl-preview | 1 | ok | ok: 1 | 1.653 | 1.653 | 0.228 | 0.228 | 2999184 | 2999184 | 239075328 | 239075328 |
| iso4017:M12x50 | stl-fine | 1 | ok | ok: 1 | 1.577 | 1.577 | 4.042 | 4.042 | 38865984 | 38865984 | 536510464 | 536510464 |
| iso4017:M14x45 | step | 1 | ok | ok: 1 | 1.388 | 1.388 | 0.043 | 0.043 | 1538691 | 1538691 | 230109184 | 230109184 |
| iso4017:M16x35 | stl-preview | 1 | ok | ok: 1 | 1.280 | 1.280 | 0.226 | 0.226 | 2743084 | 2743084 | 229904384 | 229904384 |
| iso4017:M16x130 | stl-fine | 1 | ok | ok: 1 | 2.773 | 2.773 | 11.320 | 11.320 | 112422284 | 112422284 | 757190656 | 757190656 |
| iso4017:M18x90 | step | 1 | ok | ok: 1 | 1.829 | 1.829 | 0.062 | 0.062 | 2381845 | 2381845 | 234921984 | 234921984 |
| iso4017:M20x65 | stl-preview | 1 | ok | ok: 1 | 1.438 | 1.438 | 0.448 | 0.448 | 7274084 | 7274084 | 239640576 | 239640576 |
| iso4014:M2x16 | stl-fine | 1 | ok | ok: 1 | 2.099 | 2.099 | 0.846 | 0.846 | 8250284 | 8250284 | 275365888 | 275365888 |
| iso4014:M4x30 | step | 1 | ok | ok: 1 | 1.457 | 1.457 | 0.035 | 0.035 | 1298275 | 1298275 | 217899008 | 217899008 |
| iso4014:M6x55 | stl-preview | 1 | ok | ok: 1 | 1.444 | 1.444 | 0.098 | 0.098 | 1476484 | 1476484 | 224309248 | 224309248 |
| iso4014:M8x55 | stl-fine | 1 | ok | ok: 1 | 1.573 | 1.573 | 1.510 | 1.510 | 14707484 | 14707484 | 380301312 | 380301312 |
| iso4014:M10x100 | step | 1 | ok | ok: 1 | 1.419 | 1.419 | 0.032 | 0.032 | 1096264 | 1096264 | 222953472 | 222953472 |
| iso4014:M14x70 | stl-preview | 1 | ok | ok: 1 | 1.589 | 1.589 | 0.145 | 0.145 | 1835884 | 1835884 | 228265984 | 228265984 |
| iso4014:M16x110 | stl-fine | 1 | ok | ok: 1 | 1.500 | 1.500 | 3.581 | 3.581 | 33383384 | 33383384 | 616222720 | 616222720 |
| iso4014:M18x140 | step | 1 | ok | ok: 1 | 1.580 | 1.580 | 0.041 | 0.041 | 1368868 | 1368868 | 225599488 | 225599488 |
| iso4014:M20x200 | stl-preview | 1 | ok | ok: 1 | 1.722 | 1.722 | 0.404 | 0.404 | 6015484 | 6015484 | 238608384 | 238608384 |
| iso4032:M18 | stl-fine | 1 | ok | ok: 1 | 1.522 | 1.522 | 1.011 | 1.011 | 9045684 | 9045684 | 419672064 | 419672064 |
| bolt-d1-p0.35-n240-left | step | 1 | ok | ok: 1 | 16.884 | 16.884 | 0.352 | 0.352 | 12609285 | 12609285 | 357597184 | 357597184 |
| bolt-d3-p1-n3-left | stl-preview | 1 | ok | ok: 1 | 0.512 | 0.512 | 0.013 | 0.013 | 117784 | 117784 | 209641472 | 209641472 |
| bolt-d10-p0.35-n30-right | stl-fine | 1 | ok | ok: 1 | 2.083 | 2.083 | 4.163 | 4.163 | 40733484 | 40733484 | 545394688 | 545394688 |
| bolt-d10-p3-n30-left | step | 1 | ok | ok: 1 | 1.422 | 1.422 | 0.048 | 0.048 | 1774878 | 1774878 | 225185792 | 225185792 |
| bolt-d30-p0.35-n240-left | stl-preview | 1 | ok | ok: 1 | 9.005 | 9.005 | 4.127 | 4.127 | 61196684 | 61196684 | 541671424 | 541671424 |
| bolt-d30-p10-n3-right | stl-fine | 1 | ok | ok: 1 | 0.508 | 0.508 | 1.147 | 1.147 | 7810184 | 7810184 | 510345216 | 510345216 |
| bolt-d100-p0.35-n3-left | step | 1 | ok | ok: 1 | 1.411 | 1.411 | 0.016 | 0.016 | 459344 | 459344 | 210829312 | 210829312 |
| bolt-d100-p3-n30-left | stl-preview | 1 | ok | ok: 1 | 1.874 | 1.874 | 2.827 | 2.827 | 30236784 | 30236784 | 362135552 | 362135552 |
| bolt-d300-p0.1-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p1-n240-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.1-n3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n30-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n30-left | step | 1 | ok | ok: 1 | 1.929 | 1.929 | 0.107 | 0.107 | 3769882 | 3769882 | 243408896 | 243408896 |
| nut-d10-p0.35-m3d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 8.266 | 8.266 | 0.538 | 0.538 | 7495084 | 7495084 | 261607424 | 261607424 |
| nut-d10-p3.5-m3d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.369 | 1.369 | 0.969 | 0.969 | 9397484 | 9397484 | 383234048 | 383234048 |
| nut-d30-p1-m3d-s4d-c5-right | step | 1 | ok | ok: 1 | 4.406 | 4.406 | 0.172 | 0.172 | 6059064 | 6059064 | 258932736 | 258932736 |
| nut-d100-p1-m0.8d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 9.749 | 9.749 | 8.240 | 8.240 | 98692184 | 98692184 | 627261440 | 627261440 |
| nut-d3-p1-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 0.954 | 0.954 | 0.100 | 0.100 | 939184 | 939184 | 249327616 | 249327616 |
| nut-d100-p0.35-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 21.589 | 21.589 | 0.387 | 0.387 | 13248586 | 13248586 | 335982592 | 335982592 |
| iso4017:M2x5 | stl-fine | 1 | ok | ok: 1 | 1.056 | 1.056 | 0.534 | 0.534 | 3966684 | 3966684 | 271433728 | 271433728 |
| iso4017:M2.5x20 | step | 1 | ok | ok: 1 | 2.846 | 2.846 | 0.078 | 0.078 | 2405460 | 2405460 | 231649280 | 231649280 |
| iso4017:M3.5x20 | stl-preview | 1 | ok | ok: 1 | 1.706 | 1.706 | 0.149 | 0.149 | 1545584 | 1545584 | 224808960 | 224808960 |
| iso4017:M5x10 | stl-fine | 1 | ok | ok: 1 | 0.982 | 0.982 | 0.831 | 0.831 | 6091984 | 6091984 | 309862400 | 309862400 |
| iso4017:M6x25 | step | 1 | ok | ok: 1 | 1.397 | 1.397 | 0.052 | 0.052 | 1623591 | 1623591 | 222879744 | 222879744 |
| iso4017:M7x45 | stl-preview | 1 | ok | ok: 1 | 2.197 | 2.197 | 0.282 | 0.282 | 3761184 | 3761184 | 241926144 | 241926144 |
| iso4017:M8x50 | stl-fine | 1 | ok | ok: 1 | 2.009 | 2.009 | 4.342 | 4.342 | 34180884 | 34180884 | 438439936 | 438439936 |
| iso4017:M10x55 | step | 1 | ok | ok: 1 | 1.840 | 1.840 | 0.069 | 0.069 | 2153012 | 2153012 | 236912640 | 236912640 |
| iso4017:M12x60 | stl-preview | 1 | ok | ok: 1 | 1.813 | 1.813 | 0.285 | 0.285 | 3317484 | 3317484 | 240123904 | 240123904 |
| iso4017:M14x55 | stl-fine | 1 | ok | ok: 1 | 1.581 | 1.581 | 6.479 | 6.479 | 45401284 | 45401284 | 597094400 | 597094400 |
| iso4017:M16x40 | step | 1 | ok | ok: 1 | 1.497 | 1.497 | 0.045 | 0.045 | 1394842 | 1394842 | 226693120 | 226693120 |
| iso4017:M16x150 | stl-preview | 1 | ok | ok: 1 | 3.415 | 3.415 | 1.211 | 1.211 | 12378384 | 12378384 | 290566144 | 290566144 |
| iso4017:M18x110 | stl-fine | 1 | ok | ok: 1 | 2.353 | 2.353 | 10.045 | 10.045 | 77608984 | 77608984 | 707633152 | 707633152 |
| iso4017:M20x70 | step | 1 | ok | ok: 1 | 1.653 | 1.653 | 0.072 | 0.072 | 1900835 | 1900835 | 232792064 | 232792064 |
| iso4014:M2.5x16 | stl-preview | 1 | ok | ok: 1 | 2.218 | 2.218 | 0.092 | 0.092 | 1039184 | 1039184 | 219779072 | 219779072 |
| iso4014:M4x40 | stl-fine | 1 | ok | ok: 1 | 1.643 | 1.643 | 1.356 | 1.356 | 9752984 | 9752984 | 321396736 | 321396736 |
| iso4014:M6x60 | step | 1 | ok | ok: 1 | 1.612 | 1.612 | 0.039 | 0.039 | 1211807 | 1211807 | 222404608 | 222404608 |
| iso4014:M8x65 | stl-preview | 1 | ok | ok: 1 | 1.675 | 1.675 | 0.129 | 0.129 | 1541284 | 1541284 | 220590080 | 220590080 |
| iso4014:M12x55 | stl-fine | 1 | ok | ok: 1 | 1.595 | 1.595 | 3.344 | 3.344 | 23581884 | 23581884 | 519327744 | 519327744 |
| iso4014:M14x80 | step | 1 | ok | ok: 1 | 1.637 | 1.637 | 0.039 | 0.039 | 1203668 | 1203668 | 221663232 | 221663232 |
| iso4014:M16x130 | stl-preview | 1 | ok | ok: 1 | 1.781 | 1.781 | 0.330 | 0.330 | 3640284 | 3640284 | 236445696 | 236445696 |
| iso4014:M18x160 | stl-fine | 1 | ok | ok: 1 | 1.695 | 1.695 | 4.591 | 4.591 | 34477384 | 34477384 | 579768320 | 579768320 |
| iso4032:M2 | step | 1 | ok | ok: 1 | 1.566 | 1.566 | 0.022 | 0.022 | 559963 | 559963 | 211030016 | 211030016 |
| bolt-d1-p0.1-n3-right | stl-preview | 1 | ok | ok: 1 | 0.606 | 0.606 | 0.014 | 0.014 | 128184 | 128184 | 210251776 | 210251776 |
| bolt-d3-p0.1-n3-left | stl-fine | 1 | ok | ok: 1 | 0.763 | 0.763 | 0.207 | 0.207 | 1025184 | 1025184 | 273178624 | 273178624 |
| bolt-d3-p1-n30-right | step | 1 | ok | ok: 1 | 2.311 | 2.311 | 0.056 | 0.056 | 1694430 | 1694430 | 223842304 | 223842304 |
| bolt-d10-p0.35-n240-right | stl-preview | 1 | ok | ok: 1 | 10.068 | 10.068 | 1.783 | 1.783 | 21977684 | 21977684 | 408403968 | 408403968 |
| bolt-d10-p3-n240-left | stl-fine | 1 | ok | ok: 1 | 9.605 | 9.605 | 29.938 | 29.938 | 223207684 | 223207684 | 925380608 | 925380608 |
| bolt-d30-p1-n3-right | step | 1 | ok | ok: 1 | 0.988 | 0.988 | 0.018 | 0.018 | 381958 | 381958 | 210513920 | 210513920 |
| bolt-d30-p10-n30-right | stl-preview | 1 | ok | ok: 1 | 1.334 | 1.334 | 0.846 | 0.846 | 10666084 | 10666084 | 265990144 | 265990144 |
| bolt-d100-p0.35-n30-left | stl-fine | 1 | ok | ok: 1 | 2.943 | 2.943 | 58.456 | 58.456 | 158427384 | 158427384 | 2832642048 | 2832642048 |
| bolt-d100-p3-n240-right | step | 1 | ok | ok: 1 | 7.887 | 7.887 | 0.541 | 0.541 | 16420670 | 16420670 | 418320384 | 418320384 |
| bolt-d300-p0.35-n3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n3-left | stl-fine | 1 | ok | ok: 1 | 1.132 | 1.132 | 46.541 | 46.541 | 57256684 | 57256684 | 7906009088 | 7906009088 |
| bolt-d1000-p0.1-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n240-right | stl-preview | 1 | killed | killed: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n240-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d10-p0.35-m3d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 8.151 | 8.151 | 0.161 | 0.161 | 5512760 | 5512760 | 257683456 | 257683456 |
| nut-d30-p0.35-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nut-d30-p3.5-m0.8d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 1.520 | 1.520 | 6.055 | 6.055 | 34723784 | 34723784 | 1021272064 | 1021272064 |
| nut-d100-p1-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 8.064 | 8.064 | 0.157 | 0.157 | 5062880 | 5062880 | 255774720 | 255774720 |
| nut-d10-p0.35-m0.8d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 3.729 | 3.729 | 0.146 | 0.146 | 1486984 | 1486984 | 237436928 | 237436928 |
| nut-d100-p3.5-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 4.222 | 4.222 | 29.158 | 29.158 | 98671784 | 98671784 | 2354561024 | 2354561024 |
| iso4017:M2x5 | step | 1 | ok | ok: 1 | 1.231 | 1.231 | 0.028 | 0.028 | 792456 | 792456 | 214536192 | 214536192 |
| iso4017:M2.5x25 | stl-preview | 1 | ok | ok: 1 | 4.221 | 4.221 | 0.238 | 0.238 | 2301984 | 2301984 | 243830784 | 243830784 |
| iso4017:M3.5x20 | stl-fine | 1 | ok | ok: 1 | 1.986 | 1.986 | 2.126 | 2.126 | 13214684 | 13214684 | 325738496 | 325738496 |
| iso4017:M5x10 | step | 1 | ok | ok: 1 | 1.150 | 1.150 | 0.030 | 0.030 | 894209 | 894209 | 217989120 | 217989120 |
| iso4017:M6x30 | stl-preview | 1 | ok | ok: 1 | 1.983 | 1.983 | 0.226 | 0.226 | 2427784 | 2427784 | 232722432 | 232722432 |
| iso4017:M7x45 | stl-fine | 1 | ok | ok: 1 | 2.653 | 2.653 | 3.485 | 3.485 | 23793084 | 23793084 | 345763840 | 345763840 |
| iso4017:M8x50 | step | 1 | ok | ok: 1 | 2.364 | 2.364 | 0.078 | 0.078 | 2545138 | 2545138 | 239026176 | 239026176 |
| iso4017:M10x60 | stl-preview | 1 | ok | ok: 1 | 2.376 | 2.376 | 0.359 | 0.359 | 3604984 | 3604984 | 245915648 | 245915648 |
| iso4017:M12x60 | stl-fine | 1 | ok | ok: 1 | 2.134 | 2.134 | 6.430 | 6.430 | 46831484 | 46831484 | 587333632 | 587333632 |
| iso4017:M14x55 | step | 1 | ok | ok: 1 | 1.880 | 1.880 | 0.061 | 0.061 | 1854960 | 1854960 | 233996288 | 233996288 |
| iso4017:M16x45 | stl-preview | 1 | ok | ok: 1 | 1.800 | 1.800 | 0.418 | 0.418 | 3689484 | 3689484 | 233586688 | 233586688 |
| iso4017:M16x150 | stl-fine | 1 | ok | ok: 1 | 4.024 | 4.024 | 18.250 | 18.250 | 130491884 | 130491884 | 813006848 | 813006848 |
| iso4017:M18x110 | step | 1 | ok | ok: 1 | 2.686 | 2.686 | 0.091 | 0.091 | 2876374 | 2876374 | 244330496 | 244330496 |
| iso4017:M20x80 | stl-preview | 1 | ok | ok: 1 | 2.161 | 2.161 | 0.788 | 0.788 | 8999484 | 8999484 | 254545920 | 254545920 |
| iso4014:M2.5x16 | stl-fine | 1 | ok | ok: 1 | 2.620 | 2.620 | 1.372 | 1.372 | 9579284 | 9579284 | 315908096 | 315908096 |
| iso4014:M4x40 | step | 1 | ok | ok: 1 | 1.886 | 1.886 | 0.042 | 0.042 | 1298248 | 1298248 | 217731072 | 217731072 |
| iso4014:M7x35 | stl-preview | 1 | ok | ok: 1 | 1.776 | 1.776 | 0.157 | 0.157 | 1646684 | 1646684 | 224804864 | 224804864 |
| iso4014:M8x65 | stl-fine | 1 | ok | ok: 1 | 1.975 | 1.975 | 2.098 | 2.098 | 14707484 | 14707484 | 391282688 | 391282688 |
| iso4014:M12x55 | step | 1 | ok | ok: 1 | 1.909 | 1.909 | 0.039 | 0.039 | 1187166 | 1187166 | 221609984 | 221609984 |
| iso4014:M14x90 | stl-preview | 1 | ok | ok: 1 | 1.932 | 1.932 | 0.200 | 0.200 | 1835884 | 1835884 | 224858112 | 224858112 |
| iso4014:M16x130 | stl-fine | 1 | ok | ok: 1 | 2.100 | 2.100 | 5.306 | 5.306 | 38614184 | 38614184 | 595599360 | 595599360 |
| iso4014:M18x160 | step | 1 | ok | ok: 1 | 2.026 | 2.026 | 0.045 | 0.045 | 1368870 | 1368870 | 225107968 | 225107968 |
| iso4032:M2.5 | stl-preview | 1 | ok | ok: 1 | 1.900 | 1.900 | 0.023 | 0.023 | 189084 | 189084 | 212246528 | 212246528 |
| bolt-d1-p0.1-n3-right | stl-fine | 1 | ok | ok: 1 | 0.706 | 0.706 | 0.137 | 0.137 | 922884 | 922884 | 246992896 | 246992896 |
| bolt-d3-p0.1-n3-left | step | 1 | ok | ok: 1 | 0.900 | 0.900 | 0.015 | 0.015 | 332867 | 332867 | 210403328 | 210403328 |
| bolt-d3-p1-n30-left | stl-preview | 1 | ok | ok: 1 | 2.675 | 2.675 | 0.124 | 0.124 | 1099684 | 1099684 | 221614080 | 221614080 |
| bolt-d10-p0.35-n240-right | stl-fine | 1 | ok | ok: 1 | 11.690 | 11.690 | 42.014 | 42.014 | 327102984 | 327102984 | 1198911488 | 1198911488 |
| bolt-d10-p3-n240-left | step | 1 | ok | ok: 1 | 10.966 | 10.966 | 0.428 | 0.428 | 13368933 | 13368933 | 396984320 | 396984320 |
| bolt-d30-p1-n3-left | stl-preview | 1 | ok | ok: 1 | 1.060 | 1.060 | 0.098 | 0.098 | 757684 | 757684 | 227454976 | 227454976 |
| bolt-d30-p10-n30-right | stl-fine | 1 | ok | ok: 1 | 1.553 | 1.553 | 12.077 | 12.077 | 84503984 | 84503984 | 871657472 | 871657472 |
| bolt-d100-p0.35-n30-left | step | 1 | ok | ok: 1 | 3.451 | 3.451 | 0.071 | 0.071 | 2238629 | 2238629 | 248082432 | 248082432 |
| bolt-d100-p3-n240-left | stl-preview | 1 | ok | ok: 1 | 9.265 | 9.265 | 27.170 | 27.170 | 242633784 | 242633784 | 955678720 | 955678720 |
| bolt-d300-p0.35-n3-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n3-left | step | 1 | ok | ok: 1 | 1.371 | 1.371 | 0.020 | 0.020 | 496824 | 496824 | 212987904 | 212987904 |
| bolt-d1000-p0.1-n30-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n240-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p10-n240-left | step | 1 | ok | ok: 1 | 10.034 | 10.034 | 0.952 | 0.952 | 28801913 | 28801913 | 608264192 | 608264192 |
| nut-d10-p0.35-m3d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 7.890 | 7.890 | 2.378 | 2.378 | 26875084 | 26875084 | 310988800 | 310988800 |
| nut-d30-p0.35-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nut-d30-p3.5-m0.8d-s1.6d-c5-right | step | 1 | ok | ok: 1 | 1.828 | 1.828 | 0.029 | 0.029 | 771088 | 771088 | 225046528 | 225046528 |
| nut-d100-p1-m0.8d-s4d-c5-right | stl-preview | 1 | ok | ok: 1 | 10.892 | 10.892 | 11.005 | 11.005 | 98728184 | 98728184 | 604565504 | 604565504 |
| nut-d10-p0.35-m0.8d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 4.320 | 4.320 | 2.795 | 2.795 | 20019384 | 20019384 | 415924224 | 415924224 |
| nut-d100-p3.5-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 5.057 | 5.057 | 0.061 | 0.061 | 1849763 | 1849763 | 235073536 | 235073536 |
| iso4017:M2x6 | stl-preview | 1 | ok | ok: 1 | 1.450 | 1.450 | 0.063 | 0.063 | 574784 | 574784 | 217501696 | 217501696 |
| iso4017:M2.5x25 | stl-fine | 1 | ok | ok: 1 | 4.260 | 4.260 | 2.781 | 2.781 | 20736884 | 20736884 | 325144576 | 325144576 |
| iso4017:M3.5x20 | step | 1 | ok | ok: 1 | 1.980 | 1.980 | 0.065 | 0.065 | 1918454 | 1918454 | 225595392 | 225595392 |
| iso4017:M5x12 | stl-preview | 1 | ok | ok: 1 | 1.319 | 1.319 | 0.115 | 0.115 | 1116584 | 1116584 | 221163520 | 221163520 |
| iso4017:M6x30 | stl-fine | 1 | ok | ok: 1 | 1.991 | 1.991 | 2.326 | 2.326 | 15208984 | 15208984 | 346759168 | 346759168 |
| iso4017:M7x45 | step | 1 | ok | ok: 1 | 2.601 | 2.601 | 0.087 | 0.087 | 2827479 | 2827479 | 244613120 | 244613120 |
| iso4017:M8x55 | stl-preview | 1 | ok | ok: 1 | 2.580 | 2.580 | 0.366 | 0.366 | 3702384 | 3702384 | 245780480 | 245780480 |
| iso4017:M10x60 | stl-fine | 1 | ok | ok: 1 | 2.373 | 2.373 | 6.559 | 6.559 | 49630584 | 49630584 | 550510592 | 550510592 |
| iso4017:M12x60 | step | 1 | ok | ok: 1 | 2.150 | 2.150 | 0.068 | 0.068 | 2224669 | 2224669 | 230408192 | 230408192 |
| iso4017:M14x60 | stl-preview | 1 | ok | ok: 1 | 2.076 | 2.076 | 0.350 | 0.350 | 3069284 | 3069284 | 234971136 | 234971136 |
| iso4017:M16x45 | stl-fine | 1 | ok | ok: 1 | 1.786 | 1.786 | 5.622 | 5.622 | 38914384 | 38914384 | 630464512 | 630464512 |
| iso4017:M16x150 | step | 1 | ok | ok: 1 | 4.025 | 4.025 | 0.149 | 0.149 | 4756895 | 4756895 | 289267712 | 289267712 |
| iso4017:M18x120 | stl-preview | 1 | ok | ok: 1 | 2.864 | 2.864 | 1.288 | 1.288 | 12231884 | 12231884 | 273424384 | 273424384 |
| iso4017:M20x80 | stl-fine | 1 | ok | ok: 1 | 2.154 | 2.154 | 8.164 | 8.164 | 58629084 | 58629084 | 635936768 | 635936768 |
| iso4014:M2.5x16 | step | 1 | ok | ok: 1 | 2.630 | 2.630 | 0.047 | 0.047 | 1413391 | 1413391 | 219283456 | 219283456 |
| iso4014:M5x25 | stl-preview | 1 | ok | ok: 1 | 2.023 | 2.023 | 0.145 | 0.145 | 1481784 | 1481784 | 224370688 | 224370688 |
| iso4014:M7x35 | stl-fine | 1 | ok | ok: 1 | 1.794 | 1.794 | 1.562 | 1.562 | 11039884 | 11039884 | 320602112 | 320602112 |
| iso4014:M8x65 | step | 1 | ok | ok: 1 | 1.971 | 1.971 | 0.039 | 0.039 | 1209364 | 1209364 | 222429184 | 222429184 |
| iso4014:M12x60 | stl-preview | 1 | ok | ok: 1 | 1.904 | 1.904 | 0.186 | 0.186 | 1735684 | 1735684 | 225075200 | 225075200 |
| iso4014:M14x90 | stl-fine | 1 | ok | ok: 1 | 1.932 | 1.932 | 4.109 | 4.109 | 27923284 | 27923284 | 568967168 | 568967168 |
| iso4014:M16x130 | step | 1 | ok | ok: 1 | 2.090 | 2.090 | 0.051 | 0.051 | 1536996 | 1536996 | 227381248 | 227381248 |
| iso4014:M18x180 | stl-preview | 1 | ok | ok: 1 | 1.984 | 1.984 | 0.479 | 0.479 | 4787684 | 4787684 | 244768768 | 244768768 |
| iso4032:M2.5 | stl-fine | 1 | ok | ok: 1 | 1.915 | 1.915 | 0.248 | 0.248 | 1689584 | 1689584 | 255201280 | 255201280 |
| bolt-d1-p0.1-n3-right | step | 1 | ok | ok: 1 | 0.709 | 0.709 | 0.014 | 0.014 | 288834 | 288834 | 209821696 | 209821696 |
| bolt-d3-p0.1-n30-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n30-left | stl-fine | 1 | ok | ok: 1 | 2.682 | 2.682 | 1.553 | 1.553 | 9257484 | 9257484 | 305278976 | 305278976 |
| bolt-d10-p0.35-n240-right | step | 1 | ok | ok: 1 | 11.774 | 11.774 | 0.464 | 0.464 | 14713154 | 14713154 | 399695872 | 399695872 |
| bolt-d30-p0.1-n3-right | stl-preview | 1 | ok | ok: 1 | 1.815 | 1.815 | 0.114 | 0.114 | 946684 | 946684 | 229785600 | 229785600 |
| bolt-d30-p1-n3-left | stl-fine | 1 | ok | ok: 1 | 1.063 | 1.063 | 1.851 | 1.851 | 7196784 | 7196784 | 476487680 | 476487680 |
| bolt-d30-p10-n30-right | step | 1 | ok | ok: 1 | 1.576 | 1.576 | 0.069 | 0.069 | 2058763 | 2058763 | 231825408 | 231825408 |
| bolt-d100-p0.35-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n240-left | stl-fine | 1 | ok | ok: 1 | 9.354 | 9.354 | 388.767 | 388.767 | 1163247484 | 1163247484 | 4819406848 | 4819406848 |
| bolt-d300-p0.35-n3-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n30-right | stl-preview | 1 | ok | ok: 1 | 2.360 | 2.360 | 25.754 | 25.754 | 151077584 | 151077584 | 1308196864 | 1308196864 |
| bolt-d1000-p0.1-n30-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n240-right | step | 1 | ok | ok: 1 | 12.060 | 12.060 | 0.932 | 0.932 | 28757151 | 28757151 | 558112768 | 558112768 |
| nut-d3-p0.35-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 2.368 | 2.368 | 0.039 | 0.039 | 306484 | 306484 | 217403392 | 217403392 |
| nut-d10-p0.35-m3d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 7.944 | 7.944 | 20.414 | 20.414 | 132472284 | 132472284 | 834863104 | 834863104 |
| nut-d30-p0.35-m0.8d-s1.6d-c0.15-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nut-d30-p3.5-m0.8d-s4d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 1.990 | 1.990 | 0.181 | 0.181 | 1717884 | 1717884 | 232730624 | 232730624 |
| nut-d100-p1-m0.8d-s4d-c5-right | stl-fine | 1 | ok | ok: 1 | 11.014 | 11.014 | 157.295 | 157.295 | 514749884 | 514749884 | 3701780480 | 3701780480 |
| nut-d10-p0.35-m0.8d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 4.352 | 4.352 | 0.054 | 0.054 | 1744012 | 1744012 | 234168320 | 234168320 |
| nut-d100-p3.5-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 10.992 | 10.992 | 9.537 | 9.537 | 81918184 | 81918184 | 525295616 | 525295616 |
| iso4017:M2x6 | stl-fine | 1 | ok | ok: 1 | 1.231 | 1.231 | 0.577 | 0.577 | 4656284 | 4656284 | 267100160 | 267100160 |
| iso4017:M2.5x25 | step | 1 | ok | ok: 1 | 3.607 | 3.607 | 0.091 | 0.091 | 3027901 | 3027901 | 250781696 | 250781696 |
| iso4017:M3.5x25 | stl-preview | 1 | ok | ok: 1 | 2.050 | 2.050 | 0.178 | 0.178 | 1934284 | 1934284 | 229666816 | 229666816 |
| iso4017:M5x12 | stl-fine | 1 | ok | ok: 1 | 1.128 | 1.128 | 0.902 | 0.902 | 7178784 | 7178784 | 313409536 | 313409536 |
| iso4017:M6x30 | step | 1 | ok | ok: 1 | 1.693 | 1.693 | 0.055 | 0.055 | 1919890 | 1919890 | 229261312 | 229261312 |
| iso4017:M7x50 | stl-preview | 1 | ok | ok: 1 | 2.453 | 2.453 | 0.312 | 0.312 | 4148684 | 4148684 | 252489728 | 252489728 |
| iso4017:M8x55 | stl-fine | 1 | ok | ok: 1 | 2.247 | 2.247 | 4.213 | 4.213 | 37340284 | 37340284 | 416796672 | 416796672 |
| iso4017:M10x60 | step | 1 | ok | ok: 1 | 2.077 | 2.077 | 0.072 | 0.072 | 2317056 | 2317056 | 244822016 | 244822016 |
| iso4017:M12x65 | stl-preview | 1 | ok | ok: 1 | 1.972 | 1.972 | 0.313 | 0.313 | 3592084 | 3592084 | 241455104 | 241455104 |
| iso4017:M14x60 | stl-fine | 1 | ok | ok: 1 | 1.768 | 1.768 | 5.988 | 5.988 | 49630384 | 49630384 | 620150784 | 620150784 |
| iso4017:M16x45 | step | 1 | ok | ok: 1 | 1.561 | 1.561 | 0.046 | 0.046 | 1558477 | 1558477 | 227311616 | 227311616 |
| iso4017:M16x160 | stl-preview | 1 | ok | ok: 1 | 3.578 | 3.578 | 1.181 | 1.181 | 13148084 | 13148084 | 297435136 | 297435136 |
| iso4017:M18x120 | stl-fine | 1 | ok | ok: 1 | 2.410 | 2.410 | 9.170 | 9.170 | 84498384 | 84498384 | 693940224 | 693940224 |
| iso4017:M20x80 | step | 1 | ok | ok: 1 | 1.834 | 1.834 | 0.065 | 0.065 | 2136241 | 2136241 | 236388352 | 236388352 |
| iso4014:M2.5x20 | stl-preview | 1 | ok | ok: 1 | 2.254 | 2.254 | 0.088 | 0.088 | 1039184 | 1039184 | 219635712 | 219635712 |
| iso4014:M5x25 | stl-fine | 1 | ok | ok: 1 | 1.702 | 1.702 | 1.157 | 1.157 | 10190184 | 10190184 | 321667072 | 321667072 |
| iso4014:M7x35 | step | 1 | ok | ok: 1 | 1.629 | 1.629 | 0.040 | 0.040 | 1327408 | 1327408 | 221827072 | 221827072 |
| iso4014:M8x70 | stl-preview | 1 | ok | ok: 1 | 1.705 | 1.705 | 0.124 | 0.124 | 1541284 | 1541284 | 222908416 | 222908416 |
| iso4014:M12x60 | stl-fine | 1 | ok | ok: 1 | 1.623 | 1.623 | 2.866 | 2.866 | 23581884 | 23581884 | 503885824 | 503885824 |
| iso4014:M14x90 | step | 1 | ok | ok: 1 | 1.633 | 1.633 | 0.037 | 0.037 | 1203647 | 1203647 | 224956416 | 224956416 |
| iso4014:M16x140 | stl-preview | 1 | ok | ok: 1 | 1.782 | 1.782 | 0.311 | 0.311 | 3640284 | 3640284 | 232820736 | 232820736 |
| iso4014:M18x180 | stl-fine | 1 | ok | ok: 1 | 1.657 | 1.657 | 3.827 | 3.827 | 34477384 | 34477384 | 582397952 | 582397952 |
| iso4032:M2.5 | step | 1 | ok | ok: 1 | 1.640 | 1.640 | 0.020 | 0.020 | 551189 | 551189 | 211181568 | 211181568 |
| bolt-d1-p0.1-n3-left | stl-preview | 1 | ok | ok: 1 | 0.576 | 0.576 | 0.013 | 0.013 | 128784 | 128784 | 210063360 | 210063360 |
| bolt-d3-p0.1-n30-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n30-left | step | 1 | ok | ok: 1 | 2.281 | 2.281 | 0.056 | 0.056 | 1692863 | 1692863 | 223801344 | 223801344 |
| bolt-d10-p0.35-n240-left | stl-preview | 1 | ok | ok: 1 | 10.080 | 10.080 | 1.408 | 1.408 | 18006084 | 18006084 | 455905280 | 455905280 |
| bolt-d30-p0.1-n3-right | stl-fine | 1 | ok | ok: 1 | 1.599 | 1.599 | 1.580 | 1.580 | 9913684 | 9913684 | 574042112 | 574042112 |
| bolt-d30-p1-n3-left | step | 1 | ok | ok: 1 | 0.905 | 0.905 | 0.015 | 0.015 | 382476 | 382476 | 210788352 | 210788352 |
| bolt-d30-p10-n30-left | stl-preview | 1 | ok | ok: 1 | 1.344 | 1.344 | 0.576 | 0.576 | 7839784 | 7839784 | 251547648 | 251547648 |
| bolt-d100-p0.35-n240-right | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p3-n240-left | step | 1 | ok | ok: 1 | 7.656 | 7.656 | 0.480 | 0.480 | 16417148 | 16417148 | 433307648 | 433307648 |
| bolt-d300-p0.35-n3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n30-right | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p0.1-n30-left | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n240-left | stl-preview | 1 | killed | killed: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p0.35-m0.8d-s1.6d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.997 | 1.997 | 0.329 | 0.329 | 2610384 | 2610384 | 281464832 | 281464832 |
| nut-d10-p0.35-m3d-s4d-c5-right | step | 1 | ok | ok: 1 | 6.805 | 6.805 | 0.158 | 0.158 | 5583108 | 5583108 | 258523136 | 258523136 |
| nut-d30-p0.35-m0.8d-s1.6d-c5-right | stl-preview | 1 | ok | ok: 1 | 7.241 | 7.241 | 2.040 | 2.040 | 24540784 | 24540784 | 408096768 | 408096768 |
| nut-d30-p3.5-m0.8d-s4d-c0.15-right | stl-fine | 1 | ok | ok: 1 | 1.672 | 1.672 | 2.176 | 2.176 | 16140384 | 16140384 | 554045440 | 554045440 |
| nut-d100-p1-m0.8d-s4d-c5-right | step | 1 | ok | ok: 1 | 8.796 | 8.796 | 0.163 | 0.163 | 5546450 | 5546450 | 268644352 | 268644352 |
| nut-d10-p0.35-m3d-s1.6d-c0.15-left | stl-preview | 1 | ok | ok: 1 | 8.434 | 8.434 | 0.469 | 0.469 | 6221684 | 6221684 | 266358784 | 266358784 |
| nut-d100-p3.5-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 9.147 | 9.147 | 113.082 | 113.082 | 431538684 | 431538684 | 3257507840 | 3257507840 |
| iso4017:M2x6 | step | 1 | ok | ok: 1 | 1.844 | 1.844 | 0.044 | 0.044 | 894909 | 894909 | 215642112 | 215642112 |
| iso4017:M3x6 | stl-preview | 1 | ok | ok: 1 | 1.672 | 1.672 | 0.083 | 0.083 | 529984 | 529984 | 214421504 | 214421504 |
| iso4017:M3.5x25 | stl-fine | 1 | ok | ok: 1 | 3.005 | 3.005 | 3.300 | 3.300 | 16563084 | 16563084 | 326520832 | 326520832 |
| iso4017:M5x12 | step | 1 | ok | ok: 1 | 1.669 | 1.669 | 0.047 | 0.047 | 1019364 | 1019364 | 220614656 | 220614656 |
| iso4017:M6x35 | stl-preview | 1 | ok | ok: 1 | 2.817 | 2.817 | 0.450 | 0.450 | 2805184 | 2805184 | 249663488 | 249663488 |
| iso4017:M7x50 | stl-fine | 1 | ok | ok: 1 | 3.565 | 3.565 | 4.941 | 4.941 | 26856084 | 26856084 | 338288640 | 338288640 |
| iso4017:M8x55 | step | 1 | ok | ok: 1 | 3.223 | 3.223 | 0.115 | 0.115 | 2768266 | 2768266 | 249683968 | 249683968 |
| iso4017:M10x65 | stl-preview | 1 | ok | ok: 1 | 3.092 | 3.092 | 0.550 | 0.550 | 3909984 | 3909984 | 249237504 | 249237504 |
| iso4017:M12x65 | stl-fine | 1 | ok | ok: 1 | 2.835 | 2.835 | 9.541 | 9.541 | 50512484 | 50512484 | 597401600 | 597401600 |
| iso4017:M14x60 | step | 1 | ok | ok: 1 | 2.574 | 2.574 | 0.082 | 0.082 | 1983499 | 1983499 | 231014400 | 231014400 |
| iso4017:M16x50 | stl-preview | 1 | ok | ok: 1 | 2.352 | 2.352 | 0.649 | 0.649 | 4098584 | 4098584 | 244625408 | 244625408 |
| iso4017:M16x160 | stl-fine | 1 | ok | ok: 1 | 5.244 | 5.244 | 24.116 | 24.116 | 138570484 | 138570484 | 939831296 | 939831296 |
| iso4017:M18x120 | step | 1 | ok | ok: 1 | 3.617 | 3.617 | 0.130 | 0.130 | 3119081 | 3119081 | 259928064 | 259928064 |
| iso4017:M20x90 | stl-preview | 1 | ok | ok: 1 | 2.927 | 2.927 | 1.267 | 1.267 | 10290984 | 10290984 | 257245184 | 257245184 |
| iso4014:M2.5x20 | stl-fine | 1 | ok | ok: 1 | 3.261 | 3.261 | 1.626 | 1.626 | 9579284 | 9579284 | 290897920 | 290897920 |
| iso4014:M5x25 | step | 1 | ok | ok: 1 | 2.528 | 2.528 | 0.057 | 0.057 | 1308195 | 1308195 | 219574272 | 219574272 |
| iso4014:M7x40 | stl-preview | 1 | ok | ok: 1 | 2.251 | 2.251 | 0.205 | 0.205 | 1646684 | 1646684 | 224481280 | 224481280 |
| iso4014:M8x70 | stl-fine | 1 | ok | ok: 1 | 2.472 | 2.472 | 2.684 | 2.684 | 14707484 | 14707484 | 359919616 | 359919616 |
| iso4014:M12x60 | step | 1 | ok | ok: 1 | 2.362 | 2.362 | 0.051 | 0.051 | 1187156 | 1187156 | 222777344 | 222777344 |
| iso4014:M14x100 | stl-preview | 1 | ok | ok: 1 | 2.416 | 2.416 | 0.272 | 0.272 | 1835884 | 1835884 | 226885632 | 226885632 |
| iso4014:M16x140 | stl-fine | 1 | ok | ok: 1 | 2.615 | 2.615 | 6.882 | 6.882 | 38614184 | 38614184 | 626446336 | 626446336 |
| iso4014:M18x180 | step | 1 | ok | ok: 1 | 2.629 | 2.629 | 0.061 | 0.061 | 1368870 | 1368870 | 224567296 | 224567296 |
| iso4032:M3 | stl-preview | 1 | ok | ok: 1 | 2.599 | 2.599 | 0.036 | 0.036 | 215184 | 215184 | 214147072 | 214147072 |
| bolt-d1-p0.1-n3-left | stl-fine | 1 | ok | ok: 1 | 0.896 | 0.896 | 0.171 | 0.171 | 852784 | 852784 | 247279616 | 247279616 |
| bolt-d3-p0.1-n30-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d3-p1-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d10-p0.35-n240-left | stl-fine | 1 | ok | ok: 1 | 14.559 | 14.559 | 45.325 | 45.325 | 250093784 | 250093784 | 1017917440 | 1017917440 |
| bolt-d30-p0.1-n3-right | step | 1 | ok | ok: 1 | 2.291 | 2.291 | 0.024 | 0.024 | 446021 | 446021 | 210464768 | 210464768 |
| bolt-d30-p1-n30-right | stl-preview | 1 | ok | ok: 1 | 2.975 | 2.975 | 1.312 | 1.312 | 9731684 | 9731684 | 259018752 | 259018752 |
| bolt-d30-p10-n30-left | stl-fine | 1 | ok | ok: 1 | 2.108 | 2.108 | 13.698 | 13.698 | 63734184 | 63734184 | 815476736 | 815476736 |
| bolt-d100-p0.35-n240-right | step | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d100-p10-n3-right | stl-preview | 1 | ok | ok: 1 | 1.115 | 1.115 | 0.627 | 0.627 | 3696484 | 3696484 | 316727296 | 316727296 |
| bolt-d300-p0.35-n3-left | stl-fine | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d300-p3-n30-right | step | 1 | ok | ok: 1 | 2.979 | 2.979 | 0.125 | 0.125 | 2775496 | 2775496 | 251822080 | 251822080 |
| bolt-d1000-p0.1-n240-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| bolt-d1000-p1-n240-left | stl-fine | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| nut-d3-p0.35-m0.8d-s1.6d-c0.15-right | step | 1 | ok | ok: 1 | 2.983 | 2.983 | 0.035 | 0.035 | 737130 | 737130 | 230551552 | 230551552 |
| nut-d10-p1-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 2.830 | 2.830 | 0.117 | 0.117 | 640184 | 640184 | 226693120 | 226693120 |
| nut-d30-p0.35-m0.8d-s1.6d-c5-right | stl-fine | 1 | ok | ok: 1 | 10.986 | 10.986 | 73.206 | 73.206 | 377910084 | 377910084 | 1927860224 | 1927860224 |
| nut-d30-p3.5-m0.8d-s4d-c0.15-right | step | 1 | ok | ok: 1 | 2.461 | 2.461 | 0.045 | 0.045 | 919145 | 919145 | 211963904 | 211963904 |
| nut-d100-p3.5-m0.8d-s1.6d-c0.15-right | stl-preview | 1 | ok | ok: 1 | 6.426 | 6.426 | 3.715 | 3.715 | 23853184 | 23853184 | 408379392 | 408379392 |
| nut-d10-p0.35-m3d-s1.6d-c0.15-left | stl-fine | 1 | ok | ok: 1 | 12.996 | 12.996 | 16.248 | 16.248 | 86100384 | 86100384 | 591192064 | 591192064 |
| nut-d100-p3.5-m3d-s1.6d-c0.15-left | step | 1 | ok | ok: 1 | 13.653 | 13.653 | 0.281 | 0.281 | 6092328 | 6092328 | 261459968 | 261459968 |


### spread, run 40646125666

- Dispatched sha: `7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd`
- Records: `bench/results/phase-07/spread-40646125666/` (60 artifacts, 60 readings), run https://github.com/halfb00t/screw/actions/runs/40646125666
- CPU models seen (jobs): AMD EPYC 7763 64-Core Processor (33); AMD EPYC 9V45 96-Core Processor (12); AMD EPYC 9V74 80-Core Processor (9); INTEL(R) XEON(R) PLATINUM 8573C (3); Intel(R) Xeon(R) 6973P-C (1); Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz (2)
- Counts by status: ok: 60
- 12 shards x 5 repetitions = 60 jobs, 60 runner instances.
- Summary: `python -m bench.oper summarize --markdown --reps 1,2,3,4,5` over the directory, as printed.

### Host

| fact | value |
| --- | --- |
| image | screw:ci |
| image_id | sha256:0b263da9137c19e8db679fd185b47dfa31b3f882d824f75a463c866e4c2782dd, sha256:9a65d48ea1befe3b4df03b76c248456d433d98ea8c906371b94aa4d1e485e449, sha256:f409f5c4c43796acb69d6e167bd48311b387c4144a9525e314a195c0549756fe, sha256:9f241c1a2035fe7417a477910d35d299e6ededf5cbe1adbe77703003ffeb11b1, sha256:001b5bbe85aedad0175e2532d0b5ed25fc6994fa9b99a61e54196d0baaae7306, sha256:fc4ddbf5f835df4cd2c29132f41aa0c4aa82ec68afd863ae50a985d24031ee14, sha256:e78496ac67711ac32d4d9f56ec9dea4309bb3d24120f82e7c290806afe375e27, sha256:fd6385c2d3e6d2e87e478742e8c6d06f2b21ee9051740a65c67dcbf8ea5d6ce6, sha256:954339fcf9c0d2bb9805c02757ef35863975efaabea29cb33fdca80c442122e6, sha256:5ac0a8498d7a52acb7279e2c902e13e5a259268b1b28fb9646ccc0606c6a12f7, sha256:6fbe5264de9e09b818ce1f5edb91822b67d9e2c92c1df9f5dd7e8bdb47535af2, sha256:2ef533088f861efcc7c0db3748efd520eb58513de069ad920063b8c25e559c5d, sha256:486b2887633fc40f5f214df6c0cf8c429a041573febc1e615302ac22296bcb73, sha256:28b316400b530b6c870c1b2e0869697edc625b2f366baaebf6d42bbe759437d0, sha256:fde4567b015efeeb9c4314944480418012a00a960c41ab93725d3bf711c829f2, sha256:f3fc911aa3796fcc6b2b8307ba1dd9ea59be80a740b33c49334d0b8dbd54d1aa, sha256:f9fd3199b6b110b70ae937e85f35e472e0bf666cbe04816f122dea872bdd199f, sha256:3a22e1d17bdd1852546688a06e582138cb629b8d8511b10b36bd6e52a737d7ba, sha256:848db43b262bb2b1fec74306649b0da3532f751aed3b814fec99233f29585051, sha256:a2035213382c06592ab1ba0dad6a942454ff1a15f2e1b3ba0f65e459c93926e3, sha256:96c1bb431e1c380d2b748153e8581fca828c71669abf6ae14a3c592284a956cf, sha256:6e3454b695ba2f94310bb676632dde25ec709e18e171d281482862a2236bcc81, sha256:1d3356cace8c33e6b6e588118fc73269708cf5ae0805bee285253db120b33790, sha256:706e18c104fc364eb0d34983fc4f009efdba2ee7846484f6a461a4588e29fb75, sha256:86987b82855444b0b9919630023a9a45003bd164cb2e528b11a6bd62db0fe06f, sha256:f10bcd5803491fede3a26b39bf3e84a8b3867096904af4b644a5dfcfcd4cbaad, sha256:b7253b2136326f7f0c05ed43793b751faa2bf8343c3f7569407a0decc433eda0, sha256:fae6f31083e6c4a50f3a1f55ab0f0651dbf9c245ee8ac175156d782946a30d0a, sha256:7b91de3429b028cb5465aef743b2b3aaa34dc35abd915909ef1225217f075040, sha256:48cd52434eab21517010465b90bba4d4ca1e3360adbd3cc77d48430b8af94633, sha256:61c97173486f66dda392d993f277af5149c2068227d0e94e6d9f0fece52891ac, sha256:98359d70e675f2739a56d595d20a57e2c6c244be9e28cfbdd204b3202d904364, sha256:09240d540fa41fabbe492a3fe3a43166586b97fe86dd63b56ca36e8732431600, sha256:538e9c84231107ddb6e69e8f44a6e4b8f1f6307e97787de5de0117dccd445a77, sha256:719e3a551340827592a48782092b05b13f1772f8fef333db881811ed791db5e6, sha256:31ae44e13a732ef80ceb7ff0e9b4913320b544bab5a24a131c83c83319c744ab, sha256:05764427223c70bcf1aee87eb1f9bad10699093e1328d118b47f5ed4f1826ebf, sha256:9e8ea25ec43f3bfc85dbb0edf35410fcee1c6c3345705dcf434c7382e4377583, sha256:5c888b0ba35a4545920ba077ad5ffe11e21c61aa8c3e66c232ccf7a4274babfd, sha256:52640680654303bbbefe3610cae63737419f5ba0dec4f8f85315b625bc95ee4c, sha256:55131aace7c321449b675956ce0c73d9131f1a608128f8c6755ca305dda592ed, sha256:2923018fb0a65d3ed9ce6403c448f40cdb57d16b0d16a6c4d0d38827eaba4e81, sha256:0bf1540ceb47d19557e6721facdd62f2f504fac2e7ab1d3d22411af85db256f8, sha256:8f0b519644d5ea6cbdad6ff16f37c427abac222f421e1cf6d9ba0451e8d27f86, sha256:12a0c20160986c92cb7fd9f960666e678c6b72287b5d1210bd6303a1680530b2, sha256:d2966f8ffdb0013fc65a2bfe63521697fa219fa1fcce22541341a7ee8bffc477, sha256:c955712fc16b6b6ef8c2df504871cac3db539a18897c274c83c08876c95dfcd1, sha256:a4ed2b650e0b0bdd3e2f6599321fe23777a27251b18a768ad294d01d02dd8624, sha256:fadc52345d1ccbfc9d2bffc0cf2c85c7bb477d109165e086e5288a42f47aaec6, sha256:bfcf5685694517a245150b68255c9cd5590dd701b7b4271394b487ea0ad68dc2, sha256:cbf0ff34c30915a12cc0ab585522817d43c0f8dcf58fa6dbbe9a936a1e849264, sha256:a483c47ddcc7e53ee1bde05e37355d83a47ee3ca0dffa81102811562568764bf, sha256:2a6e038cec069c7934088ae675a62e700b0607f049962fec8743649fdf7156a3, sha256:c1945f01c3e94882df9488b37577768ec34d8fe300b5c02d2d92dc61d86aa7e5, sha256:54865b9d6e9c25df3c67344c143ec7940b71089a1082c2d48958c9becbfa335a, sha256:495312d8cddb36455063b7d5c2a1a3216b5971d41b963b1352b7de53ad4a8487, sha256:0f30f206007447732ae46cce2097591e5e45c2f8c313b68164beaf5a9e76949b, sha256:974de13e8bfeb8fbb283e6ba181c366dd073d77e08efbd2cb8dd46fe9823e524, sha256:a4a06381cf3a20835ee94f2804eb2ed8c8f2b6fed6a12bede6ca71479fd85bed, sha256:ee75111132b114e5a86ec90e821efe5a6f2c704eb56d1f86f1e6aa1a80974db2 |
| versions | {"cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"} |
| nproc | 4 |
| mem_total_bytes | 16759443456, 16759439360, 16758407168, 16759435264, 16758403072, 16759447552, 16763772928 |
| cpu_model | AMD EPYC 9V74 80-Core Processor, AMD EPYC 7763 64-Core Processor, INTEL(R) XEON(R) PLATINUM 8573C, AMD EPYC 9V45 96-Core Processor, Intel(R) Xeon(R) 6973P-C, Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz |
| kernel | 7.0.0-1017-azure |
| machine | x86_64 |
| GITHUB_RUN_ID | 40646125666 |
| GITHUB_JOB | measure |
| GITHUB_SHA | 7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd |

### Readings

Status counts: ok: 60

| point | artifact | n | status | counts | median build s | max build s | median export s | max export s | median bytes | max bytes | median peak bytes | max peak bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| default-bolt | stl-preview | 5 | ok | ok: 5 | 1.912 | 1.933 | 0.198 | 0.203 | 1587384 | 1587384 | 225107968 | 226328576 |
| iso4032:M20 | stl-preview | 5 | ok | ok: 5 | 2.484 | 2.783 | 0.178 | 0.238 | 1613384 | 1613384 | 230359040 | 232751104 |
| iso4032:M20 | stl-fine | 5 | ok | ok: 5 | 2.142 | 2.776 | 1.613 | 1.975 | 10583284 | 10583284 | 446205952 | 467415040 |
| iso4032:M20 | step | 5 | ok | ok: 5 | 2.226 | 2.767 | 0.034 | 0.042 | 880932 | 880932 | 213741568 | 215003136 |
| default-bolt | stl-fine | 5 | ok | ok: 5 | 1.931 | 1.939 | 2.060 | 2.197 | 10592984 | 10592984 | 335040512 | 351391744 |
| default-bolt | step | 5 | ok | ok: 5 | 1.893 | 2.025 | 0.056 | 0.061 | 1304431 | 1304431 | 222666752 | 225292288 |
| default-nut | stl-preview | 5 | ok | ok: 5 | 2.404 | 2.431 | 0.060 | 0.062 | 354384 | 354384 | 215183360 | 215519232 |
| default-nut | stl-fine | 5 | ok | ok: 5 | 2.419 | 2.434 | 0.493 | 0.721 | 2422184 | 2422184 | 288436224 | 295292928 |
| default-nut | step | 5 | ok | ok: 5 | 2.427 | 2.457 | 0.030 | 0.032 | 622442 | 622442 | 214913024 | 216489984 |
| iso4014:M20x200 | stl-preview | 5 | ok | ok: 5 | 2.789 | 2.841 | 0.809 | 0.838 | 6015484 | 6015484 | 249503744 | 251842560 |
| iso4014:M20x200 | stl-fine | 5 | ok | ok: 5 | 1.831 | 2.785 | 4.129 | 6.390 | 37736784 | 37736784 | 597176320 | 625803264 |
| iso4014:M20x200 | step | 5 | ok | ok: 5 | 2.758 | 2.792 | 0.063 | 0.069 | 1465962 | 1465962 | 225972224 | 226476032 |


### walls, run 40646134133

- Dispatched sha: `7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd`
- Records: `bench/results/phase-07/walls-40646134133/` (20 artifacts, 756 readings), run https://github.com/halfb00t/screw/actions/runs/40646134133
- CPU models seen (jobs): AMD EPYC 7763 64-Core Processor (8); AMD EPYC 9V45 96-Core Processor (7); AMD EPYC 9V74 80-Core Processor (2); INTEL(R) XEON(R) PLATINUM 8573C (2); Intel(R) Xeon(R) 6973P-C (1)
- Counts by status: capped: 2, crashed: 10, killed: 1, ok: 300, refused: 443
- 20 shards (R4), one repetition per point.
- Summary: `python -m bench.oper summarize --markdown --reps 1` over the directory, as printed.

### Host

| fact | value |
| --- | --- |
| image | screw:ci |
| image_id | sha256:b215ba3c0db23be234457116c51ba7cc56b3d54d8ea6ca4be7a97d99530cbbbb, sha256:fd7ac281219746c5498aa2bb9569bd581bfa21c671a728b0ff25984cb66b77bf, sha256:fcbd6e5c1c55ee96535252450f4c8b47ff4f7b1ce11a9464e3c09156089f78ab, sha256:94d5b3e0407021722c1b37849894362648427deb49db6ce7a8ca718b73e3874d, sha256:c072863ae7c88fc2874bc3bbfdc77d0099710cd486a4cd9f01c6e37138ac106b, sha256:768ec24ff81cb0aebe735b0f4b77484cd79c843bfd0381207a06add766a02fd9, sha256:2bf9b23b967f8054cfd219c348eaf7eec3793ddfeddd557c7dc29c2b5e905b43, sha256:a9627fca948270d19d32a73db70b7a232572fb969e5854057ca0620faf35d455, sha256:776feb5107ee37a9b75f8713dfcfa74f7465e32f05ad8c777141055526e3ec65, sha256:ce36b0b80025e27891ebe70f5a68c19c370229251b9a5f16329a50c0bdc59e58, sha256:1a03f1cc15e5f924ead42ec102ef9f68f1308a4a903390cf640956b43ab452fb, sha256:f947a6ab93a1a9cead9ffe1866fb8b56db624e8837d904bf75bdb85281a83184, sha256:62f58a4a4f0897b0ad92c5323b19c33c3e806699abcb8137fd4bba16a1409cad, sha256:22089475c46d1b95f428fe3c24b670d460f1fefd370a3caf263fc805ba16af20, sha256:f1edae9cfe59835db76d9b0b52870b7eb7c21526b495c7e1b5f894a6e7067094, sha256:862482d3a0817e38d81ae0bca3d3fee75a5dc733eea42da330b72f22cf052575, sha256:a76a7527c4af82093235996fda002d4d1624b1393d6406414150387f088b4093, sha256:78101851cc0b1484526db54f7432b9245f0911bb4aaf4238704e299ea56364c0, sha256:3e74dc41e3541fbd9957a03096748672ab67fdce5b37cad5f4378344e64665c8, sha256:e5317f1d0d80133475738f966569aff858b9c760b5ece3ceb46f7c9a6d0f6281 |
| versions | {"cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"} |
| nproc | 4 |
| mem_total_bytes | 16759439360, 16758403072, 16759443456, 16758407168 |
| cpu_model | AMD EPYC 9V45 96-Core Processor, Intel(R) Xeon(R) 6973P-C, AMD EPYC 7763 64-Core Processor, INTEL(R) XEON(R) PLATINUM 8573C, AMD EPYC 9V74 80-Core Processor |
| kernel | 7.0.0-1017-azure |
| machine | x86_64 |
| GITHUB_RUN_ID | 40646134133 |
| GITHUB_JOB | measure |
| GITHUB_SHA | 7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd |

### Readings

Status counts: refused: 443, ok: 300, crashed: 10, capped: 2, killed: 1

| point | artifact | n | status | counts | median build s | max build s | median export s | max export s | median bytes | max bytes | median peak bytes | max peak bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| turns-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M5-right | stl-preview | 1 | ok | ok: 1 | 8.708 | 8.708 | 1.430 | 1.430 | 18754484 | 18754484 | 423329792 | 423329792 |
| turns-bolt-M12-right | stl-preview | 1 | ok | ok: 1 | 8.709 | 8.709 | 1.855 | 1.855 | 24162184 | 24162184 | 448733184 | 448733184 |
| ceiling-bolt-d-1000 | stl-preview | 1 | ok | ok: 1 | 3.202 | 3.202 | 2.482 | 2.482 | 11841984 | 11841984 | 867311616 | 867311616 |
| ceiling-bolt-s-100000 | stl-preview | 1 | ok | ok: 1 | 1.227 | 1.227 | 0.320 | 0.320 | 2081184 | 2081184 | 259264512 | 259264512 |
| tail-d6-p1-left-1e-7 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-right-1e-3 | tail | 1 | ok | ok: 1 | 0.030 | 0.030 | - | - | - | - | 201502720 | 201502720 |
| root-nut-M2-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nutlead-M8-s100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M3.5-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M8-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M18-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M7-right | stl-preview | 1 | ok | ok: 1 | 18.471 | 18.471 | 1.610 | 1.610 | 20791984 | 20791984 | 344236032 | 344236032 |
| turns-nut-M16-right | stl-preview | 1 | ok | ok: 1 | 19.419 | 19.419 | 3.875 | 3.875 | 42799784 | 42799784 | 423190528 | 423190528 |
| ceiling-bolt-d-10000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d6-p1-right-1e-4 | tail | 1 | ok | ok: 1 | 0.035 | 0.035 | - | - | - | - | 201588736 | 201588736 |
| tail-d2-p0.4-right-1e-8 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-left-1e-4 | tail | 1 | ok | ok: 1 | 0.034 | 0.034 | - | - | - | - | 201625600 | 201625600 |
| root-bolt-M2-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.483 | 0.483 | 0.027 | 0.027 | 214084 | 214084 | 210833408 | 210833408 |
| root-bolt-M3-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.477 | 0.477 | 0.031 | 0.031 | 236584 | 236584 | 210956288 | 210956288 |
| root-bolt-M3-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.494 | 0.494 | 0.027 | 0.027 | 221484 | 221484 | 210968576 | 210968576 |
| root-bolt-M3.5-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.438 | 0.438 | 0.031 | 0.031 | 241784 | 241784 | 211423232 | 211423232 |
| root-bolt-M3.5-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.405 | 0.405 | 0.026 | 0.026 | 173684 | 173684 | 211251200 | 211251200 |
| root-bolt-M4-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.413 | 0.413 | 0.039 | 0.039 | 292684 | 292684 | 213331968 | 213331968 |
| root-bolt-M7-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.491 | 0.491 | 0.047 | 0.047 | 320484 | 320484 | 213991424 | 213991424 |
| root-bolt-M7-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.443 | 0.443 | 0.041 | 0.041 | 314584 | 314584 | 214614016 | 214614016 |
| root-bolt-M8-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.439 | 0.439 | 0.047 | 0.047 | 341184 | 341184 | 213819392 | 213819392 |
| root-bolt-M8-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.428 | 0.428 | 0.051 | 0.051 | 360784 | 360784 | 215003136 | 215003136 |
| root-bolt-M10-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.445 | 0.445 | 0.057 | 0.057 | 440084 | 440084 | 216682496 | 216682496 |
| root-bolt-M16-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.450 | 0.450 | 0.085 | 0.085 | 632584 | 632584 | 226664448 | 226664448 |
| root-bolt-M16-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.446 | 0.446 | 0.081 | 0.081 | 595884 | 595884 | 226033664 | 226033664 |
| root-bolt-M18-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.446 | 0.446 | 0.092 | 0.092 | 686184 | 686184 | 229044224 | 229044224 |
| root-bolt-M18-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.449 | 0.449 | 0.085 | 0.085 | 577784 | 577784 | 226856960 | 226856960 |
| root-bolt-M20-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M2-left (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M5-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M12-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-bolt-s-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M7-left | stl-preview | 1 | ok | ok: 1 | 13.447 | 13.447 | 2.422 | 2.422 | 16534084 | 16534084 | 439336960 | 439336960 |
| turns-bolt-M16-left | stl-preview | 1 | ok | ok: 1 | 13.936 | 13.936 | 6.415 | 6.415 | 38782284 | 38782284 | 492720128 | 492720128 |
| ceiling-bolt-length-10000 | stl-preview | 1 | ok | ok: 1 | 2.635 | 2.635 | 0.200 | 0.200 | 1610484 | 1610484 | 225824768 | 225824768 |
| tail-d6-p1-right-1e-5 | tail | 1 | ok | ok: 1 | 0.051 | 0.051 | - | - | - | - | 201555968 | 201555968 |
| tail-d2-p0.4-right-1e-9 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-left-1e-5 | tail | 1 | ok | ok: 1 | 0.050 | 0.050 | - | - | - | - | 201564160 | 201564160 |
| root-nut-M2-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M2-left (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M5-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M12-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-bolt-k-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M3-left | stl-preview | 1 | ok | ok: 1 | 48.820 | 48.820 | 1.225 | 1.225 | 9755084 | 9755084 | 541376512 | 541376512 |
| turns-nut-M7-left | stl-preview | 1 | ok | ok: 1 | 24.261 | 24.261 | 1.908 | 1.908 | 16563984 | 16563984 | 338509824 | 338509824 |
| turns-nut-M16-left | stl-preview | 1 | ok | ok: 1 | 24.910 | 24.910 | 5.856 | 5.856 | 41242484 | 41242484 | 411779072 | 411779072 |
| ceiling-bolt-s-10000 | stl-preview | 1 | ok | ok: 1 | 1.690 | 1.690 | 0.207 | 0.207 | 1741584 | 1741584 | 226062336 | 226062336 |
| tail-d6-p1-right-1e-6 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-left-1e-2 | tail | 1 | ok | ok: 1 | 0.039 | 0.039 | - | - | - | - | 201834496 | 201834496 |
| tail-d20-p2.5-left-1e-6 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.605 | 0.605 | 0.037 | 0.037 | 220684 | 220684 | 211550208 | 211550208 |
| root-bolt-M2.5-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.623 | 0.623 | 0.041 | 0.041 | 220784 | 220784 | 210563072 | 210563072 |
| root-bolt-M3-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.612 | 0.612 | 0.042 | 0.042 | 229384 | 229384 | 211046400 | 211046400 |
| root-bolt-M3-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.627 | 0.627 | 0.036 | 0.036 | 228984 | 228984 | 211103744 | 211103744 |
| root-bolt-M3.5-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.576 | 0.576 | 0.051 | 0.051 | 275334 | 275334 | 212582400 | 212582400 |
| root-bolt-M3.5-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.576 | 0.576 | 0.061 | 0.061 | 311284 | 311284 | 213753856 | 213753856 |
| root-bolt-M6-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.530 | 0.530 | 0.057 | 0.057 | 289584 | 289584 | 213671936 | 213671936 |
| root-bolt-M7-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.601 | 0.601 | 0.055 | 0.055 | 326884 | 326884 | 213880832 | 213880832 |
| root-bolt-M7-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.545 | 0.545 | 0.052 | 0.052 | 307584 | 307584 | 213581824 | 213581824 |
| root-bolt-M8-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.597 | 0.597 | 0.068 | 0.068 | 377434 | 377434 | 214405120 | 214405120 |
| root-bolt-M8-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.599 | 0.599 | 0.086 | 0.086 | 473684 | 473684 | 217219072 | 217219072 |
| root-bolt-M14-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.563 | 0.563 | 0.084 | 0.084 | 432684 | 432684 | 216272896 | 216272896 |
| root-bolt-M16-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.579 | 0.579 | 0.110 | 0.110 | 635584 | 635584 | 226996224 | 226996224 |
| root-bolt-M16-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.553 | 0.553 | 0.113 | 0.113 | 535784 | 535784 | 225734656 | 225734656 |
| root-bolt-M18-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.625 | 0.625 | 0.128 | 0.128 | 621484 | 621484 | 228339712 | 228339712 |
| root-bolt-M18-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M2.5-right (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M6-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M14-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-bolt-thread-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M3.5-right | stl-preview | 1 | ok | ok: 1 | 8.439 | 8.439 | 1.081 | 1.081 | 11562984 | 11562984 | 340348928 | 340348928 |
| turns-bolt-M8-right | stl-preview | 1 | ok | ok: 1 | 8.832 | 8.832 | 1.611 | 1.611 | 21190984 | 21190984 | 427855872 | 427855872 |
| turns-bolt-M18-right | stl-preview | 1 | ok | ok: 1 | 9.424 | 9.424 | 5.149 | 5.149 | 64069784 | 64069784 | 568905728 | 568905728 |
| ceiling-bolt-k-10000 | stl-preview | 1 | ok | ok: 1 | 1.289 | 1.289 | 0.125 | 0.125 | 1587384 | 1587384 | 224460800 | 224460800 |
| tail-d6-p1-right-1e-7 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-left-1e-3 | tail | 1 | ok | ok: 1 | 0.031 | 0.031 | - | - | - | - | 201535488 | 201535488 |
| tail-d20-p2.5-left-1e-7 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M2.5-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M6-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M14-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-nut-s-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M3.5-right | stl-preview | 1 | ok | ok: 1 | 21.603 | 21.603 | 1.222 | 1.222 | 12171984 | 12171984 | 331501568 | 331501568 |
| turns-nut-M8-right | stl-preview | 1 | ok | ok: 1 | 21.770 | 21.770 | 2.010 | 2.010 | 21433484 | 21433484 | 345198592 | 345198592 |
| turns-nut-M18-right | stl-preview | 1 | ok | ok: 1 | 22.402 | 22.402 | 5.982 | 5.982 | 65678784 | 65678784 | 475594752 | 475594752 |
| ceiling-bolt-thread-10000 | stl-preview | 1 | ok | ok: 1 | 8.430 | 8.430 | 23.510 | 23.510 | 234290784 | 234290784 | 909545472 | 909545472 |
| tail-d6-p1-right-1e-8 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-left-1e-4 | tail | 1 | ok | ok: 1 | 0.037 | 0.037 | - | - | - | - | 201498624 | 201498624 |
| tail-d20-p2.5-left-1e-8 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.536 | 0.536 | 0.031 | 0.031 | 206184 | 206184 | 209711104 | 209711104 |
| root-bolt-M2.5-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.538 | 0.538 | 0.033 | 0.033 | 228684 | 228684 | 210472960 | 210472960 |
| root-bolt-M2.5-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.558 | 0.558 | 0.032 | 0.032 | 219484 | 219484 | 210763776 | 210763776 |
| root-bolt-M3-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.549 | 0.549 | 0.038 | 0.038 | 229984 | 229984 | 210980864 | 210980864 |
| root-bolt-M3-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.570 | 0.570 | 0.026 | 0.026 | 159384 | 159384 | 210919424 | 210919424 |
| root-bolt-M3.5-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.475 | 0.475 | 0.043 | 0.043 | 278584 | 278584 | 212922368 | 212922368 |
| root-bolt-M6-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.492 | 0.492 | 0.048 | 0.048 | 303784 | 303784 | 213684224 | 213684224 |
| root-bolt-M6-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.469 | 0.469 | 0.046 | 0.046 | 291984 | 291984 | 214011904 | 214011904 |
| root-bolt-M7-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.508 | 0.508 | 0.053 | 0.053 | 327884 | 327884 | 213520384 | 213520384 |
| root-bolt-M7-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.486 | 0.486 | 0.061 | 0.061 | 350684 | 350684 | 215191552 | 215191552 |
| root-bolt-M8-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.499 | 0.499 | 0.065 | 0.065 | 384784 | 384784 | 216129536 | 216129536 |
| root-bolt-M14-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.517 | 0.517 | 0.073 | 0.073 | 476684 | 476684 | 217608192 | 217608192 |
| root-bolt-M14-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.496 | 0.496 | 0.071 | 0.071 | 435184 | 435184 | 217571328 | 217571328 |
| root-bolt-M16-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.528 | 0.528 | 0.106 | 0.106 | 572384 | 572384 | 226242560 | 226242560 |
| root-bolt-M16-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.514 | 0.514 | 0.102 | 0.102 | 534584 | 534584 | 225673216 | 225673216 |
| root-bolt-M18-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M2.5-left (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M6-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M14-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-nut-clearance-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M3.5-left | stl-preview | 1 | ok | ok: 1 | 9.688 | 9.688 | 1.135 | 1.135 | 9964184 | 9964184 | 334880768 | 334880768 |
| turns-bolt-M8-left | stl-preview | 1 | ok | ok: 1 | 10.173 | 10.173 | 1.735 | 1.735 | 17308284 | 17308284 | 435892224 | 435892224 |
| turns-bolt-M18-left | stl-preview | 1 | ok | ok: 1 | 10.819 | 10.819 | 6.786 | 6.786 | 52738884 | 52738884 | 551759872 | 551759872 |
| ceiling-nut-s-10000 | stl-preview | 1 | ok | ok: 1 | 1.739 | 1.739 | 0.075 | 0.075 | 587184 | 587184 | 223363072 | 223363072 |
| tail-d6-p1-right-1e-9 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-left-1e-5 | tail | 1 | ok | ok: 1 | 0.037 | 0.037 | - | - | - | - | 201621504 | 201621504 |
| tail-d20-p2.5-left-1e-9 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M2.5-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M6-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M14-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-nut-d-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M3.5-left | stl-preview | 1 | ok | ok: 1 | 26.916 | 26.916 | 1.660 | 1.660 | 11629284 | 11629284 | 331010048 | 331010048 |
| turns-nut-M8-left | stl-preview | 1 | ok | ok: 1 | 26.751 | 26.751 | 2.181 | 2.181 | 16916984 | 16916984 | 339296256 | 339296256 |
| turns-nut-M18-left | stl-preview | 1 | ok | ok: 1 | 27.845 | 27.845 | 7.213 | 7.213 | 52001784 | 52001784 | 441774080 | 441774080 |
| ceiling-nut-clearance-10000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d6-p1-left-1e-2 | tail | 1 | ok | ok: 1 | 0.047 | 0.047 | - | - | - | - | 201527296 | 201527296 |
| tail-d2-p0.4-left-1e-6 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.682 | 0.682 | 0.038 | 0.038 | 210684 | 210684 | 209686528 | 209686528 |
| root-bolt-M2-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.696 | 0.696 | 0.039 | 0.039 | 205384 | 205384 | 210255872 | 210255872 |
| root-bolt-M2.5-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.677 | 0.677 | 0.041 | 0.041 | 226084 | 226084 | 210735104 | 210735104 |
| root-bolt-M2.5-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.679 | 0.679 | 0.043 | 0.043 | 220584 | 220584 | 210460672 | 210460672 |
| root-bolt-M3-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.793 | 0.793 | 0.056 | 0.056 | 169884 | 169884 | 211386368 | 211386368 |
| root-bolt-M3-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.633 | 0.633 | 0.057 | 0.057 | 296384 | 296384 | 213192704 | 213192704 |
| root-bolt-M5-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.597 | 0.597 | 0.054 | 0.054 | 275584 | 275584 | 212819968 | 212819968 |
| root-bolt-M6-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.635 | 0.635 | 0.061 | 0.061 | 310284 | 310284 | 214196224 | 214196224 |
| root-bolt-M6-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.593 | 0.593 | 0.057 | 0.057 | 290384 | 290384 | 213368832 | 213368832 |
| root-bolt-M7-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.663 | 0.663 | 0.077 | 0.077 | 360934 | 360934 | 214573056 | 214573056 |
| root-bolt-M7-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.658 | 0.658 | 0.085 | 0.085 | 432084 | 432084 | 216920064 | 216920064 |
| root-bolt-M12-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.626 | 0.626 | 0.084 | 0.084 | 388384 | 388384 | 215883776 | 215883776 |
| root-bolt-M14-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.656 | 0.656 | 0.091 | 0.091 | 478684 | 478684 | 217010176 | 217010176 |
| root-bolt-M14-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.626 | 0.626 | 0.087 | 0.087 | 426584 | 426584 | 217309184 | 217309184 |
| root-bolt-M16-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.698 | 0.698 | 0.132 | 0.132 | 578784 | 578784 | 225812480 | 225812480 |
| root-bolt-M16-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nutlead-M2-s1000 | stl-preview | 1 | ok | ok: 1 | 5.753 | 5.753 | 0.170 | 0.170 | 1278084 | 1278084 | 231243776 | 231243776 |
| beyond-turns-bolt-M3-right (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M7-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M16-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-nut-m-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | capped | capped: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M4-right | stl-preview | 1 | ok | ok: 1 | 12.782 | 12.782 | 1.900 | 1.900 | 12976084 | 12976084 | 345124864 | 345124864 |
| turns-bolt-M10-right | stl-preview | 1 | ok | ok: 1 | 13.365 | 13.365 | 3.090 | 3.090 | 22555084 | 22555084 | 483770368 | 483770368 |
| turns-bolt-M20-right | stl-preview | 1 | ok | ok: 1 | 13.884 | 13.884 | 8.124 | 8.124 | 71887484 | 71887484 | 573460480 | 573460480 |
| ceiling-nut-d-10000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d6-p1-left-1e-3 | tail | 1 | ok | ok: 1 | 0.050 | 0.050 | - | - | - | - | 201822208 | 201822208 |
| tail-d2-p0.4-left-1e-7 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nutlead-M2-s10000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M3-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M7-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M16-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M4-right | stl-preview | 1 | ok | ok: 1 | 17.844 | 17.844 | 1.166 | 1.166 | 15652384 | 15652384 | 336891904 | 336891904 |
| turns-nut-M10-right | stl-preview | 1 | ok | ok: 1 | 17.466 | 17.466 | 1.678 | 1.678 | 22389884 | 22389884 | 346152960 | 346152960 |
| turns-nut-M20-right | stl-preview | 1 | ok | ok: 1 | 17.779 | 17.779 | 4.513 | 4.513 | 71378084 | 71378084 | 489103360 | 489103360 |
| ceiling-nut-m-10000 | stl-preview | 1 | ok | ok: 1 | 15.767 | 15.767 | 24.735 | 24.735 | 298660684 | 298660684 | 1089880064 | 1089880064 |
| tail-d6-p1-left-1e-4 | tail | 1 | ok | ok: 1 | 0.035 | 0.035 | - | - | - | - | 201527296 | 201527296 |
| tail-d2-p0.4-left-1e-8 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.439 | 0.439 | 0.025 | 0.025 | 211984 | 211984 | 209973248 | 209973248 |
| root-bolt-M2-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.440 | 0.440 | 0.026 | 0.026 | 207384 | 207384 | 210190336 | 210190336 |
| root-bolt-M2.5-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.426 | 0.426 | 0.027 | 0.027 | 225284 | 225284 | 210657280 | 210657280 |
| root-bolt-M2.5-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.441 | 0.441 | 0.022 | 0.022 | 152584 | 152584 | 210227200 | 210227200 |
| root-bolt-M3-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.374 | 0.374 | 0.040 | 0.040 | 262384 | 262384 | 212217856 | 212217856 |
| root-bolt-M5-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.389 | 0.389 | 0.036 | 0.036 | 291784 | 291784 | 213045248 | 213045248 |
| root-bolt-M5-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.374 | 0.374 | 0.034 | 0.034 | 273984 | 273984 | 213008384 | 213008384 |
| root-bolt-M6-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.387 | 0.387 | 0.038 | 0.038 | 301184 | 301184 | 213630976 | 213630976 |
| root-bolt-M6-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.366 | 0.366 | 0.032 | 0.032 | 228584 | 228584 | 213348352 | 213348352 |
| root-bolt-M7-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.390 | 0.390 | 0.050 | 0.050 | 356184 | 356184 | 215007232 | 215007232 |
| root-bolt-M12-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.419 | 0.419 | 0.055 | 0.055 | 420984 | 420984 | 216461312 | 216461312 |
| root-bolt-M12-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.399 | 0.399 | 0.061 | 0.061 | 391384 | 391384 | 216535040 | 216535040 |
| root-bolt-M14-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.405 | 0.405 | 0.060 | 0.060 | 468784 | 468784 | 217071616 | 217071616 |
| root-bolt-M14-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.395 | 0.395 | 0.055 | 0.055 | 368984 | 368984 | 216494080 | 216494080 |
| root-bolt-M16-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.421 | 0.421 | 0.085 | 0.085 | 653484 | 653484 | 229699584 | 229699584 |
| nutlead-M2-s100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M3-left (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M7-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M16-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M4-left | stl-preview | 1 | ok | ok: 1 | 12.626 | 12.626 | 1.816 | 1.816 | 12063784 | 12063784 | 342937600 | 342937600 |
| turns-bolt-M10-left | stl-preview | 1 | ok | ok: 1 | 13.354 | 13.354 | 2.569 | 2.569 | 18293984 | 18293984 | 424583168 | 424583168 |
| turns-bolt-M20-left | stl-preview | 1 | ok | ok: 1 | 13.819 | 13.819 | 6.425 | 6.425 | 55560284 | 55560284 | 555372544 | 555372544 |
| ceiling-bolt-d-100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d6-p1-left-1e-5 | tail | 1 | ok | ok: 1 | 0.050 | 0.050 | - | - | - | - | 201515008 | 201515008 |
| tail-d2-p0.4-left-1e-9 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nutlead-M8-s1000 | stl-preview | 1 | ok | ok: 1 | 4.701 | 4.701 | 0.338 | 0.338 | 2682484 | 2682484 | 231579648 | 231579648 |
| beyond-turns-nut-M3-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M7-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M16-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M5-right | stl-preview | 1 | ok | ok: 1 | 17.559 | 17.559 | 1.360 | 1.360 | 18774284 | 18774284 | 342728704 | 342728704 |
| turns-nut-M12-right | stl-preview | 1 | ok | ok: 1 | 17.811 | 17.811 | 1.866 | 1.866 | 23752384 | 23752384 | 384999424 | 384999424 |
| ceiling-bolt-length-1000 | stl-preview | 1 | ok | ok: 1 | 1.732 | 1.732 | 0.116 | 0.116 | 1610484 | 1610484 | 224768000 | 224768000 |
| ceiling-bolt-k-100000 | stl-preview | 1 | ok | ok: 1 | 1.290 | 1.290 | 0.122 | 0.122 | 1587384 | 1587384 | 224649216 | 224649216 |
| tail-d6-p1-left-1e-8 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-right-1e-4 | tail | 1 | ok | ok: 1 | 0.030 | 0.030 | - | - | - | - | 201584640 | 201584640 |
| root-bolt-M2-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.423 | 0.423 | 0.024 | 0.024 | 212784 | 212784 | 209776640 | 209776640 |
| root-bolt-M2-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.439 | 0.439 | 0.020 | 0.020 | 145484 | 145484 | 209731584 | 209731584 |
| root-bolt-M2.5-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.361 | 0.361 | 0.030 | 0.030 | 234384 | 234384 | 211214336 | 211214336 |
| root-bolt-M4-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.397 | 0.397 | 0.035 | 0.035 | 267584 | 267584 | 212197376 | 212197376 |
| root-bolt-M4-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.377 | 0.377 | 0.034 | 0.034 | 262284 | 262284 | 212508672 | 212508672 |
| root-bolt-M5-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.386 | 0.386 | 0.038 | 0.038 | 291384 | 291384 | 212873216 | 212873216 |
| root-bolt-M5-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.387 | 0.387 | 0.044 | 0.044 | 318184 | 318184 | 213893120 | 213893120 |
| root-bolt-M6-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.385 | 0.385 | 0.042 | 0.042 | 317084 | 317084 | 214081536 | 214081536 |
| root-bolt-M10-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.420 | 0.420 | 0.051 | 0.051 | 384384 | 384384 | 215162880 | 215162880 |
| root-bolt-M10-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.406 | 0.406 | 0.049 | 0.049 | 356884 | 356884 | 214560768 | 214560768 |
| root-bolt-M12-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.402 | 0.402 | 0.061 | 0.061 | 427334 | 427334 | 217059328 | 217059328 |
| root-bolt-M14-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.424 | 0.424 | 0.100 | 0.100 | 628184 | 628184 | 226865152 | 226865152 |
| root-bolt-M20-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.439 | 0.439 | 0.099 | 0.099 | 717784 | 717784 | 231247872 | 231247872 |
| root-bolt-M20-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.403 | 0.403 | 0.095 | 0.095 | 643084 | 643084 | 229322752 | 229322752 |
| nutlead-M14-s1000 | stl-preview | 1 | ok | ok: 1 | 2.939 | 2.939 | 0.203 | 0.203 | 2456684 | 2456684 | 225615872 | 225615872 |
| beyond-turns-bolt-M3.5-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M8-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M18-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M4-left | stl-preview | 1 | ok | ok: 1 | 26.882 | 26.882 | 1.858 | 1.858 | 13656084 | 13656084 | 332746752 | 332746752 |
| turns-nut-M10-left | stl-preview | 1 | ok | ok: 1 | 26.757 | 26.757 | 2.448 | 2.448 | 18279784 | 18279784 | 340045824 | 340045824 |
| turns-nut-M20-left | stl-preview | 1 | ok | ok: 1 | 27.442 | 27.442 | 6.698 | 6.698 | 55107584 | 55107584 | 451510272 | 451510272 |
| ceiling-bolt-length-100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d6-p1-left-1e-6 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-right-1e-2 | tail | 1 | ok | ok: 1 | 0.045 | 0.045 | - | - | - | - | 201588736 | 201588736 |
| root-bolt-M2-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.679 | 0.679 | 0.042 | 0.042 | 213984 | 213984 | 211271680 | 211271680 |
| root-bolt-M2-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.675 | 0.675 | 0.040 | 0.040 | 212584 | 212584 | 209715200 | 209715200 |
| root-bolt-M2.5-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.690 | 0.690 | 0.036 | 0.036 | 162384 | 162384 | 210223104 | 210223104 |
| root-bolt-M2.5-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M4-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.631 | 0.631 | 0.052 | 0.052 | 268584 | 268584 | 212369408 | 212369408 |
| root-bolt-M4-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.591 | 0.591 | 0.051 | 0.051 | 265984 | 265984 | 212410368 | 212410368 |
| root-bolt-M5-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.622 | 0.622 | 0.057 | 0.057 | 290484 | 290484 | 212922368 | 212922368 |
| root-bolt-M5-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.579 | 0.579 | 0.054 | 0.054 | 282584 | 282584 | 213028864 | 213028864 |
| root-bolt-M6-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M10-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.649 | 0.649 | 0.078 | 0.078 | 389984 | 389984 | 215465984 | 215465984 |
| root-bolt-M10-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.634 | 0.634 | 0.079 | 0.079 | 359684 | 359684 | 214671360 | 214671360 |
| root-bolt-M12-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.651 | 0.651 | 0.085 | 0.085 | 423184 | 423184 | 216215552 | 216215552 |
| root-bolt-M12-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.605 | 0.605 | 0.071 | 0.071 | 319984 | 319984 | 215740416 | 215740416 |
| root-bolt-M14-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.673 | 0.673 | 0.091 | 0.091 | 410584 | 410584 | 216330240 | 216330240 |
| root-bolt-M14-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M20-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.698 | 0.698 | 0.150 | 0.150 | 723484 | 723484 | 230084608 | 230084608 |
| root-bolt-M20-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.680 | 0.680 | 0.135 | 0.135 | 647284 | 647284 | 229081088 | 229081088 |
| nutlead-M8-s10000 | stl-preview | 1 | ok | ok: 1 | 4.727 | 4.727 | 0.372 | 0.372 | 2804284 | 2804284 | 231702528 | 231702528 |
| beyond-turns-bolt-M3.5-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M8-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M18-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M5-left | stl-preview | 1 | ok | ok: 1 | 8.524 | 8.524 | 1.186 | 1.186 | 14810984 | 14810984 | 428236800 | 428236800 |
| turns-bolt-M12-left | stl-preview | 1 | ok | ok: 1 | 8.575 | 8.575 | 1.580 | 1.580 | 19866784 | 19866784 | 432050176 | 432050176 |
| ceiling-bolt-s-1000 | stl-preview | 1 | ok | ok: 1 | 1.209 | 1.209 | 0.119 | 0.119 | 1634784 | 1634784 | 223457280 | 223457280 |
| ceiling-bolt-thread-100000 | stl-preview | 1 | ok | ok: 1 | 6.364 | 6.364 | 325.534 | 325.534 | 1713047584 | 1713047584 | 5777043456 | 5777043456 |
| tail-d6-p1-left-1e-9 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-right-1e-5 | tail | 1 | ok | ok: 1 | 0.031 | 0.031 | - | - | - | - | 201515008 | 201515008 |
| root-nut-M2-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nutlead-M14-s10000 | stl-preview | 1 | ok | ok: 1 | 2.854 | 2.854 | 0.221 | 0.221 | 2581484 | 2581484 | 230514688 | 230514688 |
| beyond-turns-nut-M3.5-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M8-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M18-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M5-left | stl-preview | 1 | ok | ok: 1 | 17.279 | 17.279 | 1.084 | 1.084 | 14947584 | 14947584 | 337952768 | 337952768 |
| turns-nut-M12-left | stl-preview | 1 | ok | ok: 1 | 17.789 | 17.789 | 1.578 | 1.578 | 19963984 | 19963984 | 363454464 | 363454464 |
| ceiling-bolt-k-1000 | stl-preview | 1 | ok | ok: 1 | 1.259 | 1.259 | 0.118 | 0.118 | 1587384 | 1587384 | 224722944 | 224722944 |
| ceiling-nut-s-100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-right-1e-2 | tail | 1 | ok | ok: 1 | 0.029 | 0.029 | - | - | - | - | 201519104 | 201519104 |
| tail-d20-p2.5-right-1e-6 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.436 | 0.436 | 0.022 | 0.022 | 152784 | 152784 | 210239488 | 210239488 |
| root-bolt-M2-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3.5-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.385 | 0.385 | 0.029 | 0.029 | 236284 | 236284 | 211013632 | 211013632 |
| root-bolt-M3.5-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.364 | 0.364 | 0.029 | 0.029 | 233684 | 233684 | 211161088 | 211161088 |
| root-bolt-M4-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.415 | 0.415 | 0.033 | 0.033 | 266784 | 266784 | 212824064 | 212824064 |
| root-bolt-M4-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.354 | 0.354 | 0.032 | 0.032 | 261184 | 261184 | 212963328 | 212963328 |
| root-bolt-M5-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.397 | 0.397 | 0.041 | 0.041 | 330184 | 330184 | 213913600 | 213913600 |
| root-bolt-M5-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M8-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.456 | 0.456 | 0.048 | 0.048 | 346284 | 346284 | 214085632 | 214085632 |
| root-bolt-M8-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.400 | 0.400 | 0.045 | 0.045 | 323384 | 323384 | 214224896 | 214224896 |
| root-bolt-M10-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.407 | 0.407 | 0.051 | 0.051 | 388784 | 388784 | 215228416 | 215228416 |
| root-bolt-M10-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.378 | 0.378 | 0.049 | 0.049 | 356684 | 356684 | 215019520 | 215019520 |
| root-bolt-M12-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.424 | 0.424 | 0.053 | 0.053 | 358884 | 358884 | 215654400 | 215654400 |
| root-bolt-M12-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M18-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.449 | 0.449 | 0.094 | 0.094 | 684184 | 684184 | 228761600 | 228761600 |
| root-bolt-M18-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.432 | 0.432 | 0.089 | 0.089 | 625984 | 625984 | 227954688 | 227954688 |
| root-bolt-M20-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.421 | 0.421 | 0.100 | 0.100 | 723284 | 723284 | 229855232 | 229855232 |
| root-bolt-M20-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.402 | 0.402 | 0.095 | 0.095 | 658834 | 658834 | 229543936 | 229543936 |
| nutlead-M14-s100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M4-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M10-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M20-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M6-right | stl-preview | 1 | ok | ok: 1 | 13.337 | 13.337 | 2.832 | 2.832 | 20203784 | 20203784 | 406790144 | 406790144 |
| turns-bolt-M14-right | stl-preview | 1 | ok | ok: 1 | 13.714 | 13.714 | 3.687 | 3.687 | 25549884 | 25549884 | 490106880 | 490106880 |
| ceiling-bolt-thread-1000 | stl-preview | 1 | ok | ok: 1 | 15.262 | 15.262 | 2.796 | 2.796 | 21419484 | 21419484 | 423018496 | 423018496 |
| ceiling-nut-clearance-100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-right-1e-3 | tail | 1 | ok | ok: 1 | 0.046 | 0.046 | - | - | - | - | 201342976 | 201342976 |
| tail-d20-p2.5-right-1e-7 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nutcsk-d2-s4-m3-c0.05-p1.5 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M4-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M10-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M20-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M2.5-right | stl-preview | 1 | ok | ok: 1 | 56.827 | 56.827 | 1.489 | 1.489 | 10498384 | 10498384 | 667594752 | 667594752 |
| turns-nut-M6-right | stl-preview | 1 | ok | ok: 1 | 26.963 | 26.963 | 2.471 | 2.471 | 20399984 | 20399984 | 345100288 | 345100288 |
| turns-nut-M14-right | stl-preview | 1 | ok | ok: 1 | 27.486 | 27.486 | 3.791 | 3.791 | 25431684 | 25431684 | 353316864 | 353316864 |
| ceiling-nut-s-1000 | stl-preview | 1 | ok | ok: 1 | 2.133 | 2.133 | 0.063 | 0.063 | 426384 | 426384 | 214958080 | 214958080 |
| ceiling-nut-d-100000 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-right-1e-4 | tail | 1 | ok | ok: 1 | 0.050 | 0.050 | - | - | - | - | 201551872 | 201551872 |
| tail-d20-p2.5-right-1e-8 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.709 | 0.709 | 0.043 | 0.043 | 220284 | 220284 | 210857984 | 210857984 |
| root-bolt-M3.5-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.642 | 0.642 | 0.048 | 0.048 | 243284 | 243284 | 211947520 | 211947520 |
| root-bolt-M3.5-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.585 | 0.585 | 0.046 | 0.046 | 232484 | 232484 | 211566592 | 211566592 |
| root-bolt-M4-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.618 | 0.618 | 0.054 | 0.054 | 267884 | 267884 | 212508672 | 212508672 |
| root-bolt-M4-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.597 | 0.597 | 0.049 | 0.049 | 200584 | 200584 | 212602880 | 212602880 |
| root-bolt-M5-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.621 | 0.621 | 0.067 | 0.067 | 313084 | 313084 | 213970944 | 213970944 |
| root-bolt-M8-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.656 | 0.656 | 0.074 | 0.074 | 334284 | 334284 | 213934080 | 213934080 |
| root-bolt-M8-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.626 | 0.626 | 0.068 | 0.068 | 319484 | 319484 | 214437888 | 214437888 |
| root-bolt-M10-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.638 | 0.638 | 0.079 | 0.079 | 392384 | 392384 | 215117824 | 215117824 |
| root-bolt-M10-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.637 | 0.637 | 0.092 | 0.092 | 396984 | 396984 | 215715840 | 215715840 |
| root-bolt-M12-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-left-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.653 | 0.653 | 0.134 | 0.134 | 593084 | 593084 | 225509376 | 225509376 |
| root-bolt-M18-right-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.703 | 0.703 | 0.150 | 0.150 | 684884 | 684884 | 229052416 | 229052416 |
| root-bolt-M18-left-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.688 | 0.688 | 0.189 | 0.189 | 619784 | 619784 | 226869248 | 226869248 |
| root-bolt-M20-right-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.665 | 0.665 | 0.153 | 0.153 | 717134 | 717134 | 230379520 | 230379520 |
| root-bolt-M20-left-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.661 | 0.661 | 0.142 | 0.142 | 588584 | 588584 | 228864000 | 228864000 |
| nutcsk-d2-s4-m3-c0.05-p1.8 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M4-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M10-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M20-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M2.5-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M6-left | stl-preview | 1 | ok | ok: 1 | 8.930 | 8.930 | 1.167 | 1.167 | 15942184 | 15942184 | 400293888 | 400293888 |
| turns-bolt-M14-left | stl-preview | 1 | ok | ok: 1 | 8.892 | 8.892 | 1.940 | 1.940 | 21379784 | 21379784 | 467775488 | 467775488 |
| ceiling-nut-clearance-1000 | stl-preview | 1 | ok | ok: 1 | 3.236 | 3.236 | 39.104 | 39.104 | 102733434 | 102733434 | 6399807488 | 6399807488 |
| ceiling-nut-m-100000 | stl-preview | 1 | killed | killed: 1 | - | - | - | - | - | - | - | - |
| tail-d2-p0.4-right-1e-5 | tail | 1 | ok | ok: 1 | 0.031 | 0.031 | - | - | - | - | 201474048 | 201474048 |
| tail-d20-p2.5-right-1e-9 | tail | 1 | crashed | crashed: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-left-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| nutcsk-d2-s4-m3-c0.01-p1.5 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M4-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M10-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M20-left (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| turns-nut-M2.5-left | stl-preview | 1 | ok | ok: 1 | 56.659 | 56.659 | 1.294 | 1.294 | 8921284 | 8921284 | 663425024 | 663425024 |
| turns-nut-M6-left | stl-preview | 1 | ok | ok: 1 | 27.180 | 27.180 | 1.981 | 1.981 | 15980484 | 15980484 | 336130048 | 336130048 |
| turns-nut-M14-left | stl-preview | 1 | ok | ok: 1 | 27.761 | 27.761 | 3.628 | 3.628 | 21421284 | 21421284 | 346505216 | 346505216 |
| ceiling-nut-d-1000 | stl-preview | 1 | ok | ok: 1 | 4.994 | 4.994 | 103.803 | 103.803 | 116766334 | 116766334 | 12663300096 | 12663300096 |
| tail-d6-p1-right-1e-2 | tail | 1 | ok | ok: 1 | 0.047 | 0.047 | - | - | - | - | 201768960 | 201768960 |
| tail-d2-p0.4-right-1e-6 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-left-1e-2 | tail | 1 | ok | ok: 1 | 0.045 | 0.045 | - | - | - | - | 201818112 | 201818112 |
| root-bolt-M2-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M2.5-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M3-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.697 | 0.697 | 0.045 | 0.045 | 234184 | 234184 | 211595264 | 211595264 |
| root-bolt-M3-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.708 | 0.708 | 0.043 | 0.043 | 221684 | 221684 | 210509824 | 210509824 |
| root-bolt-M3.5-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.627 | 0.627 | 0.049 | 0.049 | 249284 | 249284 | 212008960 | 212008960 |
| root-bolt-M3.5-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.599 | 0.599 | 0.046 | 0.046 | 233884 | 233884 | 211746816 | 211746816 |
| root-bolt-M4-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.629 | 0.629 | 0.066 | 0.066 | 304184 | 304184 | 213573632 | 213573632 |
| root-bolt-M4-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M5-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M6-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M7-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.650 | 0.650 | 0.070 | 0.070 | 321784 | 321784 | 213639168 | 213639168 |
| root-bolt-M7-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.613 | 0.613 | 0.063 | 0.063 | 307584 | 307584 | 214065152 | 214065152 |
| root-bolt-M8-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.645 | 0.645 | 0.070 | 0.070 | 335384 | 335384 | 213876736 | 213876736 |
| root-bolt-M8-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.602 | 0.602 | 0.069 | 0.069 | 327884 | 327884 | 214556672 | 214556672 |
| root-bolt-M10-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.667 | 0.667 | 0.089 | 0.089 | 424734 | 424734 | 216240128 | 216240128 |
| root-bolt-M10-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M12-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M14-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-bolt-M16-right-r0.01 | stl-preview | 1 | ok | ok: 1 | 0.678 | 0.678 | 0.135 | 0.135 | 642584 | 642584 | 227082240 | 227082240 |
| root-bolt-M16-left-r0.003 | stl-preview | 1 | ok | ok: 1 | 0.650 | 0.650 | 0.136 | 0.136 | 598884 | 598884 | 225738752 | 225738752 |
| root-bolt-M18-right-r0.001 | stl-preview | 1 | ok | ok: 1 | 0.662 | 0.662 | 0.147 | 0.147 | 690484 | 690484 | 229052416 | 229052416 |
| root-bolt-M18-left-r0.0003 | stl-preview | 1 | ok | ok: 1 | 0.655 | 0.655 | 0.146 | 0.146 | 632984 | 632984 | 228253696 | 228253696 |
| root-bolt-M20-right-r0.0001 | stl-preview | 1 | ok | ok: 1 | 0.683 | 0.683 | 0.156 | 0.156 | 655584 | 655584 | 229289984 | 229289984 |
| root-bolt-M20-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M2-right (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M5-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-bolt-M12-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-bolt-d-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns-bolt-M7-right | stl-preview | 1 | ok | ok: 1 | 11.010 | 11.010 | 1.858 | 1.858 | 20846084 | 20846084 | 440557568 | 440557568 |
| turns-bolt-M16-right | stl-preview | 1 | ok | ok: 1 | 11.349 | 11.349 | 4.551 | 4.551 | 41376184 | 41376184 | 513839104 | 513839104 |
| ceiling-nut-m-1000 | stl-preview | 1 | ok | ok: 1 | 24.713 | 24.713 | 2.443 | 2.443 | 26157184 | 26157184 | 347422720 | 347422720 |
| tail-d6-p1-right-1e-3 | tail | 1 | ok | ok: 1 | 0.039 | 0.039 | - | - | - | - | 201695232 | 201695232 |
| tail-d2-p0.4-right-1e-7 | tail | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| tail-d20-p2.5-left-1e-3 | tail | 1 | ok | ok: 1 | 0.038 | 0.038 | - | - | - | - | 201601024 | 201601024 |
| root-nut-M2-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M2.5-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M3.5-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M4-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M5-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M6-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M7-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M8-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M10-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-right-r1e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M12-left-r3e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M14-right-r1e-06 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-right-r0.01 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M16-left-r0.003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-right-r0.001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M18-left-r0.0003 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-right-r0.0001 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| root-nut-M20-left-r3e-05 | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M2-right (lift {"max_turns": 260}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M5-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-turns-nut-M12-right (lift {"max_turns": 260}) | stl-preview | 1 | ok | ok: 1 | - | - | - | - | - | - | - | - |
| beyond-bolt-length-1000000 (lift {"max_mm": 1000000.0}) | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |


### controls, run 40646142406

- Dispatched sha: `7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd`
- Records: `bench/results/phase-07/controls-40646142406/` (4 artifacts, 69 readings), run https://github.com/halfb00t/screw/actions/runs/40646142406
- CPU models seen (jobs): AMD EPYC 9V74 80-Core Processor (3); INTEL(R) XEON(R) PLATINUM 8573C (1)
- Counts by status: ok: 53, refused: 16
- 4 shards (R4), one repetition per point. Probes carry solids, valid and volume_ratio, and no export (R2).
- Summary: `python -m bench.oper summarize --markdown --reps 1` over the directory, as printed.

### Host

| fact | value |
| --- | --- |
| image | screw:ci |
| image_id | sha256:f2b19f1ada8265a0b3033ef459f26878c59cfa6ef8ab1c679bd22138927d6c54, sha256:60e2520859827f77ad136597dfe3c0379cd4e9b3831c3b0af5aace2926e8132b, sha256:2f86f419cd1b262d229f885a8b4597e4b015a1800c024f75166ef93f88161915, sha256:26b4617e719501cc1b5ed5615257d04c33191f347b7e8d27443924e6310b8409 |
| versions | {"cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"} |
| nproc | 4 |
| mem_total_bytes | 16759443456, 16758403072, 16759439360 |
| cpu_model | AMD EPYC 9V74 80-Core Processor, INTEL(R) XEON(R) PLATINUM 8573C |
| kernel | 7.0.0-1017-azure |
| machine | x86_64 |
| GITHUB_RUN_ID | 40646142406 |
| GITHUB_JOB | measure |
| GITHUB_SHA | 7e7d7e6ed6b9a8ca3b8b5e7b9012b90e1391a4dd |

### Readings

Status counts: ok: 53, refused: 16

| point | artifact | n | status | counts | median build s | max build s | median export s | max export s | median bytes | max bytes | median peak bytes | max peak bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| naive-M2-L4 | naive | 1 | ok | ok: 1 | 0.411 | 0.411 | - | - | - | - | 222814208 | 222814208 |
| one_pipe-M2-t100 | one_pipe | 1 | ok | ok: 1 | 0.188 | 0.188 | - | - | - | - | 205643776 | 205643776 |
| naive-M2.5-L4.5 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M2.5-t55.5556 | one_pipe | 1 | ok | ok: 1 | 0.116 | 0.116 | - | - | - | - | 202436608 | 202436608 |
| one_pipe-M2.5-t250 | one_pipe | 1 | ok | ok: 1 | 0.632 | 0.632 | - | - | - | - | 210116608 | 210116608 |
| naive-M3-L30 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M3-t200 | one_pipe | 1 | ok | ok: 1 | 0.360 | 0.360 | - | - | - | - | 207638528 | 207638528 |
| naive-M6-L60 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M6-t200 | one_pipe | 1 | ok | ok: 1 | 0.357 | 0.357 | - | - | - | - | 207679488 | 207679488 |
| naive-M8-L20 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M8-t160 | one_pipe | 1 | ok | ok: 1 | 0.312 | 0.312 | - | - | - | - | 207527936 | 207527936 |
| naive-M10-L15 | naive | 1 | ok | ok: 1 | 0.511 | 0.511 | - | - | - | - | 224989184 | 224989184 |
| one_pipe-M10-t100 | one_pipe | 1 | ok | ok: 1 | 0.194 | 0.194 | - | - | - | - | 205996032 | 205996032 |
| naive-M16-L10 | naive | 1 | ok | ok: 1 | 0.331 | 0.331 | - | - | - | - | 214798336 | 214798336 |
| one_pipe-M16-t100 | one_pipe | 1 | ok | ok: 1 | 0.200 | 0.200 | - | - | - | - | 206036992 | 206036992 |
| naive-M20-L10 | naive | 1 | ok | ok: 1 | 0.263 | 0.263 | - | - | - | - | 215040000 | 215040000 |
| one_pipe-M20-t80 | one_pipe | 1 | ok | ok: 1 | 0.183 | 0.183 | - | - | - | - | 205815808 | 205815808 |
| one_pipe-M20-t250 | one_pipe | 1 | ok | ok: 1 | 0.754 | 0.754 | - | - | - | - | 210608128 | 210608128 |
| naive-M2-L10 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M2-t160 | one_pipe | 1 | ok | ok: 1 | 0.233 | 0.233 | - | - | - | - | 206311424 | 206311424 |
| naive-M2.5-L10 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M2.5-t100 | one_pipe | 1 | ok | ok: 1 | 0.197 | 0.197 | - | - | - | - | 206336000 | 206336000 |
| naive-M3-L5 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M3-t60 | one_pipe | 1 | ok | ok: 1 | 0.110 | 0.110 | - | - | - | - | 202584064 | 202584064 |
| one_pipe-M3-t250 | one_pipe | 1 | ok | ok: 1 | 0.625 | 0.625 | - | - | - | - | 209850368 | 209850368 |
| one_pipe-M6-t60 | one_pipe | 1 | ok | ok: 1 | 0.112 | 0.112 | - | - | - | - | 202514432 | 202514432 |
| one_pipe-M6-t250 | one_pipe | 1 | ok | ok: 1 | 0.634 | 0.634 | - | - | - | - | 210178048 | 210178048 |
| naive-M8-L80 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M8-t200 | one_pipe | 1 | ok | ok: 1 | 0.362 | 0.362 | - | - | - | - | 208019456 | 208019456 |
| naive-M10-L20 | naive | 1 | ok | ok: 1 | 0.749 | 0.749 | - | - | - | - | 224382976 | 224382976 |
| one_pipe-M10-t160 | one_pipe | 1 | ok | ok: 1 | 0.333 | 0.333 | - | - | - | - | 207642624 | 207642624 |
| naive-M16-L20 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M16-t160 | one_pipe | 1 | ok | ok: 1 | 0.332 | 0.332 | - | - | - | - | 207749120 | 207749120 |
| naive-M20-L20 | naive | 1 | ok | ok: 1 | 0.542 | 0.542 | - | - | - | - | 221257728 | 221257728 |
| one_pipe-M20-t100 | one_pipe | 1 | ok | ok: 1 | 0.211 | 0.211 | - | - | - | - | 205918208 | 205918208 |
| naive-M2-L20 | naive | 1 | ok | ok: 1 | 3.533 | 3.533 | - | - | - | - | 285503488 | 285503488 |
| one_pipe-M2-t200 | one_pipe | 1 | ok | ok: 1 | 0.352 | 0.352 | - | - | - | - | 207581184 | 207581184 |
| naive-M2.5-L20 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M2.5-t160 | one_pipe | 1 | ok | ok: 1 | 0.224 | 0.224 | - | - | - | - | 206700544 | 206700544 |
| naive-M3-L10 | naive | 1 | ok | ok: 1 | 1.044 | 1.044 | - | - | - | - | 238358528 | 238358528 |
| one_pipe-M3-t100 | one_pipe | 1 | ok | ok: 1 | 0.192 | 0.192 | - | - | - | - | 205725696 | 205725696 |
| naive-M6-L10 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M6-t100 | one_pipe | 1 | ok | ok: 1 | 0.193 | 0.193 | - | - | - | - | 205877248 | 205877248 |
| naive-M8-L10 | naive | 1 | ok | ok: 1 | 0.459 | 0.459 | - | - | - | - | 221593600 | 221593600 |
| one_pipe-M8-t64 | one_pipe | 1 | ok | ok: 1 | 0.115 | 0.115 | - | - | - | - | 202661888 | 202661888 |
| one_pipe-M8-t250 | one_pipe | 1 | ok | ok: 1 | 0.665 | 0.665 | - | - | - | - | 209948672 | 209948672 |
| naive-M10-L100 | naive | 1 | ok | ok: 1 | 7.620 | 7.620 | - | - | - | - | 321413120 | 321413120 |
| one_pipe-M10-t200 | one_pipe | 1 | ok | ok: 1 | 0.364 | 0.364 | - | - | - | - | 207597568 | 207597568 |
| naive-M16-L160 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M16-t200 | one_pipe | 1 | ok | ok: 1 | 0.367 | 0.367 | - | - | - | - | 207540224 | 207540224 |
| naive-M20-L25 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M20-t160 | one_pipe | 1 | ok | ok: 1 | 0.335 | 0.335 | - | - | - | - | 207851520 | 207851520 |
| one_pipe-M2-t50 | one_pipe | 1 | ok | ok: 1 | 0.097 | 0.097 | - | - | - | - | 202334208 | 202334208 |
| one_pipe-M2-t250 | one_pipe | 1 | ok | ok: 1 | 0.567 | 0.567 | - | - | - | - | 209448960 | 209448960 |
| naive-M2.5-L25 | naive | 1 | ok | ok: 1 | 3.746 | 3.746 | - | - | - | - | 281452544 | 281452544 |
| one_pipe-M2.5-t200 | one_pipe | 1 | ok | ok: 1 | 0.359 | 0.359 | - | - | - | - | 207704064 | 207704064 |
| naive-M3-L20 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M3-t160 | one_pipe | 1 | ok | ok: 1 | 0.222 | 0.222 | - | - | - | - | 206614528 | 206614528 |
| naive-M6-L20 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M6-t160 | one_pipe | 1 | ok | ok: 1 | 0.262 | 0.262 | - | - | - | - | 206839808 | 206839808 |
| naive-M8-L12.5 | naive | 1 | ok | ok: 1 | 0.462 | 0.462 | - | - | - | - | 224260096 | 224260096 |
| one_pipe-M8-t100 | one_pipe | 1 | ok | ok: 1 | 0.191 | 0.191 | - | - | - | - | 205824000 | 205824000 |
| naive-M10-L10 | naive | 1 | ok | ok: 1 | 0.325 | 0.325 | - | - | - | - | 215842816 | 215842816 |
| one_pipe-M10-t66.6667 | one_pipe | 1 | ok | ok: 1 | 0.122 | 0.122 | - | - | - | - | 203923456 | 203923456 |
| one_pipe-M10-t250 | one_pipe | 1 | ok | ok: 1 | 0.697 | 0.697 | - | - | - | - | 210460672 | 210460672 |
| one_pipe-M16-t80 | one_pipe | 1 | ok | ok: 1 | 0.181 | 0.181 | - | - | - | - | 205471744 | 205471744 |
| one_pipe-M16-t250 | one_pipe | 1 | ok | ok: 1 | 0.751 | 0.751 | - | - | - | - | 210202624 | 210202624 |
| naive-M20-L200 | naive | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| one_pipe-M20-t200 | one_pipe | 1 | ok | ok: 1 | 0.379 | 0.379 | - | - | - | - | 207777792 | 207777792 |


#### controls against L11 and the THRD-04 test rows

Each control row of the runner, next to L11's macOS arm64 outcome for the same construction, size and position (`bench/results/thread-spike/2026-10-08-a-controls.jsonl`, rows of kind naive and one_pipe, right hand; `ratio` is the precise volume over the closed form, so L11's relative error plus 1). Generated from the two record files; no figure is typed.

| construction | d | pitch | length (naive) or turns (one_pipe) | runner (linux/amd64) | L11 macOS arm64 |
| --- | --- | --- | --- | --- | --- |
| naive-M2-L4 | 2 | 0.4 | 4 | ok, 1 solid(s), valid True, ratio 0.290229 | built, 1 solid(s), valid True, ratio 0.290229 |
| one_pipe-M2-t100 | 2 | 0.4 | 100 | ok, 1 solid(s), valid True, ratio 0.99999 | built, 1 solid(s), valid True, ratio 0.99999 |
| naive-M2.5-L4.5 | 2.5 | 0.45 | 4.5 | refused: ValueError: Null TopoDS_Shape object | built, 1 solid(s), valid True, ratio 0.258961 |
| one_pipe-M2.5-t55.5556 | 2.5 | 0.45 | 55.5556 | ok, 1 solid(s), valid True, ratio 0.999996 | built, 1 solid(s), valid True, ratio 0.999996 |
| one_pipe-M2.5-t250 | 2.5 | 0.45 | 250 | ok, 1 solid(s), valid True, ratio 0.999994 | built, 1 solid(s), valid True, ratio 0.999994 |
| naive-M3-L30 | 3 | 0.5 | 30 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M3-t200 | 3 | 0.5 | 200 | ok, 1 solid(s), valid True, ratio 0.999988 | built, 1 solid(s), valid True, ratio 0.999988 |
| naive-M6-L60 | 6 | 1 | 60 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M6-t200 | 6 | 1 | 200 | ok, 1 solid(s), valid True, ratio 0.999988 | built, 1 solid(s), valid True, ratio 0.999988 |
| naive-M8-L20 | 8 | 1.25 | 20 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M8-t160 | 8 | 1.25 | 160 | ok, 1 solid(s), valid True, ratio -1.00001 | built, 1 solid(s), valid True, ratio -1.00001 |
| naive-M10-L15 | 10 | 1.5 | 15 | ok, 1 solid(s), valid True, ratio 0.212962 | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M10-t100 | 10 | 1.5 | 100 | ok, 1 solid(s), valid True, ratio 0.999997 | built, 1 solid(s), valid True, ratio 0.999997 |
| naive-M16-L10 | 16 | 2 | 10 | ok, 1 solid(s), valid True, ratio 0.204723 | built, 1 solid(s), valid True, ratio 0.204723 |
| one_pipe-M16-t100 | 16 | 2 | 100 | ok, 1 solid(s), valid True, ratio 0.999995 | built, 1 solid(s), valid True, ratio 0.999995 |
| naive-M20-L10 | 20 | 2.5 | 10 | ok, 1 solid(s), valid True, ratio 0.219346 | built, 1 solid(s), valid True, ratio 0.219346 |
| one_pipe-M20-t80 | 20 | 2.5 | 80 | ok, 1 solid(s), valid True, ratio 0.999998 | built, 1 solid(s), valid True, ratio 0.999998 |
| one_pipe-M20-t250 | 20 | 2.5 | 250 | ok, 1 solid(s), valid True, ratio 0.999998 | built, 1 solid(s), valid True, ratio 0.999998 |
| naive-M2-L10 | 2 | 0.4 | 10 | refused: ValueError: Null TopoDS_Shape object | built, 1 solid(s), valid True, ratio 0.261206 |
| one_pipe-M2-t160 | 2 | 0.4 | 160 | ok, 1 solid(s), valid True, ratio -1.00001 | built, 1 solid(s), valid True, ratio -1.00001 |
| naive-M2.5-L10 | 2.5 | 0.45 | 10 | refused: ValueError: Null TopoDS_Shape object | built, 1 solid(s), valid True, ratio 0.236871 |
| one_pipe-M2.5-t100 | 2.5 | 0.45 | 100 | ok, 1 solid(s), valid True, ratio 0.999999 | built, 1 solid(s), valid True, ratio 0.999999 |
| naive-M3-L5 | 3 | 0.5 | 5 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M3-t60 | 3 | 0.5 | 60 | ok, 1 solid(s), valid True, ratio 0.999984 | built, 1 solid(s), valid True, ratio 0.999984 |
| one_pipe-M3-t250 | 3 | 0.5 | 250 | ok, 1 solid(s), valid True, ratio 0.999993 | built, 1 solid(s), valid True, ratio 0.999993 |
| one_pipe-M6-t60 | 6 | 1 | 60 | ok, 1 solid(s), valid True, ratio 0.999994 | built, 1 solid(s), valid True, ratio 0.999994 |
| one_pipe-M6-t250 | 6 | 1 | 250 | ok, 1 solid(s), valid True, ratio 0.999993 | built, 1 solid(s), valid True, ratio 0.999993 |
| naive-M8-L80 | 8 | 1.25 | 80 | refused: ValueError: Null TopoDS_Shape object | built, 1 solid(s), valid True, ratio 0.191174 |
| one_pipe-M8-t200 | 8 | 1.25 | 200 | ok, 1 solid(s), valid True, ratio 0.999988 | built, 1 solid(s), valid True, ratio 0.999988 |
| naive-M10-L20 | 10 | 1.5 | 20 | ok, 1 solid(s), valid True, ratio 1.02492 | built, 1 solid(s), valid True, ratio 1.02662 |
| one_pipe-M10-t160 | 10 | 1.5 | 160 | ok, 1 solid(s), valid True, ratio -1 | built, 1 solid(s), valid True, ratio -1 |
| naive-M16-L20 | 16 | 2 | 20 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M16-t160 | 16 | 2 | 160 | ok, 1 solid(s), valid True, ratio -1.00001 | built, 1 solid(s), valid True, ratio -1.00001 |
| naive-M20-L20 | 20 | 2.5 | 20 | ok, 1 solid(s), valid True, ratio 0.182789 | built, 1 solid(s), valid True, ratio 0.182789 |
| one_pipe-M20-t100 | 20 | 2.5 | 100 | ok, 1 solid(s), valid True, ratio 0.999992 | built, 1 solid(s), valid True, ratio 0.999992 |
| naive-M2-L20 | 2 | 0.4 | 20 | ok, 1 solid(s), valid True, ratio 0.251542 | built, 1 solid(s), valid True, ratio 0.251542 |
| one_pipe-M2-t200 | 2 | 0.4 | 200 | ok, 1 solid(s), valid True, ratio 0.999958 | built, 1 solid(s), valid True, ratio 0.999958 |
| naive-M2.5-L20 | 2.5 | 0.45 | 20 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M2.5-t160 | 2.5 | 0.45 | 160 | ok, 1 solid(s), valid True, ratio -1.00001 | built, 1 solid(s), valid True, ratio -1.00001 |
| naive-M3-L10 | 3 | 0.5 | 10 | ok, 1 solid(s), valid True, ratio 0.218512 | built, 1 solid(s), valid True, ratio 0.218512 |
| one_pipe-M3-t100 | 3 | 0.5 | 100 | ok, 1 solid(s), valid True, ratio 0.999999 | built, 1 solid(s), valid True, ratio 0.999999 |
| naive-M6-L10 | 6 | 1 | 10 | refused: ValueError: Null TopoDS_Shape object | built, 1 solid(s), valid True, ratio 0.238384 |
| one_pipe-M6-t100 | 6 | 1 | 100 | ok, 1 solid(s), valid True, ratio 0.999999 | built, 1 solid(s), valid True, ratio 0.999999 |
| naive-M8-L10 | 8 | 1.25 | 10 | ok, 1 solid(s), valid True, ratio 0.231722 | built, 1 solid(s), valid True, ratio 0.231722 |
| one_pipe-M8-t64 | 8 | 1.25 | 64 | ok, 1 solid(s), valid True, ratio 1.00001 | built, 1 solid(s), valid True, ratio 1.00001 |
| one_pipe-M8-t250 | 8 | 1.25 | 250 | ok, 1 solid(s), valid True, ratio 1 | built, 1 solid(s), valid True, ratio 1 |
| naive-M10-L100 | 10 | 1.5 | 100 | ok, 1 solid(s), valid True, ratio 0.182793 | built, 1 solid(s), valid True, ratio 0.182793 |
| one_pipe-M10-t200 | 10 | 1.5 | 200 | ok, 1 solid(s), valid True, ratio 0.999991 | built, 1 solid(s), valid True, ratio 0.999991 |
| naive-M16-L160 | 16 | 2 | 160 | refused: StdFail_NotDone: BRepOffsetAPI_MakePipeShell::MakeSolid | failure: Standard_Failure: BRepOffsetAPI_MakePipeShell::MakeSolid |
| one_pipe-M16-t200 | 16 | 2 | 200 | ok, 1 solid(s), valid True, ratio 0.999995 | built, 1 solid(s), valid True, ratio 0.999995 |
| naive-M20-L25 | 20 | 2.5 | 25 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M20-t160 | 20 | 2.5 | 160 | ok, 1 solid(s), valid True, ratio -0.999995 | built, 1 solid(s), valid True, ratio -0.999995 |
| one_pipe-M2-t50 | 2 | 0.4 | 50 | ok, 1 solid(s), valid True, ratio 0.99999 | built, 1 solid(s), valid True, ratio 0.99999 |
| one_pipe-M2-t250 | 2 | 0.4 | 250 | ok, 1 solid(s), valid True, ratio 0.99998 | built, 1 solid(s), valid True, ratio 0.99998 |
| naive-M2.5-L25 | 2.5 | 0.45 | 25 | ok, 2 solid(s), valid True, ratio 1.03572 | built, 2 solid(s), valid True, ratio 1.03573 |
| one_pipe-M2.5-t200 | 2.5 | 0.45 | 200 | ok, 1 solid(s), valid True, ratio 0.999988 | built, 1 solid(s), valid True, ratio 0.999988 |
| naive-M3-L20 | 3 | 0.5 | 20 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M3-t160 | 3 | 0.5 | 160 | ok, 1 solid(s), valid True, ratio -1.00001 | built, 1 solid(s), valid True, ratio -1.00001 |
| naive-M6-L20 | 6 | 1 | 20 | refused: ValueError: Null TopoDS_Shape object | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M6-t160 | 6 | 1 | 160 | ok, 1 solid(s), valid True, ratio -0.999995 | built, 1 solid(s), valid True, ratio -0.999995 |
| naive-M8-L12.5 | 8 | 1.25 | 12.5 | ok, 1 solid(s), valid True, ratio 0.222455 | failure: ValueError: Null TopoDS_Shape object |
| one_pipe-M8-t100 | 8 | 1.25 | 100 | ok, 1 solid(s), valid True, ratio 0.999998 | built, 1 solid(s), valid True, ratio 0.999998 |
| naive-M10-L10 | 10 | 1.5 | 10 | ok, 1 solid(s), valid True, ratio 0.23071 | built, 1 solid(s), valid True, ratio 0.23071 |
| one_pipe-M10-t66.6667 | 10 | 1.5 | 66.6667 | ok, 1 solid(s), valid True, ratio 1 | built, 1 solid(s), valid True, ratio 1 |
| one_pipe-M10-t250 | 10 | 1.5 | 250 | ok, 1 solid(s), valid True, ratio 1.00001 | built, 1 solid(s), valid True, ratio 1.00001 |
| one_pipe-M16-t80 | 16 | 2 | 80 | ok, 1 solid(s), valid True, ratio 0.999994 | built, 1 solid(s), valid True, ratio 0.999994 |
| one_pipe-M16-t250 | 16 | 2 | 250 | ok, 1 solid(s), valid True, ratio 0.999975 | built, 1 solid(s), valid True, ratio 0.999975 |
| naive-M20-L200 | 20 | 2.5 | 200 | refused: ValueError: Null TopoDS_Shape object | built, 1 solid(s), valid True, ratio 0.149887 |
| one_pipe-M20-t200 | 20 | 2.5 | 200 | ok, 1 solid(s), valid True, ratio 0.999986 | built, 1 solid(s), valid True, ratio 0.999986 |

- THRD-04 row naive (2.0, 0.4, 4.0) (naive-M2-L4): 1 solid(s), valid True, volume ratio 0.290229: one valid solid, volume below half the closed form
- THRD-04 row naive (8.0, 1.25, 10.0) (naive-M8-L10): 1 solid(s), valid True, volume ratio 0.231722: one valid solid, volume below half the closed form
- THRD-04 row naive (20.0, 2.5, 10.0) (naive-M20-L10): 1 solid(s), valid True, volume ratio 0.219346: one valid solid, volume below half the closed form
- THRD-04 row one-pipe (6.0, 1.0, 160 turns) (one_pipe-M6-t160): 1 solid(s), valid True, volume ratio -0.999995: one valid solid, volume inverted (below -0.5 times the closed form, the test's error < -1.5)

### D-19 margin and R6 charges

Both come from `python -m bench.oper_sets` over the committed records of the spread run 40646125666 and the explore run 40646117094; each cell is the command's output, put into a table.

**Margin (R5, G3).** The cold wall is `build_s + export_s` of each reading; `m` is the largest `max / median - 1` over the 12 spread points, every one complete at repetitions 1 to 5 and ok (no point without a median, so no G3 stop).

| point | artifact | median cold wall s | max cold wall s | max / median - 1 |
| --- | --- | --- | --- | --- |
| default-bolt | stl-preview | 2.110499190999974 | 2.1363796780000257 | 0.012262732490216921 |
| iso4032:M20 | stl-preview | 2.6614660170000093 | 3.0202592229999823 | 0.13481036530551038 |
| iso4032:M20 | stl-fine | 3.7548752579999984 | 4.739558092999999 | 0.2622411577860202 |
| iso4032:M20 | step | 2.259308578999992 | 2.8088933559999987 | 0.24325352548489088 |
| default-bolt | stl-fine | 3.9845434549999936 | 4.136267407999981 | 0.03807812732211424 |
| default-bolt | step | 1.9532275739999818 | 2.0808743249999964 | 0.065351704378517 |
| default-nut | stl-preview | 2.4645077259999937 | 2.491368682000001 | 0.010899116166944944 |
| default-nut | stl-fine | 2.912370015000022 | 3.146872801000029 | 0.08051957161769008 |
| default-nut | step | 2.4569704450000245 | 2.488935288999926 | 0.01300986101194268 |
| iso4014:M20x200 | stl-preview | 3.595484694999982 | 3.678528082000014 | 0.023096576413053738 |
| iso4014:M20x200 | stl-fine | 5.960165231000019 | 9.168338566000017 | 0.5382691940004687 |
| iso4014:M20x200 | step | 2.8264241389999967 | 2.8569772710000336 | 0.01080981851890317 |

`m = 0.5382691940004687, set by iso4014:M20x200 at stl-fine` (spread run 40646125666).

**R6 charges (G4).** Per (kind, artifact) the largest `wall_s` over every explore reading of the group, whatever its status (explore run 40646117094, 1692 readings). Half of the measure job's `timeout-minutes` (350) is 10500 s. A point of a group absent here (a probe) is charged its `deadline_s`, 600 s.

| kind | artifact | largest explore wall_s (every status) |
| --- | --- | --- |
| bolt | step | 29.94342979000004 |
| bolt | stl-fine | 571.832342047 |
| bolt | stl-preview | 600.731243473 |
| nut | step | 37.973383033999994 |
| nut | stl-fine | 576.08785283 |
| nut | stl-preview | 74.68551229399986 |

### walls-down, run 40652801529

- Dispatched sha: `4dd60e1cade32eddbc5beccdccfcb6b2c44f8115`
- Records: `bench/results/phase-07/walls-down-40652801529/` (9 artifacts, 216 readings), run https://github.com/halfb00t/screw/actions/runs/40652801529
- CPU models seen (jobs): AMD EPYC 7763 64-Core Processor (5); AMD EPYC 9V45 96-Core Processor (1); AMD EPYC 9V74 80-Core Processor (3)
- Counts by status: ok: 131, refused: 85
- One dispatch of walls-down.json (216 points of the 9 cells that were refused at 250 turns, in 9 R6 shards), dispatched at the commit that added the file; not split.
- Summary: `python -m bench.oper summarize --markdown --reps 1` over the directory, as printed.

### Host

| fact | value |
| --- | --- |
| image | screw:ci |
| image_id | sha256:237b8049e1627cc0f911ba5c8b74d7579762e5c883a9e9afaa3edd59b10c40d0, sha256:e5e95b94b64d61625a9623b379a513834446251533fa0f6cdbf6c1762f566d28, sha256:a42fb1ba7b2ea4ecd8d00755a5398cad7ebac95c19828c4dd2ab1e2016d5ad97, sha256:2752a7fd76e1d544238675b427a2c161ef2015f94656cb5829c95cbc1f569de6, sha256:343a71cdaff2d30b58892bc4638f786dcdb0143075c9937d420d8fc2321bb071, sha256:3a50adf9fa73f4b8b76f5a60f0b7d34b7b1a201245a0ba5e6d09779df142e4b7, sha256:d5643e70e27080b56678acd8f6e651af55f21fa05e6c8597a693e4c074804666, sha256:7f615c0e7759974963ec7e7207c8593de87f94e8c17e62d9637812f8af806cbd, sha256:b025f22b763cc69cbcf81336933fcbae3745a63a095c333201561bc1b9d84bee |
| versions | {"cadquery": "2.8.0", "cadquery_ocp": "7.9.3.1.1"} |
| nproc | 4 |
| mem_total_bytes | 16759443456, 16759439360 |
| cpu_model | AMD EPYC 7763 64-Core Processor, AMD EPYC 9V74 80-Core Processor, AMD EPYC 9V45 96-Core Processor |
| kernel | 7.0.0-1017-azure |
| machine | x86_64 |
| GITHUB_RUN_ID | 40652801529 |
| GITHUB_JOB | measure |
| GITHUB_SHA | 4dd60e1cade32eddbc5beccdccfcb6b2c44f8115 |

### Readings

Status counts: refused: 85, ok: 131

| point | artifact | n | status | counts | median build s | max build s | median export s | max export s | median bytes | max bytes | median peak bytes | max peak bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| turns240-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns200-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns190-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns180-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns170-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns160-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns150-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns140-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns130-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns120-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns110-bolt-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns100-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 10.296 | 10.296 | 0.518 | 0.518 | 3813284 | 3813284 | 265678848 | 265678848 |
| turns90-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 9.266 | 9.266 | 0.465 | 0.465 | 3432284 | 3432284 | 260153344 | 260153344 |
| turns80-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 8.034 | 8.034 | 0.441 | 0.441 | 3043584 | 3043584 | 258551808 | 258551808 |
| turns70-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 6.900 | 6.900 | 0.368 | 0.368 | 2669784 | 2669784 | 251465728 | 251465728 |
| turns60-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 5.930 | 5.930 | 0.317 | 0.317 | 2289384 | 2289384 | 248254464 | 248254464 |
| turns50-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 4.847 | 4.847 | 0.260 | 0.260 | 1899984 | 1899984 | 242806784 | 242806784 |
| turns40-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 3.789 | 3.789 | 0.212 | 0.212 | 1526584 | 1526584 | 240848896 | 240848896 |
| turns30-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 3.015 | 3.015 | 0.210 | 0.210 | 1146284 | 1146284 | 236027904 | 236027904 |
| turns20-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 2.264 | 2.264 | 0.111 | 0.111 | 757284 | 757284 | 218943488 | 218943488 |
| turns10-bolt-M2-right | stl-preview | 1 | ok | ok: 1 | 1.372 | 1.372 | 0.058 | 0.058 | 383584 | 383584 | 214560768 | 214560768 |
| turns240-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns200-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns190-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns180-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns170-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns160-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns150-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns140-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns130-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns120-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns110-nut-M2-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns100-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 21.885 | 21.885 | 0.545 | 0.545 | 3941384 | 3941384 | 390283264 | 390283264 |
| turns90-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 19.660 | 19.660 | 0.492 | 0.492 | 3544784 | 3544784 | 376520704 | 376520704 |
| turns80-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 17.093 | 17.093 | 0.437 | 0.437 | 3145884 | 3145884 | 357093376 | 357093376 |
| turns70-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 14.932 | 14.932 | 0.381 | 0.381 | 2735184 | 2735184 | 346722304 | 346722304 |
| turns60-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 12.601 | 12.601 | 0.326 | 0.326 | 2341484 | 2341484 | 323997696 | 323997696 |
| turns50-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 10.538 | 10.538 | 0.272 | 0.272 | 1941284 | 1941284 | 308715520 | 308715520 |
| turns40-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 8.465 | 8.465 | 0.250 | 0.250 | 1531584 | 1531584 | 295649280 | 295649280 |
| turns30-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 7.278 | 7.278 | 0.163 | 0.163 | 1138984 | 1138984 | 262651904 | 262651904 |
| turns20-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 4.845 | 4.845 | 0.110 | 0.110 | 739084 | 739084 | 257875968 | 257875968 |
| turns10-nut-M2-right | stl-preview | 1 | ok | ok: 1 | 3.574 | 3.574 | 0.054 | 0.054 | 329984 | 329984 | 238583808 | 238583808 |
| turns240-bolt-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-bolt-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-bolt-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 22.490 | 22.490 | 0.945 | 0.945 | 6808984 | 6808984 | 308940800 | 308940800 |
| turns200-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 21.251 | 21.251 | 0.894 | 0.894 | 6480384 | 6480384 | 305127424 | 305127424 |
| turns190-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 20.040 | 20.040 | 0.849 | 0.849 | 6160484 | 6160484 | 302039040 | 302039040 |
| turns180-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 19.098 | 19.098 | 0.820 | 0.820 | 5837084 | 5837084 | 295378944 | 295378944 |
| turns170-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 18.612 | 18.612 | 0.847 | 0.847 | 5508084 | 5508084 | 305471488 | 305471488 |
| turns160-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 17.457 | 17.457 | 0.689 | 0.689 | 5187584 | 5187584 | 289304576 | 289304576 |
| turns150-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 16.452 | 16.452 | 0.648 | 0.648 | 4865084 | 4865084 | 284164096 | 284164096 |
| turns140-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 15.202 | 15.202 | 0.605 | 0.605 | 4537084 | 4537084 | 281051136 | 281051136 |
| turns130-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 14.046 | 14.046 | 0.561 | 0.561 | 4216384 | 4216384 | 277118976 | 277118976 |
| turns120-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 13.176 | 13.176 | 0.553 | 0.553 | 3893884 | 3893884 | 271822848 | 271822848 |
| turns110-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 11.810 | 11.810 | 0.479 | 0.479 | 3565884 | 3565884 | 268161024 | 268161024 |
| turns100-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 10.636 | 10.636 | 0.434 | 0.434 | 3245084 | 3245084 | 265240576 | 265240576 |
| turns90-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 9.728 | 9.728 | 0.393 | 0.393 | 2922384 | 2922384 | 260005888 | 260005888 |
| turns80-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 8.583 | 8.583 | 0.372 | 0.372 | 2593984 | 2593984 | 256311296 | 256311296 |
| turns70-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 7.164 | 7.164 | 0.306 | 0.306 | 2273684 | 2273684 | 251940864 | 251940864 |
| turns60-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 6.148 | 6.148 | 0.263 | 0.263 | 1950984 | 1950984 | 247275520 | 247275520 |
| turns50-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 5.166 | 5.166 | 0.224 | 0.224 | 1623084 | 1623084 | 244523008 | 244523008 |
| turns40-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 3.947 | 3.947 | 0.178 | 0.178 | 1302684 | 1302684 | 240017408 | 240017408 |
| turns30-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 3.099 | 3.099 | 0.172 | 0.172 | 979684 | 979684 | 236859392 | 236859392 |
| turns20-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 2.337 | 2.337 | 0.093 | 0.093 | 652084 | 652084 | 217714688 | 217714688 |
| turns10-bolt-M2-left | stl-preview | 1 | ok | ok: 1 | 1.445 | 1.445 | 0.050 | 0.050 | 330984 | 330984 | 215203840 | 215203840 |
| turns240-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns200-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 45.220 | 45.220 | 0.928 | 0.928 | 6640484 | 6640484 | 562003968 | 562003968 |
| turns190-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 43.031 | 43.031 | 0.884 | 0.884 | 6294384 | 6294384 | 554430464 | 554430464 |
| turns180-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns170-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 38.526 | 38.526 | 0.789 | 0.789 | 5638784 | 5638784 | 516526080 | 516526080 |
| turns160-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 36.082 | 36.082 | 0.741 | 0.741 | 5292284 | 5292284 | 487788544 | 487788544 |
| turns150-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns140-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 30.992 | 30.992 | 0.651 | 0.651 | 4637484 | 4637484 | 469958656 | 469958656 |
| turns130-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 29.022 | 29.022 | 0.640 | 0.640 | 4290484 | 4290484 | 450170880 | 450170880 |
| turns120-nut-M2-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns110-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 24.144 | 24.144 | 0.642 | 0.642 | 3634984 | 3634984 | 416219136 | 416219136 |
| turns100-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 22.011 | 22.011 | 0.467 | 0.467 | 3288084 | 3288084 | 397930496 | 397930496 |
| turns90-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 19.582 | 19.582 | 0.418 | 0.418 | 2959484 | 2959484 | 372326400 | 372326400 |
| turns80-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 17.467 | 17.467 | 0.373 | 0.373 | 2632884 | 2632884 | 357593088 | 357593088 |
| turns70-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 15.040 | 15.040 | 0.326 | 0.326 | 2286384 | 2286384 | 349888512 | 349888512 |
| turns60-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 12.630 | 12.630 | 0.280 | 0.280 | 1956684 | 1956684 | 325541888 | 325541888 |
| turns50-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 10.332 | 10.332 | 0.233 | 0.233 | 1631284 | 1631284 | 302923776 | 302923776 |
| turns40-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 8.543 | 8.543 | 0.186 | 0.186 | 1283784 | 1283784 | 280494080 | 280494080 |
| turns30-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 7.052 | 7.052 | 0.140 | 0.140 | 954184 | 954184 | 270053376 | 270053376 |
| turns20-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 4.888 | 4.888 | 0.093 | 0.093 | 628784 | 628784 | 249765888 | 249765888 |
| turns10-nut-M2-left | stl-preview | 1 | ok | ok: 1 | 3.428 | 3.428 | 0.046 | 0.046 | 281684 | 281684 | 240631808 | 240631808 |
| turns240-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns200-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns190-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns180-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns170-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns160-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns150-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns140-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns130-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns120-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns110-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns100-bolt-M2.5-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns90-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 9.223 | 9.223 | 0.516 | 0.516 | 3729284 | 3729284 | 257044480 | 257044480 |
| turns80-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 7.941 | 7.941 | 0.483 | 0.483 | 3317684 | 3317684 | 256536576 | 256536576 |
| turns70-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 6.853 | 6.853 | 0.399 | 0.399 | 2901184 | 2901184 | 249753600 | 249753600 |
| turns60-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 5.836 | 5.836 | 0.344 | 0.344 | 2488084 | 2488084 | 244953088 | 244953088 |
| turns50-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 4.715 | 4.715 | 0.284 | 0.284 | 2075084 | 2075084 | 241479680 | 241479680 |
| turns40-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 3.868 | 3.868 | 0.233 | 0.233 | 1658784 | 1658784 | 238055424 | 238055424 |
| turns30-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 3.135 | 3.135 | 0.210 | 0.210 | 1243784 | 1243784 | 235032576 | 235032576 |
| turns20-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 2.245 | 2.245 | 0.120 | 0.120 | 830984 | 830984 | 217194496 | 217194496 |
| turns10-bolt-M2.5-right | stl-preview | 1 | ok | ok: 1 | 1.363 | 1.363 | 0.063 | 0.063 | 414784 | 414784 | 213651456 | 213651456 |
| turns240-bolt-M2.5-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-bolt-M2.5-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-bolt-M2.5-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-bolt-M2.5-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns200-bolt-M2.5-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns190-bolt-M2.5-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns180-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 19.077 | 19.077 | 0.883 | 0.883 | 6119084 | 6119084 | 293392384 | 293392384 |
| turns170-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 16.372 | 16.372 | 0.711 | 0.711 | 5789284 | 5789284 | 288997376 | 288997376 |
| turns160-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 15.597 | 15.597 | 0.681 | 0.681 | 5438084 | 5438084 | 284991488 | 284991488 |
| turns150-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 14.730 | 14.730 | 0.624 | 0.624 | 5096884 | 5096884 | 280498176 | 280498176 |
| turns140-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 13.424 | 13.424 | 0.685 | 0.685 | 4769184 | 4769184 | 279126016 | 279126016 |
| turns130-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 12.347 | 12.347 | 0.549 | 0.549 | 4418184 | 4418184 | 272334848 | 272334848 |
| turns120-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 11.579 | 11.579 | 0.499 | 0.499 | 4079084 | 4079084 | 268943360 | 268943360 |
| turns110-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 10.397 | 10.397 | 0.461 | 0.461 | 3750984 | 3750984 | 265093120 | 265093120 |
| turns100-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 9.582 | 9.582 | 0.436 | 0.436 | 3399884 | 3399884 | 261623808 | 261623808 |
| turns90-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 8.473 | 8.473 | 0.410 | 0.410 | 3060784 | 3060784 | 257654784 | 257654784 |
| turns80-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 7.393 | 7.393 | 0.349 | 0.349 | 2732084 | 2732084 | 253009920 | 253009920 |
| turns70-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 6.422 | 6.422 | 0.292 | 0.292 | 2380284 | 2380284 | 249323520 | 249323520 |
| turns60-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 5.519 | 5.519 | 0.258 | 0.258 | 2043584 | 2043584 | 244654080 | 244654080 |
| turns50-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 4.339 | 4.339 | 0.212 | 0.212 | 1716884 | 1716884 | 241332224 | 241332224 |
| turns40-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 3.599 | 3.599 | 0.184 | 0.184 | 1366984 | 1366984 | 238280704 | 238280704 |
| turns30-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 2.811 | 2.811 | 0.135 | 0.135 | 1026784 | 1026784 | 224628736 | 224628736 |
| turns20-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 2.076 | 2.076 | 0.092 | 0.092 | 698284 | 698284 | 216907776 | 216907776 |
| turns10-bolt-M2.5-left | stl-preview | 1 | ok | ok: 1 | 1.329 | 1.329 | 0.050 | 0.050 | 347084 | 347084 | 213086208 | 213086208 |
| turns240-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns200-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns190-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns180-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns170-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns160-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns150-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns140-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns130-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns120-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns110-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns100-bolt-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns90-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 6.022 | 6.022 | 0.335 | 0.335 | 3967184 | 3967184 | 257888256 | 257888256 |
| turns80-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 5.369 | 5.369 | 0.299 | 0.299 | 3527884 | 3527884 | 254787584 | 254787584 |
| turns70-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 6.763 | 6.763 | 0.444 | 0.444 | 3085084 | 3085084 | 250908672 | 250908672 |
| turns60-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 5.789 | 5.789 | 0.380 | 0.380 | 2645184 | 2645184 | 246272000 | 246272000 |
| turns50-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 4.767 | 4.767 | 0.323 | 0.323 | 2205884 | 2205884 | 242614272 | 242614272 |
| turns40-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 3.723 | 3.723 | 0.258 | 0.258 | 1763284 | 1763284 | 239673344 | 239673344 |
| turns30-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 3.144 | 3.144 | 0.207 | 0.207 | 1323184 | 1323184 | 233992192 | 233992192 |
| turns20-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 2.389 | 2.389 | 0.132 | 0.132 | 883884 | 883884 | 217772032 | 217772032 |
| turns10-bolt-M3-right | stl-preview | 1 | ok | ok: 1 | 1.424 | 1.424 | 0.072 | 0.072 | 441284 | 441284 | 214188032 | 214188032 |
| turns240-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 53.331 | 53.331 | 1.523 | 1.523 | 10738484 | 10738484 | 515391488 | 515391488 |
| turns230-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 51.322 | 51.322 | 1.524 | 1.524 | 10288184 | 10288184 | 511893504 | 511893504 |
| turns220-nut-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 46.676 | 46.676 | 1.329 | 1.329 | 9383384 | 9383384 | 486465536 | 486465536 |
| turns200-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 44.709 | 44.709 | 1.266 | 1.266 | 8932684 | 8932684 | 470495232 | 470495232 |
| turns190-nut-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns180-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 39.716 | 39.716 | 1.146 | 1.146 | 8028184 | 8028184 | 421175296 | 421175296 |
| turns170-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 37.634 | 37.634 | 1.081 | 1.081 | 7577284 | 7577284 | 440483840 | 440483840 |
| turns160-nut-M3-right | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns150-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 32.711 | 32.711 | 0.950 | 0.950 | 6672184 | 6672184 | 411893760 | 411893760 |
| turns140-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 30.866 | 30.866 | 0.887 | 0.887 | 6221384 | 6221384 | 397897728 | 397897728 |
| turns130-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 28.099 | 28.099 | 0.822 | 0.822 | 5763984 | 5763984 | 387612672 | 387612672 |
| turns120-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 25.815 | 25.815 | 0.757 | 0.757 | 5319684 | 5319684 | 366149632 | 366149632 |
| turns110-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 23.114 | 23.114 | 0.699 | 0.699 | 4869484 | 4869484 | 359018496 | 359018496 |
| turns100-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 21.030 | 21.030 | 0.632 | 0.632 | 4414584 | 4414584 | 350261248 | 350261248 |
| turns90-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 19.023 | 19.023 | 0.653 | 0.653 | 3969784 | 3969784 | 328556544 | 328556544 |
| turns80-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 16.224 | 16.224 | 0.505 | 0.505 | 3519884 | 3519884 | 322760704 | 322760704 |
| turns70-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 14.276 | 14.276 | 0.439 | 0.439 | 3065084 | 3065084 | 285847552 | 285847552 |
| turns60-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 12.436 | 12.436 | 0.379 | 0.379 | 2618984 | 2618984 | 294350848 | 294350848 |
| turns50-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 9.695 | 9.695 | 0.311 | 0.311 | 2168684 | 2168684 | 286408704 | 286408704 |
| turns40-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 8.354 | 8.354 | 0.317 | 0.317 | 1711384 | 1711384 | 267468800 | 267468800 |
| turns30-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 6.856 | 6.856 | 0.185 | 0.185 | 1265284 | 1265284 | 259387392 | 259387392 |
| turns20-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 4.771 | 4.771 | 0.121 | 0.121 | 814384 | 814384 | 247087104 | 247087104 |
| turns10-nut-M3-right | stl-preview | 1 | ok | ok: 1 | 3.367 | 3.367 | 0.058 | 0.058 | 356384 | 356384 | 234733568 | 234733568 |
| turns240-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns230-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns220-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns210-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns200-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns190-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns180-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns170-bolt-M3-left | stl-preview | 1 | refused | refused: 1 | - | - | - | - | - | - | - | - |
| turns160-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 13.385 | 13.385 | 0.716 | 0.716 | 6043684 | 6043684 | 302669824 | 302669824 |
| turns150-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 12.773 | 12.773 | 0.612 | 0.612 | 5666884 | 5666884 | 282501120 | 282501120 |
| turns140-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 11.689 | 11.689 | 0.573 | 0.573 | 5297184 | 5297184 | 279486464 | 279486464 |
| turns130-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 10.871 | 10.871 | 0.529 | 0.529 | 4913684 | 4913684 | 276189184 | 276189184 |
| turns120-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 10.057 | 10.057 | 0.491 | 0.491 | 4536084 | 4536084 | 270323712 | 270323712 |
| turns110-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 9.024 | 9.024 | 0.453 | 0.453 | 4166084 | 4166084 | 267116544 | 267116544 |
| turns100-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 8.215 | 8.215 | 0.441 | 0.441 | 3780784 | 3780784 | 267845632 | 267845632 |
| turns90-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 7.331 | 7.331 | 0.369 | 0.369 | 3403884 | 3403884 | 257728512 | 257728512 |
| turns80-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 6.367 | 6.367 | 0.328 | 0.328 | 3033384 | 3033384 | 254779392 | 254779392 |
| turns70-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 5.462 | 5.462 | 0.289 | 0.289 | 2648184 | 2648184 | 250462208 | 250462208 |
| turns60-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 4.711 | 4.711 | 0.248 | 0.248 | 2271284 | 2271284 | 246439936 | 246439936 |
| turns50-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 3.852 | 3.852 | 0.209 | 0.209 | 1901384 | 1901384 | 243363840 | 243363840 |
| turns40-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 3.049 | 3.049 | 0.168 | 0.168 | 1516584 | 1516584 | 228540416 | 228540416 |
| turns30-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 2.491 | 2.491 | 0.128 | 0.128 | 1138784 | 1138784 | 221523968 | 221523968 |
| turns20-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 1.916 | 1.916 | 0.087 | 0.087 | 768384 | 768384 | 218013696 | 218013696 |
| turns10-bolt-M3-left | stl-preview | 1 | ok | ok: 1 | 1.208 | 1.208 | 0.047 | 0.047 | 384284 | 384284 | 214118400 | 214118400 |


#### R7 first ok step of the walked cells

The first ok step of a cell is the highest step whose reading is ok (R7, G2); a cell with no row ran ok at 250 turns. `python -m bench.oper_sets decide-walls` computes it from the two directories.

| cell | 250-turn reading | first ok step | readings it rests on |
| --- | --- | --- | --- |
| bolt-M2-right | refused | 100 | 16 |
| nut-M2-right | refused | 100 | 16 |
| bolt-M2-left | refused | 210 | 5 |
| nut-M2-left | refused | 200 | 6 |
| bolt-M2.5-right | refused | 90 | 17 |
| bolt-M2.5-left | refused | 180 | 8 |
| bolt-M3-right | refused | 90 | 17 |
| nut-M3-right | refused | 240 | 2 |
| bolt-M3-left | refused | 160 | 10 |

The smallest first ok step over the 60 cells is 90 turns (the candidate T of R7).

### D-08 stop at R10 (owner decision pending)

`python -m bench.oper_sets decide-walls --walls bench/results/phase-07/walls-40646134133 --down bench/results/phase-07/walls-down-40652801529` exits 3:

```
oper_sets: stop (R10): the largest failing value is 0.01, so V is 0.1, which lies outside the walk (it holds at most 0.01)
```

No candidate walls are recorded, and the walls confirm set is not generated, until the owner rules (R10: "Otherwise there is no number: the phase stops and asks the owner"). The evidence is the status of the 540 group (d) readings of the walls run 40646134133, by kind and radius `r` (mm):

| kind | r mm | readings by status |
| --- | --- | --- |
| bolt | 0.01 | ok: 30 |
| bolt | 0.003 | ok: 30 |
| bolt | 0.001 | ok: 30 |
| bolt | 0.0003 | ok: 29, refused: 1 |
| bolt | 0.0001 | ok: 29, refused: 1 |
| bolt | 3e-05 | refused: 30 |
| bolt | 1e-05 | refused: 30 |
| bolt | 3e-06 | refused: 30 |
| bolt | 1e-06 | refused: 30 |
| nut | 0.01 | refused: 30 |
| nut | 0.003 | refused: 30 |
| nut | 0.001 | refused: 30 |
| nut | 0.0003 | refused: 30 |
| nut | 0.0001 | refused: 30 |
| nut | 3e-05 | refused: 30 |
| nut | 1e-05 | refused: 30 |
| nut | 3e-06 | refused: 30 |
| nut | 1e-06 | refused: 30 |

Message prefixes of the refused readings (count): nut: `Geometry kernel failed (StdFail_NotDone); check d, pitch, le` (270); bolt: `Geometry kernel produced 0 solids from the tip cut for these` (2), `Geometry kernel failed (StdFail_NotDone); check d, pitch, le` (120).

For scale (from `bench/points/walls.json`, not a reading): the nut point `root-nut-M8-right-r0.01` has pitch 7.6487363662241625 mm and `m` 22.946209098672487 mm, where the M8 coarse pitch of the L11 sizes is 1.25 mm; every one of the 270 nut readings is refused, at every radius from 1e-2 to 1e-6, and the bolt readings are not.

