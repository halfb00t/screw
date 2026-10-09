---
phase: 02-thread-spike
reviewed: 2026-10-09T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - bench/quiet.py
  - bench/thread_spike/__init__.py
  - bench/thread_spike/__main__.py
  - bench/thread_spike/helical.py
  - bench/thread_spike/maths.py
  - bench/thread_spike/measure.py
  - bench/thread_spike/pair.py
  - bench/thread_spike/runner.py
  - bench/thread_spike/verdict.py
  - bench/thread_spike/worker.py
  - tests/test_bench.py
  - Makefile
  - pyproject.toml
findings:
  critical: 0
  warning: 5
  info: 7
  total: 12
status: issues_found
---

# Phase 2: Code Review Report

**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

I read all thirteen files in full. The first four warnings below are all places where the harness could read a record that is not the one the protocol means. None of them changed the recorded campaign `2026-10-08-a`.

- **Row and cell classification:** I found nothing that makes a recorded number wrong. The classifier in `verdict.py`, the closed-form maths and the STL check hold up.
- **Real campaign data:** I only grepped the `.md` reports, never the JSONL. `2026-10-08-a-pair.md` has no timeout, failure or worker_died cells. Its names match the `{prefix}-{block}` pattern.
- **Test suite:** I found nothing in `tests/test_bench.py` that threatens reliability. Real git is used only against a throwaway bare repo. Real-time tests use sleeps of 0.5 s against a 60 s child.
- **`Makefile` and `pyproject.toml`:** no defects.

Per D-19, every item is for a follow-up PR.

## Warnings

### WR-01: `verdict --campaign PREFIX` also reads campaigns whose prefix merely extends PREFIX

**File:** `bench/thread_spike/__main__.py:1375` (also 1379-1389)
**Issue:** The glob is `results_dir.glob(f"{prefix}-*.jsonl")`, and `*` matches `-` and anything else.
- Prefix `c1` picks up `c1-ksweep.jsonl` and also `c1-x-ksweep.jsonl`. I confirmed this with a scratch directory.
- Prefix `2026-10-08` therefore reads every block of `2026-10-08-a`.
- Once a second campaign such as `2026-10-08-a-2` exists, verdict on `2026-10-08-a` sees two runs per block and refuses with exit 2.
- If the shorter prefix has no run of a block, the longer campaign's run is silently adopted as that block.
- `_read_runs` also trusts `header["block"]` over the file name, so a file named `P-grid.jsonl` that holds a ksweep header is read as the ksweep.

`run_campaign` checks only the exact names `PREFIX-<block>.jsonl`, so it does not prevent nested prefixes. The output header does print the run ids. Nothing enforces them, though, and `test_the_verdict_only_reads_runs_under_its_own_prefix` uses unrelated prefixes `c1` and `c2`, so it never exercises this.
**Fix:** Match exactly the names a campaign writes, and require the header to agree with the name.
```python
paths = [results_dir / f"{prefix}-{b}.jsonl" for b in CAMPAIGN_BLOCKS]
for path in (p for p in paths if p.exists()):
    ...
    if header["block"] != path.stem.removeprefix(f"{prefix}-"):
        raise ValueError(f"{path.name} holds a {header['block']} run")
```

### WR-02: `--k-from` and `--frontier-from` accept incomplete records

**File:** `bench/thread_spike/__main__.py:1142-1154` (`_locked_k`), `1118-1126` (`_frontier_rows`), `537-551` (`_frontier_terminals`)
**Issue:** `run_block` takes the locked K from whatever rows the named ksweep JSONL holds, with no `block_gaps` check. The rss block takes its "terminal rows" from the maximum turn count in whatever the named frontier JSONL holds.
- `run_campaign` protects the in-order path through `_NEEDS`. The standalone `run <block> --k-from X` path, which the CLI docstring documents, has no such guard.
- A ksweep that crashed after K=3's rows would select K=3 from half a sweep.
- A header-only ksweep returns `DEFAULT_K` with the source string "no K qualified under the rule (escape clause)", which is false for an empty file.
- A partial frontier walk makes the rss block measure its mid-walk row as a "frontier terminal".
- `verdict` later refuses the incomplete ksweep, so the final verdict is safe. The recorded block and its `k_source` header are still wrong, and the cost is a re-run.
- `_frontier_terminals` calls `SIZES.index` on a row's size, and that call is outside the `try` in `run_block`. An edited or foreign frontier file therefore crashes the rss block after its header is written.

