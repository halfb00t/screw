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
    disposition: open
    title: "`bench/head_fuse.py` does not fuse in the order the shipped builder does, yet claims to measure what ships"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Kind-specific rules are hard-coded into the generic request and CLI paths"
  - id: IN-01
    severity: info
    disposition: open
    title: "Production `assert` statements guard data and kernel invariants"
  - id: IN-02
    severity: info
    disposition: open
    title: "The page's Download STL link fetches the fine STL, which is refused for 62 of the picker's presets"
  - id: IN-03
    severity: info
    disposition: open
    title: "The same edit gives a 422 or a warning depending on whether `thread_length` equals the default 20"
  - id: IN-04
    severity: info
    disposition: open
    title: "The `thread` parameter of `assemble` shadows the module-level `thread` function"
open: 6
total: 7
recorded: 2026-10-12T07:27:50Z
---

# Phase 04: Code Review Disposition

Recorded by the execute-phase code-review gate on 2026-10-12. CR-01 was a blocker under the repo's rule ("fix it now or stop and ask"): it was reproduced, fixed and tested in the same run. Every other finding stays `open` until the owner rules; none is filed as tech debt yet, because a deferred item needs the owner's sign-off (CLAUDE.md). Review: `04-REVIEW.md` (33 files, standard depth, 1 critical / 2 warnings / 4 info).

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | `41c21ae` fix(app): refuse the thread_length conflict on the matched route, not the URL path — reproduced first (`TestClient(app, root_path="/screw")` on `/screw/api/bolt/info?length=10&thread_length=30` → 200 with a warning), fixed, regression test `test_the_conflict_is_still_a_422_behind_a_root_path`; pre-commit `make verify` green |
| WR-01 | warning | open | owner ruling needed: re-run the D-03 probe through the shipped `assemble` (kernel minutes) and refresh `bench/RESULTS.md`, or amend the probe docstring and the RESULTS note to say the probe fuses `thread.fuse(shank.fuse(head))` while the product fuses `thread.fuse(shank).fuse(head)`; the `_build` gate protects users either way |
| WR-02 | warning | open | design change (a registry-dispatched conflict rule, as `download_refusal` is); the Phase 5 nut is the trigger; owner decides debt item vs Phase 5 plan |
| IN-01 | info | open | production `assert` as an invariant guard; owner decides whether a `BuildError` / `ValueError` is wanted instead |
| IN-02 | info | open | user-visible: the page's Download STL link asks for the fine STL, refused (422) for 62 of the 294 presets; a UAT item and a Phase 6 printability candidate |
| IN-03 | info | open | user-visible: an edited Length is a 422 when `thread_length` was set explicitly and a warning when it equals the default 20, because the page omits default-equal fields (D-09); as designed under D-25, but worth an owner look |
| IN-04 | info | open | naming: `assemble(thread=...)` shadows the module-level `thread` function |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
