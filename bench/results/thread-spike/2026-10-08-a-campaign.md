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
