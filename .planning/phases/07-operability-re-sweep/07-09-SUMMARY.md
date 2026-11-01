---
phase: 07-operability-re-sweep
plan: 09
subsystem: testing
tags: [operability, cost-model, envelope, budget-candidates, d-06, numpy, R11, R12, R13]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-05: explore 40646117094 and spread 40646125666 records; 07-07: the L20 walls in the parameter model"
provides:
  - "bench.oper_fit: features, fit_points, fit, envelope, predict, enveloped, admit, load_set, fit_document, candidates, c3_basis, d06_trim, table; CLI fit and table"
  - "bench/results/phase-07/fit.json: 18 models (bolt and nut x 3 artifacts x bytes, seconds, peak), envelopes, 175 excluded explore points, run ids"
  - ".planning/phases/07-operability-re-sweep/07-BUDGET-TABLE.md: C1, C2, C3 with counts, worst cases and D-06 evidence, generated"
  - "bench.oper_fit in the kernel-free import contract"
affects: [07-10, 07-11, 07-15]

actuals:
  tokens: 11340   # chars/4 over bench/oper_fit.py and tests/test_oper_fit.py (45357 chars); generated fit.json and table excluded
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count 8518ff6..90f4c0a
plan_head_before: 8518ff6be8c949088d96c0187ee0447e146d7026
plan_head_after: 90f4c0a2d645329b4673657974b61263e81a3c0f   # before this SUMMARY's own commit

tech-stack:
  added: []
  patterns:
    - "a fit is reproducible from committed records: the plan's cmp holds on the writing machine; the gate compares coefficients to 1e-9 relative, since another BLAS may move last bits"
    - "a runner-only guard on fit input: oper-<set> file name, x86_64 header and a GitHub run id, or the record is refused"

key-files:
  created:
    - bench/oper_fit.py
    - tests/test_oper_fit.py
    - bench/results/phase-07/fit.json
    - .planning/phases/07-operability-re-sweep/07-BUDGET-TABLE.md
    - .planning/phases/07-operability-re-sweep/deferred-items.md
  modified:
    - pyproject.toml

key-decisions:
  - "The envelope's factor 1 + e is raised by whole ulps until every fitted point is covered in the float arithmetic admission uses; e is R12's value or a few ulps above it, never below"
  - "The table CLI takes --spread as well as --explore: R13's C3 rho is chosen among explore and spread points"
  - "Table populations: catalogue rows (294 bolt, 14 nut) and explore free-space points per artifact; a part the L20 model refuses counts as refused by the walls, separately from the budget"

requirements-completed: []   # OPER-03 advances; the admission model ships in 07-11 after the owner's budget ruling (07-10)

duration: about 45 min
completed: 2026-10-28
status: complete
---

# Phase 7 Plan 09: Cost model fit and candidate budget table Summary

**R11 least-squares cost models for bolt and nut at all three artifacts fitted from explore 40646117094 and spread 40646125666 (1529 fitted points, 175 excluded), R12 envelopes from 0.380 to 4.286, and a generated C1/C2/C3 table with D-06 trim evidence for the owner's ruling.**

## What was done

1. **Task 1 (tracer), `5b5fd58`.** `bench/oper_fit.py`:
   - The fit input is the `ok` rows of `bench.oper.summarize` with (1,) for explore and (1..5) for spread. The cold wall is summed per reading before the per-point max.
   - `fit` runs `numpy.linalg.lstsq` on the log target per (kind, artifact, target) and stops (`ProtocolStop` R11) when a model has fewer than coefficients + 1 points.
   - `envelope`, `predict` (`math.exp`), `admit`.
   - `load_set` takes only `oper-<set>-` files whose header names an `x86_64` machine and a run id.
   - `fit.json` committed, plus the kernel-free contract entry and 18 tests.
2. **Task 2, `90f4c0a`.** `candidates` (C1, C2 and C3 only, G10), `c3_basis`, `d06_trim`, `table` and the `table` CLI, with 7 more tests. `07-BUDGET-TABLE.md` is generated and has nothing added by hand.

## The fit (fit.json)

- Explore: 1517 points fitted, 175 excluded (killed, capped or refused). Spread: 12 fitted, none excluded. Full rank in all 18 models (bolt 8, nut 7).
- The envelopes vary widely. The largest is bolt `stl-preview` seconds, e = 4.286, set by `explore:bolt-d1-p0.35-n240-right`. The smallest is nut `step` bytes, e = 0.380. Every value is listed in the table.

