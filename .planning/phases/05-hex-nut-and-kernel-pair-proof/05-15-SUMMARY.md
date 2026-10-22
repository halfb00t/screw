---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 15
subsystem: cli
tags: [pair-proof, cli, exit-codes, verify-cell, pair-tier, workflow, pair-03, pair-04]
requires:
  - phase: 05-14
    provides: "screw.solid.pair.prove, PairReport, the import-boundary contract"
  - phase: 05-01
    provides: "tests/data/pair_expected.tsv, the 240 pre-registered verdicts"
provides:
  - "screw pair nut: flags generated from NutParams, PairReport JSON on stdout, exit 0 proven / 1 violated / 2 inconclusive"
  - "the verify cell (M6 right hand c = 0.10, m 5.2) in make verify, in a child process, equal to the table's proven"
  - "the pair-marked tier: 240 cells, make pair [SIZE=], deselected by default, one child process and a 600 s deadline per cell"
  - ".github/workflows/pair.yml, outside ci.yml and required-jobs.txt, pinned by tests"
  - "draft PR #18 and the first ubuntu reading of the verify cell"
affects: [05-16, 05-17, 05-18]
requirements-completed: [PAIR-03, PAIR-04]
estimate_ref: "120000 tokens, 3 tasks"
actuals:
  tokens: 7000
  tasks: 3
  commits: 3
plan_head_before: daaf15975398293d174b0fdeec6ccf2a4c30c9c0
plan_head_after: c374150a5970d674cd90339ee918f7623d545b70
tech-stack:
  added: []
  patterns:
    - "a command whose process parked a kernel operation ends with flush + os._exit, and is tested only through child interpreters (RESEARCH F5)"
    - "the CLI offers `pair` for the kinds whose model declares a `clearance` field: the model decides, no kind name in the subparser loop"
key-files:
  created:
    - tests/test_cli_pair.py
    - .github/workflows/pair.yml
  modified:
    - src/screw/cli.py
    - tests/test_pair.py
    - tests/test_parity.py
    - tests/test_api.py
    - tests/test_grid.py
    - pyproject.toml
    - Makefile
key-decisions:
  - "The cell harness raises the nut's across-flats s to max(10, d + 2c + 1): the product default s = 10 mm is refused by NutParams for 94 of the 240 rows, and prove never reads s"
  - "make test prints the ten slowest tests, so a runner's duration for the verify cell is readable from the log"
status: complete
---

# Phase 5 Plan 15: screw pair, the verify cell and the pair tier Summary

`screw pair nut --clearance C` now asks the kernel whether the nut mates and answers in the exit code (0 proven, 1 violated, 2 inconclusive); the M6 right-hand c = 0.10 cell runs in `make verify` and was `proven` on ubuntu-latest, as pre-registered, with no rule, constant or table changed.

## Task commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | 24ed09f | feat(cli): add screw pair with exit codes 0 proven, 1 violated, 2 inconclusive |
| 2 | cbbb2fc | test(pair): add the verify cell and the pre-registered pair grid tier |
| 3 | c374150 | chore(test): print the ten slowest tests in the gate's log (needed to read the cell's seconds, see Deviations 2) |

`commits: 3` is measured from the plan-start ledger (`git rev-list --count daaf159..HEAD` before this summary).

## What was built

