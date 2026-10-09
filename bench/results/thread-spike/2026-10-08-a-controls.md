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
