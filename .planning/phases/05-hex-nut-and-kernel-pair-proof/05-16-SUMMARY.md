---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 16
subsystem: bench
tags: [pair-proof, pre-registered, m18-diagnosis, pair-grid, product-cells, pair-03, pair-04]
requires:
  - phase: 05-15
    provides: "make pair, the pair tier and the verify cell"
  - phase: 05-03
    provides: "05-M18-DIAGNOSIS.md on main and bench/m18_probe.py"
  - phase: 05-01
    provides: "tests/data/pair_expected.tsv, the 240 pre-registered verdicts"
provides:
  - "bench/RESULTS.md: M18 control diagnosis, pair tier and product pair cells entries"
  - "bench/results/phase-05/m18-diagnosis.jsonl and pair-<size>.jsonl (15), each with its sha256 in the entry"
affects: [05-17, 05-18]
requirements-completed: [PAIR-03, PAIR-04]
estimate_ref: "90000 tokens, 3 tasks"
actuals:
  tokens: 9000
  tasks: 3
  commits: 3
plan_head_before: b19348a974434072accbb6d410e9fb133ebc16ef
plan_head_after: a58b70204c4ea55c2b392c11d9c0becd90abeb50
tech-stack:
  added: []
  patterns:
    - "a pre-registered run is one run: the entry is written from the record, whatever it says"
key-files:
  created:
    - bench/results/phase-05/m18-diagnosis.jsonl
    - bench/results/phase-05/pair-M2.jsonl (and the other 14 sizes)
  modified:
    - bench/RESULTS.md
key-decisions:
  - "Task 3 took the plan's no-difference branch: no size's m differs, so only the entry was committed (no bench/product_cells.py, no predictions file, no test)"
status: complete
---

# Phase 5 Plan 16: the pre-registered runs Summary

The M18 diagnosis, the full 240-cell pair grid and the product-cell comparison are on record: the M18 empty reproduces 10 of 10 and is a band of poses, not one pose; all 240 cells equal their pre-registered verdict; no ISO 4032 row's `m` differs from the recorded one, so there are no product cells. Nothing under `src/` or `tests/` changed.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 22bcd50 | test(bench): record the M18 control diagnosis |
| 2 | 80aac99 | test(pair): record the full pre-registered pair grid |
| 3 | a58b702 | test(pair): record that no product cell differs from the recorded height |

`commits: 3` is measured from the plan-start ledger (`git rev-list --count b19348a..HEAD` before this summary). `git diff --stat b19348a..HEAD -- src tests` is empty.

## Findings

**1. M18 control diagnosis (D-08).** One run of the 36 readings: **59.6 s** wall, 4 children at a time, each reading 2.89 to 3.70 s, 36 of 36 built, probe not void. Host `18 CPUs, arm64, 64.0 GiB RAM`, load1 9.46 before and 12.85 after (shared, busy). jsonl sha256 `b301560c784d386dd3d680ad2d52e71b674f7355264218ab9cc397dcf0ad8fbc`.
- H1 held (10 of 10 P1 readings empty), H3 held (both c = -0.05 readings empty), H4 held (fuzzy 1e-4 and swapped operands both still empty), H held (four harness controls non-empty, relative error 3.9e-06 to 5.0e-06).
- **H2 not held.** Of eight readings at |delta| >= 0.01 rad only two were non-empty (delta -0.1 right, +0.1 left, mirror images, away from theta 0); the other six read 0 solids.
- **Finding:** reproducible on this host: yes. Pose-local: no, the empty is a band at least 0.11 rad wide (14 of 16 neighbours empty); one edge lies between 0.01 and 0.1 rad on the away side, the other is beyond 0.1 rad on the toward side and not bracketed. M18 stays `inconclusive`; no rule or label changed.

**2. Full pair grid (D-07).** `make pair`, HEAD `22bcd50`, 8 workers, **1054.04 s (17:34)**, load1 5.69 before, 7.53 after, 5.69 to 28.21 sampled during (shared host, own workers included). **240 of 240 pass**: 88 proven, 60 violated, 92 inconclusive, each equal to the table; no mismatch, no timeout, no `error` line. Slowest cell 150.2 s (`M16-right-c0.05`), serial sum 7955 s. The 8 same-hand M18 cells at c 0.05 to 0.20 read inconclusive with the control empty, as in the diagnosis. The sha256 of each `pair-<size>.jsonl` is in the entry.

**3. Product cells (D-07 planner alert).** Compared the table's `m` with `iso4032.NUTS` `m_max` for the 14 sizes with a row: **none differs** (pitch equal too). M7 has no row, so no product cell. Per the plan's last sentence for this case, the entry says so and is the only thing committed.

## Deviations from Plan

### Interpretation

**1. Task 3 artifacts not created.** `bench/product_cells.py`, `product-cells-predictions.tsv`, `product-cells.jsonl` and the `tests/test_bench.py` test are named in the plan's `files_modified` and artifacts, but the action says "If no size's `m` differs, write the entry saying so and commit only it." That branch was taken, so Task 3's automated check `make test ... -k product_cells` (which needs the test) was not run: it would report "no tests ran". The `acceptance_criteria` predecessor-commit check has no predictions commit to cite. The comparison in the entry is the evidence.

**2. Task 3's `<verify>` second check** (the entry exists) passes; the first does not apply, as above.

No Rule 1-3 deviations. No auth gates.

## Measured facts

- **`make verify`** after the last commit: `3334 passed in 199.69s (0:03:19)`, coverage **97.32 %** against the 96.0 % floor. All three commits also passed the pre-commit `make verify`.
- Host load for every timing is in the entries; the host was shared with other sessions throughout.
- Plan estimate was 90000 tokens at low confidence; actuals use the estimate's chars/4 scale over the diff, which is the jsonl and RESULTS text (small).

## Known Stubs

None.

## Threat Flags

None. T-05-36 mitigated (protocol on main before the probe, guard passed, one run each, sha256 of every jsonl in its entry), T-05-37 mitigated (no mismatch to reclassify; nothing under `src/` or `tests/data/` changed).

## Notes for later plans

- `bench/results/phase-05/` now holds 16 committed jsonl files (the M18 record and 15 pair sizes); a re-run would append to the pair files, which the plan forbids.
- Debt or ideas filed: none.

## Self-Check: PASSED

- FOUND: bench/RESULTS.md (three entries), bench/results/phase-05/m18-diagnosis.jsonl, pair-M2.jsonl to pair-M20.jsonl (15)
- FOUND commits: 22bcd50, 80aac99, a58b702 (each an ancestor of HEAD)
