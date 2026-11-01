# The bolt's fine-STL peak budget is above the memory a worker has

Severity: must
Status: active
Date: 2026-10-31
Source: quick task 261031-qd7, G40 ("1: nut stl-fine only (Recommended)"), L32
Related files:
- src/screw/calc/cost.py (`BUDGET`, `budget`, `HEADROOM_CAPPED`, `WORKER_HEADROOM_BYTES`)
- bench/results/phase-07/runtime.json (`mem_limit_bytes`, `b`, `export_cache`, `tmpfs_bytes`)

## Context
G40 caps the nut's fine-STL peak budget at the worker's headroom, 1,830,617,088 B (`mem_limit`
2,415,919,104 B less B 65,208,320, the export cache 251,658,240 and the tmpfs 268,435,456). The
bolt's stays B-01's 2,930,457,561 B, set by iso4017:M20x200's enveloped peak. Capping it too would
refuse the fine STL of 110 bolt catalogue rows (77 ISO 4017 and 33 ISO 4014, M10 to M20) and of 33
links that name only d (bolt d 3.9 to 5.4 and 8.3 to 9.9). The bolt stl-fine peak e is
2.170967259675211 (set by explore:bolt-d300-p10-n3-right), so the envelope is about 3.2 x looser than
any admitted bolt measured: the full tier read those 110 rows' stl-fine peaks at 904,486,912 B at
most (iso4017:M20x200, run 41155746591; run 41161227951 reads 882,589,696 B at most), 0.4941 of the
headroom.

## Why it matters
A bolt admitted between a measured peak and the budget could pass `mem_limit` and be OOM-killed
instead of getting L21's `over_budget` 422 (L02). No admitted bolt has been read near the headroom,
so this is unmeasured, which is why it is not a blocker.

## Next step
Re-fit or tighten the bolt stl-fine peak model so its envelope is near the readings, then cap the
bolt's budget at the headroom as G40 does the nut's. Revisit before the first release, or as soon as
an admitted bolt reads a fine-STL peak above 1,830,617,088 B.
