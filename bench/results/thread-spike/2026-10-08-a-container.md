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
