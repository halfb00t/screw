---
status: testing
phase: 07-operability-re-sweep
source: [07-VERIFICATION.md]
started: 2026-10-31T00:00:00Z
updated: 2026-10-31T00:00:00Z
---

## Current Test

number: 1
name: Owner confirms Phase 7 closes with OPER-03 still Pending
expected: |
  The owner accepts that the phase goal is met except for the residual in
  docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md, and names what carries
  OPER-03 forward.
awaiting: user response

## Tests

### 1. Owner confirms Phase 7 closes with OPER-03 still Pending
expected: The owner accepts the residual (an admitted in-wall part can still get a 422 build_error that names no field) and names what carries OPER-03 forward.
result: [pending]
owner_answer: "Close, carry via debt (Recommended)", given 2026-10-31 to the question "OPER-03 is still Pending: an admitted in-wall part can still get a kernel BuildError (422 build_error, no field named). Can phase 7 close with that, and what carries it forward?" The option text read: "Phase 7 closes with OPER-03 Pending. The must debt '2026-10-29-in-wall-parts-the-kernel-refuses' carries it, with the trigger 'before first release'. The roadmap and requirements say so."

### 2. Owner decides whether the bolt fine-STL peak budget needs a guard before release
expected: Either accept docs/tech_debt/active/2026-10-31-bolt-fine-peak-budget-above-the-worker-headroom.md as filed (bolt stl-fine peak budget 2,930,457,561 B against a worker headroom of 1,830,617,088 B), or schedule the re-fit.
result: [pending]
owner_answer: "Accept the must debt (Recommended)", given 2026-10-31. The option text read: "Keep '2026-10-31-bolt-fine-peak-budget-above-the-worker-headroom' as must, to be fixed by a bolt peak re-fit before the first release. Nothing measured fails."

### 3. Full-tier follow-up job has never run on the runner
expected: Either accept docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md as filed, or force a run that exercises the job.
result: [pending]
owner_answer: "Accept, existing debt (Recommended)", given 2026-10-31. The option text read: "The nice debt '2026-10-31-full-tier-follow-up-job-never-run-on-the-runner' already covers it. Close it the first time a real run reaches the margin."

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
