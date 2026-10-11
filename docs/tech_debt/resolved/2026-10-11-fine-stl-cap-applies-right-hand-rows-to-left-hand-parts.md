# The fine-STL refusal applies the right-hand caps to left-hand parts and misstates what L11 measured

Severity: must
Status: resolved
Date: 2026-10-11
Resolved in: this commit, `fix(calc): key the fine-STL caps by hand from the grid records and say what was measured` (plan 04-02; `git log --grep` finds the sha)
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

## Resolution
Option (a), ruled by the owner as D-21 (Phase 4 plan 04-02), in one commit.

- `FINE_STL_ROWS` is keyed by `(d, pitch, left_hand)` and has 13 entries. The right-hand seven
  are unchanged. The left-hand caps are the longest measured length below the first over-budget
  length, not the first over-budget length this item listed (the D-21 clarification): M10 72
  (first over 73), M12 77 (78), M14 78 (79), M16 75 (76), M18 91 (92), M20 91 (92). M8 left-hand has
  no entry: no run measured it over budget up to 80 mm.
- `tests/test_thread_maths.py::test_every_cap_is_the_longest_measured_length_that_fits_in_the_grid_records`
  recomputes every cap from `bench/results/thread-spike/2026-10-08-a-grid.jsonl` and requires
  equality with `FINE_STL_ROWS`, so a cap the records do not hold fails `make verify`.
- The refusal and the info warning now name the hand and say what was measured: the fine STL
  plus its gzip copy over the 64 MiB export budget (run `2026-10-08-a-grid`). The `app.py`
  comments over `_EXPORTS` and in `_serve` say the same, with the raw 45,659,684 bytes at M8 right
  L=68 as the reason the two blobs, not the STL, were over.
- L12's measurement claim ("the fine STL ... over the budget") is corrected beside the new
  hand-keyed cap rule L13 in plan 04-14 (D-24); the decision log is not edited here, so no locked
  entry is amended in place and no pointer dangles.