**Fix:** Check `block_gaps("ksweep", header, rows, sizes=SIZES, sample_sizes=SAMPLE_SIZES)` in `_locked_k`, and `block_gaps("frontier", ...)` (or at least `mislabelled_rows`) in `_frontier_rows`. On a gap, raise `ValueError("... is incomplete: ...")`, which `run_block` already turns into exit 2. Also require the frontier run's header `k` to equal the locked K.

### WR-03: The quiet gate decides `decisive` once, at the start of each block

**File:** `bench/quiet.py:52-79`, `bench/thread_spike/__main__.py:1218-1221, 1112`
**Issue:** `Campaign.decisive` is fixed from the release at the start of the block.
- A grid or frontier block runs long enough for the host to get busy part-way through.
- Nothing re-reads the load during the block, and the end reading is labelled "includes this run's own load" and is never used.
- A block that went noisy half-way therefore still carries `decisive: true` in its header.
- Every timing claim that depends on it is then treated as established: the seconds cap, the 30 s frontier stop, the estimator tie-break, and over-budget.
- This is the failure D-17 and owner ruling R4 exist to prevent. They guard the start of the run but not its duration.

**Fix:** Take a load reading between rows, for example every N rows or per size. Record the readings in the JSONL. Downgrade the block's `decisive` to false if any reading is at or above `QUIET_BAR` before a timing-bearing row. This also needs a pre-registered rule.

### WR-04: A mixed-hand cell reads "violated" without the nut body being checked

**File:** `bench/thread_spike/verdict.py:1589-1597` (compare 1604-1610)
**Issue:** For same-hand cells, `cell_verdict` refuses to believe any reading when the recorded `nut_volume` misses `pi d^2 m - A(c) m` by more than `T_PASS`. The stated reason is "not even a violation". The mixed-hand branch returns before that check.
- A nut whose void cut silently failed (an intact cylinder) overlaps the rod at every pose and reads non-empty at all three matched poses.
- That reads as `violated` and satisfies `mixed_hand_violated`, the D-14 criterion that a mixed pair must read violated, on garbage.
- In practice the identical left-hand nut also appears in the left/left same-hand cell at every proof clearance. That cell is guarded, and the build is deterministic, which makes the risk small.
- Nothing in the code ties the two together, so the mixed verdict does not stand on its own evidence.

**Fix:** Run the nut-body check before the `_is_mixed` branch, so it covers both cases.
```python
body = _nut_body(record)
if nut_volume is None or abs(nut_volume / body - 1.0) > T_PASS:
    return "inconclusive", (...)
```
`_nut_body` does not depend on hand, and the pair record carries `nut_volume` for every built cell.

### WR-05: A run is recorded under the HEAD sha without checking the harness is committed

**File:** `bench/thread_spike/__main__.py:183-205` (`read_guard`), `1223-1227` (header)
**Issue:** The guard compares the protocol text with `origin/main`'s and checks the protocol commit is an ancestor of HEAD. The header then records `git rev-parse HEAD` as `head`. Nothing checks that the working tree matches HEAD.
- An uncommitted edit to `T_PASS`, `PAIR_BAND` or `helical.py` runs under a clean-looking sha.
- That defeats "fixed before any data" and "never tuned toward a pass".
- The protocol file is compared from the working tree, so even that file only has to match `origin/main`, not HEAD.

**Fix:** In `read_guard`, run `git status --porcelain -- bench pyproject.toml .planning/phases/02-thread-spike/02-SPIKE.md`. If it prints anything, add a reason to the guard such as "working tree has uncommitted changes to the harness". Alternatively, record a `dirty` flag in the header and make the verdict mark such runs non-decisive.

## Info

### IN-01: `_head()` has no `cwd` and is read after the run

**File:** `bench/thread_spike/__main__.py:226-230`, `1133`, `1244`
**Issue:** `_head()` calls `subprocess.run(["git", "rev-parse", ...])` without `cwd=_REPO_ROOT` and with `check=True`. Every other git call uses `_git`. Run from another directory with `PYTHONPATH` set, the `.md` "HEAD" line is the other repository's HEAD, or a `CalledProcessError`. It is also evaluated when the report is built, after the run, and not at start where `facts.head` is read.
**Fix:** Use `_git("rev-parse", "--short", "HEAD")` and take the value once, at start.

