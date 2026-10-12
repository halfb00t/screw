---
phase: 04
review: 04-REVIEW.md
titles: json
findings:
  - id: WR-04
    severity: warning
    disposition: open
    title: "The info-row pin matches selectors exactly, so a more specific selector walks past it"
  - id: IN-09
    severity: info
    disposition: open
    title: "`gap: .75rem` is also a row gap, so a wrapped value sits 10.5 px below its label"
  - id: IN-10
    severity: info
    disposition: open
    title: "The docstring of `_info_row_problems` is garbled, and the pin also freezes `#dims dl`"
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
    disposition: fixed
    title: "The page's Download STL link fetches the fine STL, which is refused for 62 of the picker's presets"
  - id: IN-03
    severity: info
    disposition: skipped
    title: "The same edit gives a 422 or a warning depending on whether `thread_length` equals the default 20"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "The `thread` parameter of `assemble` shadows the module-level `thread` function"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The \"rule 17\" link test checks a Python copy of the algorithm, not app.js"
  - id: IN-05
    severity: info
    disposition: open
    title: "Stale, now-false comment above the thread-length warning in `_bolt`"
  - id: IN-06
    severity: info
    disposition: open
    title: "`downloadLinks` selects every `.downloads a`, while the lookup uses `#dl-<format>`"
  - id: IN-07
    severity: info
    disposition: open
    title: "Two new tests compare `_downloads` to the call it is built from"
  - id: IN-08
    severity: info
    disposition: open
    title: "Stub bytes for ISO 4017 M8 x 70 land in the session-wide export cache"
open: 8
total: 15
recorded: 2026-10-12T15:17:32.407Z
---

# Phase 04: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-04 | warning | open | - |
| IN-09 | info | open | - |
| IN-10 | info | open | - |
| CR-01 | critical | fixed | `41c21ae` fix(app): refuse the thread_length conflict on the matched route, not the URL path — reproduced first (`TestClient(app, root_path="/screw")` on `/screw/api/bolt/info?length=10&thread_length=30` → 200 with a warning), fixed, regression test `test_the_conflict_is_still_a_422_behind_a_root_path`; pre-commit `make verify` green (not in the current review) |
| WR-01 | warning | fixed | `27723c1` fix(bench): build the head-fuse probe through the shipped bolt builder — re-run 2026-10-12 at 979168d, every geometry column identical to the 2026-10-11 run; RESULTS and L13 record both runs (not in the current review) |
| WR-02 | warning | fixed | `505934a` refactor(calc, app, cli): make the explicit-conflict rule the kind's own — `calc.explicit_conflict` dispatched by kind with one entry per registered kind, route-attached `refuse_explicit_conflict(kind)`, CLI calls the same; tests walk `KINDS` (not in the current review) |
| IN-01 | info | fixed | `d38efef` fix(solid, tables): raise on an unexpected kernel shape instead of asserting — `BuildError` for a non-Solid head or shank, `ValueError` for a missing second b (not in the current review) |
| IN-02 | info | fixed | `90ad513` feat(calc): carry the download state on the info document, from the rule the model route and screw export share, and `31a4596` feat(ui): build the download links from the info document and offer the preview STL where the fine one is refused — `PartInfo.downloads` from `download_refusal`; the page links per format the first entry not refused and offers `Download STL (preview)` with the refusal as its title where the fine STL is refused (owner ruling 2026-10-12, UAT test 3, option a: gap G-04-3); route-agreement, three-way parity, catalogue-wide (`afeffd8`), page-source and label tests (not in the current review) |
| IN-03 | info | skipped | owner ruling 2026-10-12 (UAT test 3, option a): as designed — "explicit" means named in the request, and the page's request is the link's content (D-25, D-09) (not in the current review) |
| IN-04 | info | fixed | `d38efef` — `assemble(p, bare_thread)`; `_build`'s local renamed too (not in the current review) |
| WR-03 | warning | open | recorded by the execute-phase code-review gate on 2026-10-12 (incremental review of the G-04-3 gap closure); awaiting the owner's ruling (not in the current review) |
| IN-05 | info | open | recorded by the execute-phase code-review gate on 2026-10-12 (incremental review of the G-04-3 gap closure); awaiting the owner's ruling (not in the current review) |
| IN-06 | info | open | recorded by the execute-phase code-review gate on 2026-10-12 (incremental review of the G-04-3 gap closure); awaiting the owner's ruling (not in the current review) |
| IN-07 | info | open | recorded by the execute-phase code-review gate on 2026-10-12 (incremental review of the G-04-3 gap closure); awaiting the owner's ruling (not in the current review) |
| IN-08 | info | open | recorded by the execute-phase code-review gate on 2026-10-12 (incremental review of the G-04-3 gap closure); awaiting the owner's ruling (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
