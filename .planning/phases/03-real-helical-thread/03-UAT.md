---
status: complete
phase: 03-real-helical-thread
source: [03-VERIFICATION.md]
started: 2026-10-11T03:47:00Z
updated: 2026-10-13T05:13:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Left-hand checkbox and thread hand in a browser (03-05 human-check 1)
expected: The Thread fieldset shows a "Left-hand thread" checkbox at its natural width in both themes. Ticking it triggers a rebuild after the debounce; the preview's thread visibly reverses hand; the link gains `left_hand=true` only while checked; reloading `/#left_hand=true` restores the checkbox and the left-hand mesh; Reset unchecks it; Copy link copies the current hash. (No browser in the gate, L01.)
result: pass

### 2. Link refusals in a browser (03-05 human-check 2), plus `/#d=` from the WR-01 fix
expected: Each of `/#d=8&m=5`, `/#d=1&d=2`, `/#kind=bolt&kind=bolt`, `/#left_hand=banana`, `/#d=abc`, `/#d=` is refused with a message naming the key; the form is empty, the panel empty, downloads disabled, nothing builds. Then `/#d=8` opens normally. (`#d=abc` rests on the browser turning `abc` into an empty number input — browser behaviour, never run.)
result: pass

### 3. Per-mesh warnings after a failed update (03-05 human-check 3)
expected: After a failing edit (a 422, a gate `build_error`, a lost connection), the last mesh, the text "Showing the last valid part" and that mesh's own warnings are on screen together; the warnings change only when a new mesh replaces it; the startup failure shows none. (Fetch interleaving is observable only in a running page.)
result: pass

### 4. Status text after a refused link while a mesh is on screen (03-05 SUMMARY human item 4)
expected: Owner decides whether the status line should read "Showing the last valid part" in that state. Today it is empty while the mesh's warnings show (form cleared, mesh not editable). A UX call, not a defect a test can judge.
result: pass
note: owner keeps the empty status line over a refused link (2026-10-11)

### 5. First `workflow_dispatch` of `.github/workflows/grid.yml` after merge
expected: All 15 size shards (7160 rows) green on a GitHub runner; per-size wall time recorded in bench/RESULTS.md. Until then `timeout-minutes: 120` is an unmeasured guess (03-06). Locally: one cell (M2-left-void) green in 81 s; 03-06 recorded the M3.5 (131.89 s) and M4 (148.15 s) shards. Needs GitHub Actions after the PR merges.
result: pass
note: "Deferred on 2026-10-11 because no run existed (grid.yml was not yet on the default branch); closed on 2026-10-13 on run 38240380994. That run was the workflow's weekly schedule trigger, not a workflow_dispatch: same workflow, same job matrix, ref main at 57d05c6. 15 of 15 shards green, 7160 rows. Per-size pytest and job wall time are in bench/RESULTS.md under '### GitHub runner: run 38240380994 (2026-10-12)'. The slowest job, M20, took 29:03 of job wall (1686.74 s of pytest wall) against timeout-minutes: 120, which this test does not change."

### 6. Owner severity ruling on WR-05
expected: Rule on docs/tech_debt/active/2026-10-11-default-pitch-d100-length200-exceeds-both-interim-backstops.md: keep Severity must under D-18, or re-tag blocker. A single `GET /api/bolt/model.stl?d=100&length=200` (valid, in-cap, default pitch) measured at 53.3 s, 9143 MiB peak RSS, 1.3 GB fine STL against the 30 s timeout and the 4g limit. CLAUDE.md: a blocker is fixed now or surfaced and waited on — it is surfaced here.
result: pass
note: owner ruling 2026-10-11 — WR-05 stays Severity must under D-18; trigger the Phase 7 linux/amd64 re-sweep

### 7. Owner ruling on THRD-02 bookkeeping
expected: REQUIREMENTS.md line 15 is ticked `[x]` and traceability says Complete, but THRD-02's second clause (a left-hand pair proven like a right-hand pair) is Phase 5's PAIR-03. Either annotate the requirement so the second clause visibly points at PAIR-03 / Phase 5, or untick and re-tick at Phase 5. The verifier treated Phase 3's THRD-02 scope as met (see 03-VERIFICATION.md Requirements Coverage).
result: pass
note: owner ruling 2026-10-11 — keep the tick; REQUIREMENTS.md annotated "second clause: Phase 5 PAIR-03"

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

## Deferred Follow-Ups

- test: 5
  idea: "First workflow_dispatch of .github/workflows/grid.yml after the Phase 3 PR merges: 15 shards green, per-size GitHub-runner wall time recorded in bench/RESULTS.md; timeout-minutes: 120 is unmeasured until then"
  deferred_at: 2026-10-11
  resolved_at: 2026-10-13
  resolved_by: "quick task 261013-f9m: grid run 38240380994 (schedule, main at 57d05c6), recorded in bench/RESULTS.md"