- **`screw pair <kind>`** (`src/screw/cli.py`). The subparser is added for each `KINDS` entry whose model has a `clearance` field (today `nut`); its flags are `_add_args` over the model and nothing else (no `--preset`: `kp.set_defaults(preset=None)` gives `_params` the attribute without a flag). `cmd_pair` runs `_params`, refuses with exit 2 and `error: pair: the nominal rod <root_radius_refusal text>` when the nominal rod's root is not above 0 (before the kernel is imported), then lazily imports `prove`, prints `report.model_dump_json(indent=2)`, flushes both streams and ends with `os._exit` (0, 1, 2 by verdict) as its last statement.
- **The printed report names the clearance** (`PairReport.clearance` is a field of the JSON), so the 05-14 note on the empty-control reason text needed no extra output.
- **Measured by hand with the real kernel:** `screw pair nut --clearance 0.1` exits **0** in 64 s with the shipped-row evidence (verdict `proven`, controls 12.2130 mm3 at all three poses against the closed form 12.2130, matched poses 0, shipped rows 0 solids); the stderr is empty and the status is not 139. `--clearance 0` exits 2 with `readings: []` in 1.7 s.
- **Tests, none calls the entry point on the real `prove` in the pytest process** (`grep -n 'main(\["pair"' tests/*.py` prints nothing). `tests/test_cli_pair.py`: subprocess exit codes for nut_too_thin (exit 2, stderr only, under 5 s), c = 0 (exit 2, stdout a `PairReport` with `inconclusive` and `readings == []`), no clearance (exit 2 naming it), `pair bolt` (exit 2, invalid choice), and a nominal rod with no root (`--d 2 --pitch 2 --clearance 0.5`: the nut's void root is 0.4175 mm so the nut is valid and only the proof refuses); a fresh `-I` interpreter shows `cadquery` and `OCP` absent from `sys.modules` after each of the three refusals; the 0/1/2 mapping in process with `prove` and `os._exit` replaced, reading stdout at the moment of exit to prove the JSON is out first. `tests/test_parity.py`: the pair flags equal the model's exactly, the offered kinds are `["nut"]`, a planted stray flag fails the comparison. `tests/test_api.py`: no `/openapi.json` path and no app route contains `pair`, and `GET /api/nut/pair` is 404.
- **The verify cell** (`tests/test_pair.py::test_the_verify_cell_is_proven_as_pre_registered`, unmarked): the table's `M6-right-c0.1` row (m 5.2) through `prove(..., shipped=False)` in a child interpreter ending in `os._exit(0)`; a timeout, a non-zero exit or output that is not a `PairReport` fails the cell. A second unmarked test pins the row to d 6.0, pitch 1.0, m 5.2, `proven`.
- **The pair tier**: `test_pair_cell` marked `pair`, 240 items (verified by `--collect-only -m pair`, `240/333 tests collected`), ids `<size>-<right|left|mixed>-c<clearance:g>` (`M6-right-c0.1`, `M6-left-c0.1`, `M6-mixed-c0.1`, `M6-right-c0`, `M6-right-c-0.05` all present), deadline `bench.thread_spike.verdict.PAIR_TIMEOUT_S` (600 s, imported not retyped). Every cell appends a line (id, expected, report, wall seconds) to `bench/results/phase-05/pair-<size>.jsonl`; a failed, killed or dead cell appends an `error` line and then fails. A test pins that `-k 'M2-'` selects exactly its 16 cells and never M12 or M2.5.
- **`pyproject.toml`**: `addopts` is `-m 'not grid and not pair'`, the `pair:` marker is registered; `tests/test_grid.py` asserts the new substring. **`Makefile`**: target `pair` (and `.PHONY`).
- **`.github/workflows/pair.yml`** copies `grid.yml`: `workflow_dispatch` plus `23 4 * * 1`, `permissions: contents: read`, no `pull_request`/`push`, no secrets, a matrix equal to `maths.SIZES`, `make pair PYTHON=python SIZE=${{ matrix.size }}`, `timeout-minutes: 240`. Tests pin each of these and that `make pair` / `-m pair` are absent from `ci.yml` and no `pair` job is in `required-jobs.txt`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's cell harness cannot build 94 of the 240 nuts**
- **Found during:** Task 2, before writing the harness.
- **Issue:** the plan builds `NutParams(d, pitch, m, clearance, left_hand=...)` with `s` at its default of 10 mm. `NutParams._nut_too_thin` refuses a nut whose `s` does not exceed `d + 2c`, which is true for 94 of the 240 table rows (M10 and above at the larger clearances, M12 to M20 throughout). Measured by constructing all 240 rows.
- **Fix:** the child passes `s = max(10.0, d + 2c + 1.0)`: the product default wherever it already suffices (every M6 row, so the verify cell is the product's own nut), and 1 mm clear of the void otherwise. All 240 rows then validate. `prove(..., shipped=False)` builds no bolt and does not read `s`, so no verdict input changes. The comment in `_CELL_CHILD` says so.
- **Files modified:** `tests/test_pair.py`. **Commit:** cbbb2fc.

**2. [Rule 2 - Missing critical functionality] The cell's seconds on ubuntu were not in the CI log**
- **Found during:** Task 3. The first run's log has `3334 passed` and nothing per test (`pytest -q`, no durations), so the acceptance criterion "the SUMMARY states the verdict and seconds" could not be met from it, and T-05-35 says the cell is "measured locally and on ubuntu".
- **Fix:** `--durations=10` in the `test` target of the Makefile (one flag, a comment giving the reason). CI ran again on the push; the number below is read from that log.
- **Commit:** c374150.

**3. [Interpretation] `cmd_pair` casts the parsed kind to `NutParams`**
- `prove` takes a `NutParams`; `_params` returns `FastenerParams`. The one `cast` is in `cmd_pair`, and the kind decision stays in the model (`"clearance" in model.model_fields`). A second kind with a clearance would need `prove` generalised first.

## The ubuntu reading (Task 3)

Draft PR **#18**: https://github.com/halfb00t/screw/pull/18 (draft, open, against `main`). No skip token. Two runs of `ci.yml` on the PR head, all three required jobs green in both.

| Run | Head | `test (3.12)` | `image` | `vendor-bundle` |
| --- | ---- | ------------- | ------- | --------------- |
| https://github.com/halfb00t/screw/actions/runs/39428789949 | cbbb2fc | pass, 12m26s (`3334 passed in 681.73s`) | pass 1m51s | pass 10s |
| https://github.com/halfb00t/screw/actions/runs/39431329111 | c374150 | pass, 16m28s (`3334 passed in 922.00s`) | pass 2m21s | pass 11s |

- **Verdict of the verify cell on ubuntu-latest: `proven`**, equal to the pre-registered row. The test `test_the_verify_cell_is_proven_as_pre_registered` asserts exactly that equality and passed in both runs. The stop rule (verdict not `proven`) did not trigger.
- **Seconds:** the first run's log does not carry it. The second run's log (`--durations=10`, `cadquery 2.8.0 cadquery-ocp 7.9.3.1.1`): **167.50 s** for the cell, with 4 vCPU runner workers running the rest of the suite beside it. Locally the same test is 42.55 s alone and about 35 s per RESEARCH F5, so the runner is about 4x slower under load (RESEARCH A1 predicted 3-4x).
- **For the owner, not acted on (T-05-35):** the required job went from 3 to 7.5 min on earlier runs (e.g. run 38592222792, 7m33s) to **12m26s and 16m28s**. The durations list names the cost: `test_the_expected_verdicts_are_re_derived_from_the_recorded_pair_campaign` took **300.34 s** on the runner against 13.6 s here (a kernel-free test, 22x), the verify cell 167.50 s, the 05-14 shipped child test 78.97 s, and four pre-existing tests 67 to 93 s. The runner's seconds vary a lot between runs (681 s then 922 s for the same suite). Nothing was trimmed or moved under a marker; R14 accepted a local verify above 90 s, the CI job time has not been ruled on.

## Measured facts

- **`make verify` (before the Task 2 commit):** `3334 passed in 150.93s (0:02:30)` (wall 2:31.58), coverage **97.32 %** against the 96.0 % floor. Host busy, so slower than 05-14's 132.94 s; the plan estimated about 35 s for the cell, and it ran in parallel with the rest. All three task commits passed the pre-commit `make verify`.
- **`make pair SIZE=M6`:** `16 passed in 128.34s (0:02:08)` on 8 workers. Every verdict equals the table: 4 `inconclusive` (c = 0 and c = -0.05, both hands, 2.1 to 2.2 s each, no booleans), 8 `proven` (right and left at c = 0.05 to 0.2, 31 to 64 s each), 4 `violated` (mixed at 0.05 to 0.2, 26 to 37 s each). The full grid is 05-16's. The local results file was removed after reading (a copy is in the scratchpad) so 05-16's full run does not append to stale lines; it is not committed.
- **First wrong form in my own work, fixed before the first commit:** ruff's PT018 and ARG005 and one mypy `BaseRoute.path` error; the Task 1 commit was rejected by the hook once and recommitted after the fixes.

## Known Stubs

None.

## Threat Flags

None. T-05-33 mitigated (flush then `os._exit`, subprocess tests for 2, the in-process 0/1/2 test, and one real-kernel run exiting 0), T-05-34 mitigated (`pair.yml` pinned: no `pull_request`/`push`, read-only token, no secrets), T-05-35 measured on both platforms and surfaced above; no stop rule was reached.

## Notes for 05-16 and later

- `make pair` appends to `bench/results/phase-05/pair-<size>.jsonl`; the directory does not exist until a run creates it. Delete a size's file before re-running that size.
- Debt or ideas filed: none.

## Self-Check: PASSED

- FOUND: src/screw/cli.py, tests/test_cli_pair.py, tests/test_pair.py, .github/workflows/pair.yml, Makefile, pyproject.toml
- FOUND commits: 24ed09f, cbbb2fc, c374150 (each an ancestor of HEAD)
- `gh pr view 18`: draft true, state OPEN; `gh pr checks 18 --required`: all pass
