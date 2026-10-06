# bench.memory samples too coarsely to read a peak off a corpus that runs in seconds

Severity: must
Status: active
Date: 2026-10-06
Source: 01-08 harness check on the walking skeleton (bench/RESULTS.md, "Container memory sweep")
Related files:
- bench/memory.py (`_poll_peak_mem`, `_sweep_one`)
- bench/RESULTS.md (Container memory sweep)

## Context
`bench.memory` is ported from spur with its method intact: it polls `docker stats --no-stream`
in a thread for the length of the corpus run and reports the maximum reading. One reading takes
longer than the 0.5 s `POLL_INTERVAL`, and the skeleton corpus (12 plain cylinders) runs in 6 to
22 s, so the first sweep got 4, 6 and 12 readings for N = 1, 2, 4. The peak fell in the second
half of the readings in every row and N=1 read higher than N=2 (1323 against 981 MiB), so those
figures are not a footprint. The harness prints the sample count per row so the reader can see
this, and RESULTS.md says so; it does not refuse a row for having few samples.

spur's corpus (40 gears, minutes) never met the limit. A threaded part's grid might not either
if the builds are fast.

## Why it matters
Phase 7 sets `mem_limit` (OPER-03) from this sweep. A peak read off a handful of samples can
under-state the real one and size a limit that the container then hits (an OOM kill is a 503
`pool_broken` for the user, not a slow answer).

## Next step
Before the Phase 7 sweep: read the cgroup's own `memory.peak` (or `memory.max_usage_in_bytes`)
through `docker exec` once at the end of the run, which is exact where `docker stats` is sampled,
or refuse a row below a stated sample count the way `bench.latency` refuses a p95 under 20
samples (`MIN_SAMPLES`). Pick one with the owner when the Phase 7 corpus lands; the image runs as
a non-root `nologin` user, so check `docker exec` works without a shell first.

<!-- On resolve: set Status: resolved, add `Resolved in: <commit sha>`,
     git mv into resolved/, move the INDEX row to Resolved — same commit as the fix. -->
