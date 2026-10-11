# The in-process pair tests in tests/test_bench.py end the pytest process with exit 139

Severity: must
Status: active
Date: 2026-10-10
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
exit. ASSUMPTION: that is also the cause here; the faulting frame was not captured.

## Why it matters
Any script or CI step that runs the bench tests serially, or a developer running the documented
`make test PYTEST_ARGS="... -n0"` form for `-x` or `--pdb`, sees a failing exit status on a green
run, and a real failure at exit would be indistinguishable from it.

## Next step
Revisit when a serial run of the bench tests is wanted in a script or CI. Smallest fix: keep the
boolean and filler alive for the process in the tests as `pair._KEEP` does in the worker (it is
filled by `common`, so check that the tests do not clear it), or run those tests through a worker
subprocess. Capture the faulting frame with `python -X faulthandler` first.

<!-- On resolve: set Status: resolved, add `Resolved in: <commit sha>`,
     git mv into resolved/, move the INDEX row to Resolved — same commit as the fix. -->
