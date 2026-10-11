# The in-process pair tests in tests/test_bench.py end the pytest process with exit 139

Severity: must
Status: resolved
Date: 2026-10-10
Resolved in: test(bench): read pair.common only in a child so the pytest worker exits clean (this commit; the next commit names its sha)
Source: plan 03-06 Task 1 verification (`make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov"`)
Related files:
- bench/thread_spike/pair.py (`_KEEP`, `common`)
- tests/test_bench.py (the pair block, "The pair builder, the pair block and smoke --pair")

## Context
Run serially, `tests/test_bench.py` reports `449 passed` and then the interpreter dies with
SIGSEGV (exit 139, "Segmentation fault: 11" from make). It does so on HEAD `85b08ee`, before
plan 03-06 touched anything (checked on a `git archive` copy of that commit), so the import-back
did not cause it. `-k "common or pair or place or nut or rod_piece"` (52 tests) reproduces it
alone; the 12 tests that build real rods and one-pipe twists without the pair boolean exit 0.
`make verify` runs `-n 8` and exits 0. `pair.py` already records the cause it saw in the
harness: freeing the `BRepAlgoAPI_Common` and its filler segfaulted at teardown (RESEARCH
Pitfall 4), which is why the worker ends with `os._exit(0)`; the in-process tests have no such
exit. The macOS crash report of 2026-10-11 confirms the cause: SIGSEGV in
`BRepAlgoAPI_BuilderAlgo::~BRepAlgoAPI_BuilderAlgo` under `tupledealloc` <- `list_dealloc` <-
`_PyModule_ClearDict` <- `Py_FinalizeEx`, that is module teardown freeing `pair._KEEP`, which
only the in-process test
test_common_reads_the_volume_of_an_overlap_and_zero_solids_for_a_disjoint_pair filled. With it
deselected, the other 51 tests of the block exit 0 (`-n0`, 2026-10-11).

## Why it matters
Any script or CI step that runs the bench tests serially, or a developer running the documented
`make test PYTEST_ARGS="... -n0"` form for `-x` or `--pdb`, sees a failing exit status on a green
run, and a real failure at exit would be indistinguishable from it.

## Next step
Revisit when a serial run of the bench tests is wanted in a script or CI. Smallest fix: keep the
boolean and filler alive for the process in the tests as `pair._KEEP` does in the worker (it is
filled by `common`, so check that the tests do not clear it), or run those tests through a worker
subprocess. Capture the faulting frame with `python -X faulthandler` first.

## Resolution (2026-10-11)

- The in-process test is deleted. Its checks (volume approx 1.0, one solid, both filler flags
  False, a positive time, the disjoint pair's `(0.0, 0)`) are now read from a child by
  `test_a_child_that_read_a_pose_comes_back_with_exit_0_the_way_the_worker_ends`, whose exit
  code stays the behaviour under test.
- No test calls `common` in the pytest process. The remaining `run_pair` callers stub it, fail
  before the boolean, or run in a `Worker` child that ends with `os._exit(0)`. pair.py now says
  so next to `_KEEP`.
- Measured after the fix: the pair block (`-k "common or pair or place or nut or rod_piece"`,
  `-n0 --no-cov`, `-X faulthandler`) gives `51 passed`, rc 0 and no fatal line (`52 passed`
  then `Fatal Python error: Segmentation fault`, rc 139 before). The whole of
  tests/test_bench.py at `-n0 --no-cov` gives `448 passed` and rc 0 (449 tests before; one
  deleted).
- `pair.common`, the `_KEEP` hold and the worker are unchanged.
