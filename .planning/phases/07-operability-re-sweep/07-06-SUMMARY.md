---
phase: 07-operability-re-sweep
plan: 06
subsystem: testing
tags: [operability, contention, drift, arenas, runs-ii, buildpool, cgroup]

requires:
  - phase: 07-operability-re-sweep
    provides: "07-05: the R6 shards and the oper_sets generator; 07-07: the measured walls (L20) the production model validates against"
provides:
  - "bench.oper_bound: build_task, run_member, contention (R14), drift and arenas (R23), read_current, vm_rss_bytes, main"
  - "bench.oper: point kinds contention (workers, points with slot), drift (part, k, deadline_s) and arenas (part, trim), run by bench.oper_bound; reading_argv(..., module=...)"
  - "bench.oper_sets: pool_slot, bound_smoke(); bench/points/bound-smoke.json, generated and covered by --check"
  - "a successful runner smoke of the three instruments (run 40700137932), a path check that sets nothing"
affects: [07-08, 07-15, 07-16]

actuals:
  tokens: 17216   # chars/4 over the added lines of bench/ and tests/ across the three commits
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count 1555261..2a0916b
plan_head_before: 155526162ad232af881d2345e9f7e5d6cce8a4f7
plan_head_after: 2a0916bb8122ab83850b2ae95cd2e86b9030c417   # before this SUMMARY's own commit

tech-stack:
  added: []
  patterns:
    - "a Runs II child (bench.oper_bound) may report killed and crashed itself; the parent tests its line against the cap before taking the child's status (R2's order)"
    - "a contention reading routes every point through BuildPool.executor_for and checks the set's slot, and each build's worker pid, before it yields a number"

key-files:
  created:
    - bench/oper_bound.py
    - bench/points/bound-smoke.json
    - tests/test_oper_bound.py
  modified:
    - bench/oper.py
    - bench/oper_sets.py
    - tests/test_oper.py

key-decisions:
  - "An arena reading reads memory.current and VmRSS right after the export returns, before the level-1 gzip and the peak (G17 says 'read after the export'; the peak stays after the gzip as R2 says)"
  - "A trim-on arena reading where malloc_trim cannot load is not taken (RuntimeError, recorded crashed): it would be a trim-off reading under the wrong name"

requirements-completed: []   # OPER-01 and OPER-02 advance; neither is wholly done (the Runs II sets, the timeouts, mem_limit and the rest are later plans)

duration: about 30 min of work plus one runner job
completed: 2026-10-28
status: complete
---

# Phase 7 Plan 06: The Runs II instruments Summary

**`bench.oper_bound` runs R14's contention reading (P plus one cold partner per worker, routed by `executor_for`, each submitted once) and R23's drift and arena readings in the production image. The parent knows the three point kinds, and a generated smoke set read `ok` in all 5 readings on the runner (run 40700137932).**

## What was done

