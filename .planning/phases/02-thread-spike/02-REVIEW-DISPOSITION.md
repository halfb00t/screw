---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`verdict --campaign PREFIX` also reads campaigns whose prefix merely extends PREFIX"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`--k-from` and `--frontier-from` accept incomplete records"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "The quiet gate decides `decisive` once, at the start of each block"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "A mixed-hand cell reads \"violated\" without the nut body being checked"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "A run is recorded under the HEAD sha without checking the harness is committed"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "`_head()` has no `cwd` and is read after the run"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "`PAIR_TIMEOUT_S` does not follow from the numbers in its own comment"
  - id: IN-03
    severity: info
    disposition: skipped
    title: "A bad request line kills the worker instead of returning a failure record"
  - id: IN-04
    severity: info
    disposition: skipped
    title: "The status returns of `Build`, `MakeSolid` and `VolumeProperties_s` are ignored"
  - id: IN-05
    severity: info
    disposition: fixed
    title: "The oracle docstring overclaims independence from the builder"
  - id: IN-06
    severity: info
    disposition: fixed
    title: "An oversized integer in an edited JSONL escapes the refusal path"
  - id: IN-07
    severity: info
    disposition: skipped
    title: "The reference worker's kernel is not recorded"
open: 0
total: 12
recorded: 2026-10-09T02:43:53.790Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | be82c06: the verdict reads only <prefix>-<block>.jsonl and refuses a header naming another block |
| WR-02 | warning | fixed | 9a5a5c5: a --k-from sweep and a --frontier-from walk go through block_gaps, the walk at the locked K |
| WR-03 | warning | deferred | owner ruling 2026-10-10 (Task 1): a D-17 protocol amendment (load readings and a downgrade rule), put off to before the next campaign; see docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md |
| WR-04 | warning | fixed | cc05a38: the nut-body check runs ahead of the mixed-hand branch |
| WR-05 | warning | fixed | 0e2f437: the guard refuses on uncommitted harness changes; bench/results excluded so campaign output never refuses the next block; src added because the worker imports screw |
| IN-01 | info | fixed | 0e2f437: the report prints the HEAD the guard read at the start of the run |
| IN-02 | info | deferred | the 600 s is pre-registered (Protocol inputs, owner: they stand); 2026-10-08-a-pair recorded no timeout cell; changing it is an amendment for the owner before the next campaign; see docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md |
| IN-03 | info | skipped | unreachable: the parent builds every request line; if reached, worker_died fails the pass bar loudly |
| IN-04 | info | skipped | both failure modes are caught downstream: a shell reads solids=0 and so silent_wrong; the nut-body check; a non-converged volume misses the closed form by more than T_PASS; a status check would only relabel a failing row |
| IN-05 | info | fixed | 2bf9a90: the oracle docstring says it imports no kernel code and shares the pinned profile parameters |
| IN-06 | info | fixed | a8bc769: an integer too large for a float is refused as ValueError |
| IN-07 | info | skipped | the ruled rows are evidence only, never a verdict input, and the reference package was installed --no-deps (STATE.md, Phase 02), so the scratch directory carries no kernel to shadow |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