### IN-02: `PAIR_TIMEOUT_S` does not follow from the numbers in its own comment

**File:** `bench/thread_spike/verdict.py:1329-1331`
**Issue:** The comment cites 16-121 s per M20 boolean, with six booleans per cell. Six times 121 s is 726 s, plus the rod and nut builds, against a 600 s deadline. A slow M20 cell would be killed and recorded as an inconclusive timeout. `2026-10-08-a-pair.md` shows no timeouts, so this is latent.
**Fix:** Derive the deadline from the cited worst case, or cite the measurement that justifies 600.

### IN-03: A bad request line kills the worker instead of returning a failure record

**File:** `bench/thread_spike/worker.py:246-263`
**Issue:** `_is_pair` calls `json.loads`, and `parse_request` and `parse_pair_request` raise `ValueError`, all outside any `try`. The parent builds every request itself, so this is unreachable today. If it were reached, the child would die with a traceback and the parent would record `worker_died`, which fails the pass bar. A harness bug would then read as a kernel death.
**Fix:** Catch `ValueError` in `main` and answer with a one-line failure record, or let the parent label it a protocol error.

### IN-04: The status returns of `Build`, `MakeSolid` and `VolumeProperties_s` are ignored

**File:** `bench/thread_spike/helical.py:74-76`, `bench/thread_spike/measure.py:40-42`
**Issue:**
- `pipe.MakeSolid()` and `pipe.Build()` results are discarded. A failed `MakeSolid` leaves a shell wrapped in `cq.Solid`, which then shows as `solids=0` and `silent_wrong`, so it is caught downstream. In `pair.nut`, a shell used as a cut tool is caught only by the nut-body check.
- `BRepGProp.VolumeProperties_s` returns the achieved error estimate. It is dropped, so a non-converged integration is not distinguishable from a converged one. The closed-form comparison catches a wrong value.

**Fix:** Check `pipe.MakeSolid()` and `pipe.IsReady()` and raise on failure. Record or compare the returned estimate against `PRECISE_EPS`.

### IN-05: The oracle docstring overclaims independence from the builder

**File:** `bench/thread_spike/maths.py:3-5`, `bench/thread_spike/helical.py:23`
**Issue:** The `maths` docstring says the closed form "must share no code path" with the kernel. The contract forbids only importing cadquery and OCP. `helical.section`, `trim_tip` and `naive_sweep_fuse` import `thread_depth` from `maths`, and the profile angles are re-typed in two places. A wrong 5/8 factor would be common-mode, so the volume check would pass while both were wrong against ISO.
**Fix:** Reword the docstring to say the oracle shares the pinned profile parameters. Add a test that pins `thread_depth` against an independently written value.

### IN-06: An oversized integer in an edited JSONL escapes the refusal path

**File:** `bench/thread_spike/verdict.py:196-202`
**Issue:** `_num` calls `math.isfinite(value)` on an `int`. `10**400` raises `OverflowError`, which is not a `ValueError`. I confirmed that `parse_header` raises it. The header `readings` list goes through `_num`, so a tampered file crashes `verdict_campaign` with a traceback instead of the documented exit 2, where T-02-09 is meant to "refuse" it. The campaign's own files are not affected.
**Fix:** Test `isinstance(value, float)` or catch `OverflowError` and call `_refuse`.

### IN-07: The reference worker's kernel is not recorded

**File:** `bench/thread_spike/__main__.py:1056-1071`
**Issue:** `PYTHONPATH` puts the scratch directory first. A package installed there with its dependencies would shadow the parent's `cadquery`/`OCP`. The probe checks only that `cq_warehouse.thread` imports. `_environment_lines` reports the parent's kernel versions. The ruled rows are evidence only, not accuracy claims.
**Fix:** Have the probe print `OCP.__file__` and the `cadquery` version from the child, and record them in the controls run's notes.

---

_Reviewed: 2026-10-09_
_Reviewer: Claude (gsd-code-reviewer, sonnet), dispatched by the execute-phase code-review hook; the agent returned the report inline and the orchestrator saved it verbatim_
_Depth: standard_