## The candidates (07-BUDGET-TABLE.md)

- **C1:** keeps all 294 bolt and 14 nut catalogue rows by construction. The budgets are (bytes, s, peak):
  - stl-preview: (5.57e7, 34.13, 1.05e9)
  - stl-fine: (2.40e8, 94.43, 2.93e9)
  - step: (9.75e6, 15.00, 4.22e8)
  - Repr values are in the table.
- **C2:** peak 4e9 at every artifact.
- **C3:** Q = 1277373727.3382857 bytes at `stl-fine`. rho = 3.1314 comes from `explore:bolt-d100-p10-n240-right`, a 240-turn part past the 90-turn wall. R13 selects among all-ok points and applies no wall filter.
- No candidate refuses a catalogue row.

## Verification

- `make test PYTEST_ARGS="tests/test_oper_fit.py -q -n0 --no-cov"`: 25 passed.
- `python -m bench.oper_fit fit ... --out /dev/stdout | cmp - bench/results/phase-07/fit.json`: no output, exit 0.
- `grep -c "^## C[123]" 07-BUDGET-TABLE.md`: 3. Running the table CLI again and diffing it against the committed file: no difference.
- The fit.json acceptance one-liner lists bolt and nut for each of `step`, `stl-fine` and `stl-preview`. Run ids `{'explore': ['40646117094'], 'spread': ['40646125666']}`.
- Pre-commit `make verify` passed for both commits. The task 2 commit failed once, on the known flake `tests/test_pool.py::test_a_request_queued_behind_a_build_keeps_its_own_full_timeout` alone (1 failed, 4335 passed), and passed on the one allowed retry.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The envelope's ulp loop stepped `e` instead of `1 + e`**
- **Found during:** Task 1 (the noise-free test hung)
- **Issue:** `nextafter(0.0, inf)` is 5e-324, and that leaves `1 + e` at 1, so the coverage loop never ended.
- **Fix:** step the factor `1 + e` by its own ulps, then set `e = factor - 1` (exact for these factors).
- **Commit:** 5b5fd58

**2. [Plan interface] The `table` CLI also takes `--spread`**
- **Issue:** the plan names `table --fit --explore --out`, but C3's rho is chosen among explore *and* spread points (R13).
- **Fix:** `--spread` added. The table reads fit.json for the models and the records for the populations and rho.

**3. [Plan wording] The target names in fit.json**
- The targets are written `bytes`, `seconds` (build_s + export_s) and `peak` (cgroup `memory_peak_bytes`), in R13's triple order.

**4. [Test scope] No byte-compare of the committed table or fit.json inside `make verify`**
- CI runs `make verify` on ubuntu. There, numpy uses OpenBLAS and libm's `exp` may differ by an ulp, while the files were written on macOS. The gate therefore refits the committed records and compares the coefficients and envelopes to 1e-9 relative, with every other field exact. The byte checks (`cmp`, `diff`) were run as plan verifies on the machine that wrote the files.

**Total deviations:** 1 auto-fixed bug, 3 interface or scope notes. **Impact:** no figure moved. The envelope is R12's value or a few ulps above it.

## For the owner (not decided here)

- Every candidate admits some in-wall free-space parts whose explore reading is not `ok`. The table's last column counts them per artifact.
  - **Refused with `BuildError`:** 20 such parts, 60 readings.
  - **Capped at the 12 GiB cap:** under C3 at `stl-fine`, 5 parts.
  - Both are logged in `deferred-items.md`. No cause was investigated.
- C3's rho comes from a part past the turn wall, as R13 reads.
- The D-06 evidence shows that raising the pitch on its 0.05 step admits most refused parts whose pitch is at default. Some d 300 bolts at 30 turns have no admitting pitch under C1.

## Known Stubs

None.

## Threat Flags

None. The fit reads committed files only, and the provenance guard (T-07-24) and the excluded list (T-07-62) are tested.

## Self-Check: PASSED

Files found: bench/oper_fit.py, tests/test_oper_fit.py, bench/results/phase-07/fit.json, 07-BUDGET-TABLE.md, deferred-items.md. Commits 5b5fd58 and 90f4c0a are ancestors of HEAD.
