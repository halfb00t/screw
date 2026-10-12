---
phase: 04
review: 04-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "The `thread_length`/`length` 422 is silently skipped under `screw serve --root-path`"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`bench/head_fuse.py` does not fuse in the order the shipped builder does, yet claims to measure what ships"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Kind-specific rules are hard-coded into the generic request and CLI paths"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "Production `assert` statements guard data and kernel invariants"
  - id: IN-02
    severity: info
    disposition: open
    title: "The page's Download STL link fetches the fine STL, which is refused for 62 of the picker's presets"
  - id: IN-03
    severity: info
    disposition: skipped
    title: "The same edit gives a 422 or a warning depending on whether `thread_length` equals the default 20"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "The `thread` parameter of `assemble` shadows the module-level `thread` function"
open: 1
total: 7
recorded: 2026-10-12T08:56:58Z
---

# Phase 04: Code Review Disposition

Recorded by the execute-phase code-review gate on 2026-10-12. CR-01 was a blocker under the repo's rule ("fix it now or stop and ask"): it was reproduced, fixed and tested in the same run. Owner ruling 2026-10-12 (UAT test 3): "fix all". WR-01, WR-02, IN-01 and IN-04 were fixed in the same session; IN-03 was skipped by the owner as designed; IN-02 is a page/API contract change and goes through a gap-closure plan (G-04-3). Review: `04-REVIEW.md` (33 files, standard depth, 1 critical / 2 warnings / 4 info).

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | `41c21ae` fix(app): refuse the thread_length conflict on the matched route, not the URL path — reproduced first (`TestClient(app, root_path="/screw")` on `/screw/api/bolt/info?length=10&thread_length=30` → 200 with a warning), fixed, regression test `test_the_conflict_is_still_a_422_behind_a_root_path`; pre-commit `make verify` green |
| WR-01 | warning | fixed | `27723c1` fix(bench): build the head-fuse probe through the shipped bolt builder — re-run 2026-10-12 at 979168d, every geometry column identical to the 2026-10-11 run; RESULTS and L13 record both runs |
| WR-02 | warning | fixed | `505934a` refactor(calc, app, cli): make the explicit-conflict rule the kind's own — `calc.explicit_conflict` dispatched by kind with one entry per registered kind, route-attached `refuse_explicit_conflict(kind)`, CLI calls the same; tests walk `KINDS` |
| IN-01 | info | fixed | `d38efef` fix(solid, tables): raise on an unexpected kernel shape instead of asserting — `BuildError` for a non-Solid head or shank, `ValueError` for a missing second b |
| IN-02 | info | open | owner ruling 2026-10-12 (UAT test 3, option a): fix through gap G-04-3 in 04-UAT.md — a structured download state on the info document and a preview-STL link on the page; planned by /gsd-plan-phase 4 --gaps, not patched inline |
| IN-03 | info | skipped | owner ruling 2026-10-12 (UAT test 3, option a): as designed — "explicit" means named in the request, and the page's request is the link's content (D-25, D-09) |
| IN-04 | info | fixed | `d38efef` — `assemble(p, bare_thread)`; `_build`'s local renamed too |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
