# The fine-STL refusal applies the right-hand caps to left-hand parts and misstates what L11 measured

Severity: must
Status: active
Date: 2026-10-11
Source: Phase 3 code review (03-REVIEW.md WR-02), deferred by the owner on 2026-10-10 ("fix mechanical now, defer the rest"); needs a measurement or a rule decision
Related files:
- src/screw/calc/thread.py (`FINE_STL_ROWS`, `fine_stl_refusal`)
- src/screw/app.py (`download_refusal` call and its budget comment)
- docs/architecture/decision_log.md (L12 "Caps")
- bench/results/thread-spike/2026-10-08-a-grid.jsonl (the measured rows)

## Context
`fine_stl_refusal` keys the seven L11 rows on `(d, pitch)` only. Recomputed from the committed grid records, the first over-budget length differs by hand: right-hand M8 68, M10 57, M12 61, M14 59, M16 53, M18 66, M20 65 mm; left-hand M8 none measured (fits to 80), M10 73, M12 78, M14 79, M16 76, M18 92, M20 92 mm. A left-hand M10 at 60 mm is therefore refused with "L11 measured it over the export budget" although L11 measured that part inside the budget. The recorded criterion is `fine raw + gzip-1 bytes > 67108864` (two blobs); at M8 L=68 the raw fine STL alone is 45,659,684 bytes, under 64 MiB, so `_BlobCache.put` does not drop it — the blobs evict each other. The `app.py` comment and the user-facing message both say the STL itself was measured over budget.

## Why it matters
L02: a refusal is a number someone acts on; this one covers a range nobody measured and names the wrong quantity. D-02's rule is to refuse only where L11 measured a limit.

## Next step
Owner ruling, then one of: (a) key the rows on `(d, pitch, left_hand)` with the left-hand caps above (M8 left has no measured stop, so no cap), or (b) keep the single conservative cap and reword the message, the `app.py` comment and L12 to "the fine STL plus its gzip copy was measured over the 64 MiB export budget for the right-hand rod; applied to both hands". Either way, re-check the text against the records in the same commit.
