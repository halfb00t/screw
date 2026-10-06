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
