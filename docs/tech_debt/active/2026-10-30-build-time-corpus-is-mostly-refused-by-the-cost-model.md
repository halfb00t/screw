# The build-time corpus is mostly parts the cost model refuses, so the bench judges little

Severity: nice
Status: active
Date: 2026-10-30
Source: plan 07-17, deviation 2. The owner accepted the skip and asked for this item on 2026-10-30.
Related files:
- bench/corpus.py:22 (`corpus`)
- bench/build_time.py:124 (a refused artifact is printed as `refused (L21)` and not judged)
- src/screw/calc/cost.py (`fits`, `refusal`)

## Context
Since 07-17 (530adbe), `bench.build_time` marks a corpus artifact that the cost model refuses as
`refused (L21)`. It does not judge that artifact against a timeout or count it in the exit code.
The service answers such a request with a 422 before any build, so a timeout verdict on it would
mean nothing. At bc78eb9 the cost model refuses 11 of the 12 corpus entries at one artifact or
more. For example, d 6, length 20, s 12, k 3 is refused at all three artifacts. Its k/d of 0.5 is
below the fitted band, and the one-sided G28 rule keeps the raw prediction, which grows as k
falls.

## Why it matters
The local build-time bench still runs, but it now times almost no part the service would build.
A slowdown in the kernel on admitted parts would not show in it. The runner tiers that 07-18 and
07-19 add judge admitted boundary points, so this is not a gap in the gate, only in the local
bench.

## Next step
Rebuild the corpus from parts the cost model admits at every artifact. Do it by code from the
admitted space, keeping a heaviest-part entry. Alternatively, retire `bench.build_time` if the
07-18 and 07-19 tiers make it redundant. Revisit at the next change to `bench/corpus.py` or
`bench/build_time.py`.