1. **Task 1 (tracer), `f836e80`.** `contention(points, workers, deadline_s, *, artifact, task, read_peak, oom_kills)`:
   - A `BuildPool(N, {a: deadline_s})` is built and every slot is warmed first (each worker's pid is kept).
   - All N points are then submitted together, once each, through `pool.executor_for(p)`.
   - The set's `slot` is checked against `hash(p) % N` before anything is built. A mismatch is `crashed`, with both slots in the message.
   - Each build's pid is checked against its slot's warm pid.
   - Each build times its own build, export and level-1 gzip in the worker (`build_task`).
   - The peak is read once, after all N builds end.
   - A build still running at the deadline makes the reading `killed`, and its process is terminated, as the pool's own timeout branch does it.
   - The status order is: `no_cgroup`, then `crashed` (any exception that is not a kernel refusal), then `refused` (class and text), then `ok`.
   - A set that is not one point per slot 0 to N-1 raises a `ValueError` naming R14.
   - In `bench/oper.py`: the contention kind (N in 1 to 3, P first, distinct slots, exact keys), `reading_argv(..., module=)`, and `bench.oper_bound` as the child for these points. A Runs II line is tested against the cap before its own status is taken.
2. **Task 2, `eb81392`.** `drift`:
   - K builds in one process, with `clear_cache()` before each.
   - Each build is followed by its export, a level-1 gzip and a peak read (G14).
   - It records the K peaks and build 1's `build_s`, `export_s` and `bytes`.
   - A refusal at any build, or an unreadable cgroup, leaves no peaks.

   `arenas`:
   - The trim is on, or `screw.solid._MALLOC_TRIM` is set to None for the call. It is restored in a `finally`.
   - `read_current` (cgroup v2 `memory.current` only; no v1 substitute) and `vm_rss_bytes` are read right after the export. Then come the gzip and the peak.

   In the parent: the drift kind (part, k at least 2, its own `deadline_s`, used in place of the set's) and the arenas kind (part, trim). `peaks`, `memory_current_bytes` and `vm_rss_bytes` must be whole numbers.
3. **Task 3, `2a0916b`.** `bench.oper_sets.bound_smoke()` and `pool_slot()`:
   - The set holds a contention at N = 2 (the default bolt on slot 0, the default nut on slot 1), a contention at N = 1, `drift-k3` (deadline 600 s), and `arenas-trim-on` and `arenas-trim-off`. All are the default bolt at `stl-preview`, with reps 1 and shards 1.
   - `generate()` and `--check` include it. `bench/points/bound-smoke.json` is written by the generator. No other point file changed.

## Runner smoke, path check only

Run **40700137932** (`operability: bound-smoke`, commit 2a0916b), conclusion `success`. One job, 5 readings: **ok 5**, and no other status.

- Every reading carries integer cgroup figures.
- Each contention build's recorded slot equals the slot its point names: `contention-n2` has bolt 0 and nut 1, and `contention-n1` has bolt 0.
- `drift-k3` carries 3 peaks.
- Both arena readings carry `memory_current_bytes` and `vm_rss_bytes`.

The artifacts were downloaded into the session scratch directory (`gh run download 40700137932 -p 'oper-*'`), not into the repository. Nothing is recorded under `bench/results/`, and no figure from this run is quoted here: the smoke sets nothing (L02).

## Verification

- `make test PYTEST_ARGS="tests/test_oper_bound.py tests/test_oper.py -q -n0 --no-cov"`: 430 passed after Task 2. After Task 3, with `tests/test_oper_followup.py` added: 529 passed.
- `make verify` passed in the pre-commit hook for each of the three commits. The flaky `tests/test_pool.py` queued-request test did not fire.
- `gh run list ... select(success and "operability: bound-smoke") | length` prints 1.
- `.venv/bin/python -m bench.oper_sets --check` exits 0.
- `ls bench/results/phase-07 | grep -c bound-smoke` prints 0.
- Acceptance greps:
  - `^def contention(`, `^def drift(` and `^def arenas(` each match once.
  - `executor_for` appears 3 times.
  - `_executors[` appears 0 times.
  - Non-comment lines with the word `failed`: 0.
  - Each commit subject matches the plan.
- Local path check (context only, Docker Desktop on the laptop): a two-worker contention of the default bolt and the default nut read `ok`, and a swapped-slot version read `crashed` with both slots named. Drift k 2 and arenas on and off read `ok`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] A Runs II line carries the peak for the parent's cap test**
- **Found during:** Task 1
- **Issue:** R2 makes `capped` the first status. A contention reading whose build was refused or crashed after the others ran could sit at the cap. If the child's `refused` were taken first, the reading would hide that.
- **Fix:** A non-ok contention line keeps `memory_peak_bytes` and `oom_kills`. `classify(..., bound=True)` applies the cap test before the child's status, then cuts the line to its reason as before. Part readings are unchanged.
- **Commit:** f836e80

**2. [Rule 2 - Correctness, T-07-59] Worker pid check**
- **Issue:** Matching `slot` against `hash(p) % N` does not prove that two builds ran in two processes.
- **Fix:** Each build returns its worker's pid (`run_member`), and it must equal the pid its slot was warmed in. Otherwise the reading is `crashed`.
- **Commit:** f836e80

**3. [Rule 2 - L02] A trim-on arena reading without `malloc_trim` is not taken**
- **Issue:** Where glibc's `malloc_trim` is not loadable (`_MALLOC_TRIM is None`), a trim-on reading would measure no trim and still be labelled "trim on".
- **Fix:** It raises `RuntimeError`, and the parent records `crashed`.
- **Commit:** eb81392

**4. [Rule 3 - Blocking] Generator tests list the smoke**
- **Issue:** `tests/test_oper.py` asserted that `generate()` lists exactly the four pre-registered sets, so adding `bound-smoke` would fail it. The file is not in Task 3's file list.
- **Fix:** Those two assertions now expect `(*SET_NAMES, "bound-smoke")`. The protocol's blob-sha pin and the R4 shape tests still cover the four sets only.
- **Commit:** 2a0916b

**5. [Plan wording] Local path check**
- The plan's step said to run it "under emulation" through `python3 -m bench.oper point`.
- I ran it on the laptop's native arm64 image, through `oper._load_point` and `run_reading` in a `python -c`: the `point` command takes part and probe flags only, and adding CLI surface for a one-off check would be speculative.
- It is a path check. No figure from it is used.

**6. Process.** Tests and code share one commit per task, because the hook runs `make verify` and a RED commit cannot land (as in 07-05).

## Needs the owner (not a halt of this plan)

**When an arena reading reads `memory.current`.** G17 says "read after the export". The instrument reads `memory.current` and `VmRSS` right after `export()` returns, before the level-1 gzip. R2 still puts the peak last, after the gzip. Reading after the gzip would also count the compressed buffer. If the owner meant "after the gzip", it is a one-line move in `bench/oper_bound.py` `arenas`, and it has to happen before 07-15 generates the arena set. I recommend keeping it as it is: it is the literal reading of G17 and leaves the transient gzip buffer out of the "retained" figure.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register:
- T-07-15: the same cap; contention and drift are cut at their deadlines.
- T-07-16: every field is validated, and the point is passed as one argv element.
- T-07-17: there is no scaling path; each N is its own container.
- T-07-59: the slot and the pid are checked.

## Debt

None filed. None resolved.

## Self-Check: PASSED

Files found:
- `bench/oper_bound.py`
- `bench/points/bound-smoke.json`
- `tests/test_oper_bound.py`

Commits f836e80, eb81392 and 2a0916b are ancestors of HEAD.
