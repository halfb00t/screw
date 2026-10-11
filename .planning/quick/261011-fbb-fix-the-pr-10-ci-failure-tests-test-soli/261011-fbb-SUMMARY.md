---
phase: quick-261011-fbb
plan: 01
status: complete
requirements: [THRD-04]
commits: 2
plan_head_before: a0d727a65a0ee42f05e8ee172bf4c507c1ece88f
plan_head_after: ff6f1d5
actuals:
  tasks: 2
  commits: 2
---

# Quick 261011-fbb: fix the PR #10 CI failure in the THRD-04 naive-sweep control

One-liner: the platform-dependent control row (6.0, 1.0, 10.0), which raises `Null TopoDS_Shape` on linux/amd64, is replaced by (8.0, 1.25, 10.0), one valid silent-wrong solid on both platforms, and L11 gains a dated platform note.

## Commits

- `5ae0341` test(solid): feed the gate a naive-sweep row that is one solid on linux/amd64 too (tests/test_solid.py, bench/thread_spike/helical.py, .planning/phases/03-real-helical-thread/03-01-PLAN.md)
- `ff6f1d5` docs(decisions): qualify L11's known-bad rows by platform and file the OPER-02 controls idea (docs/architecture/decision_log.md, docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md, docs/ideas/INDEX.md)

## Verification (quoted)

- Task 1 verify: `3 passed, 29 deselected in 4.51s`; slowest durations: 0.49s [2.0-0.4-4.0], **0.48s [8.0-1.25-10.0]**, 0.37s [20.0-2.5-10.0]. Collected ids are exactly the three expected ones, no `assert` line removed, 03-01-PLAN.md frontmatter parsed with yaml, ruff clean.
- Task 2 verify: ALLOK (decision_log diff only adds lines, the 15-row list intact, the note carries every required fact, idea item has the template headings, INDEX Open row present with no placeholder).
- After both commits: `.venv/bin/python -m pytest tests/test_solid.py -k naive_sweep -q` -> `3 passed, 29 deselected in 3.31s`
- After both commits: `make verify` -> `Required test coverage of 96.0% reached. Total coverage: 96.88%` / `======================== 860 passed in 68.61s (0:01:08) ========================`. The pre-commit hook ran `make verify` on both commits and passed.

## Filed items

- Idea: `docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md` (listed under Open in `docs/ideas/INDEX.md`).
- No tech-debt item filed.

## Deviations from Plan

None. The plan executed as written. `import yaml` was available, so no substitution was needed.

## Notes

- The idea item follows TEMPLATE.md exactly (no Status line, unlike the one older item that has one).
- The Linux/amd64 proof of the swapped row is the orchestrator's emulated measurement; the executor did not push. CI on the next push is the native proof.
- Docs artifacts (this SUMMARY, PLAN.md, STATE.md) are left uncommitted for the orchestrator. ROADMAP.md untouched.

## Self-Check: PASSED

Both commits are ancestors of HEAD; the idea item, the platform note and all three edited code/doc files exist.
