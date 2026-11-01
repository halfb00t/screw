---
phase: 07-operability-re-sweep
plan: 14
subsystem: web
tags: [page, OPER-03, D-06, L21, B-02, B-03, refused-preview, ui-spec]
status: complete

requires:
  - phase: 07-operability-re-sweep
    provides: "07-11: the per-artifact cost model, downloads[].refusal on the cost model, the over_budget 422"
  - phase: 07-operability-re-sweep
    provides: "07-12: B-03 part-wide default cap and L21, including the ISO 4017 M20 x 60 pitch-1 refused-preview case"
provides:
  - "src/screw/static/app.js: PREVIEW, and update() handles a refused preview (dropMesh, panel, served downloads, the refusal as status, no mesh request)"
  - "src/screw/static/app.js: the 350 ms debounce relabelled a UI choice, no INTERIM"
  - "tests/test_parity.py: test_the_ui_offers_the_downloads_that_fit_when_the_preview_is_refused, test_the_debounce_is_a_ui_choice_and_not_a_runtime_bound"
  - "01-UI-SPEC.md: the Phase 7 amendment note; rules 11, 13, 15, 17; the over_budget, refused-status and cap-warning rows"
affects: [07-15, 07-16]

tech-stack:
  added: []
  patterns:
    - "The page names the preview STL it draws in one constant (PREVIEW), used for the fetch and for finding its own downloads entry"

key-files:
  created:
    - docs/tech_debt/active/2026-10-29-status-sentence-runs-under-fit.md
    - .planning/phases/07-operability-re-sweep/07-14-SUMMARY.md
  modified:
    - src/screw/static/app.js
    - tests/test_parity.py
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
    - docs/tech_debt/INDEX.md

key-decisions:
  - "The page names the preview STL once, in PREVIEW = { format: 'stl', quality: 'preview' }; the parity pin now allows exactly one 'stl' literal and still one 'preview'"
  - "On a refused preview the panel is drawn after dropMesh(), because dropMesh clears the messages; meshWarnings stay empty because no mesh is on screen"

metrics:
  duration: "about 25 minutes"
  completed: 2026-10-29

estimate:
  tokens: 70000
  tasks: 2
actuals:
  tokens: 15600
  tasks: 2
  commits: 2
plan_head_before: 5f8728225c1b263d7dc195528369ecbd059a5af1
plan_head_after: 63460c7a08782dce61ede634b7397b2762252ffb
---

# Phase 7 Plan 14: The page with a refused preview Summary

When the info document refuses the preview STL, the page no longer requests the mesh. It drops the
mesh on screen, draws the part's panel and warnings, links every download that is served, and shows
the server's refusal sentence as the status. The 350 ms debounce is now labelled a UI choice. The
page contract (01-UI-SPEC.md) is amended in place to match.

## Commits

| # | Hash | Subject |
|---|------|---------|
| 1 | 717f333 | feat(web): offer the downloads that fit when the preview STL is refused (07 D-06) |
| 2 | 63460c7 | docs(07): amend the page contract for a refused preview (07 D-06) |

## What was built

- **`update()`**: after the info fetch it finds the `downloads` entry whose format and quality
  match `PREVIEW`.
  - **Refusal set:** `dropMesh()`, then `renderInfo(info)`, then `setDownloads(q, info.downloads)`,
    then `setStatus(preview.refusal)`, then return. No `model.stl` request is made.
  - **Refusal null:** the path rule 13 already described, unchanged: render, fetch the preview, a
    failed request goes through `fail()`, then `showModel`, `setDownloads`, `setStatus('')`.
- **`PREVIEW`** is the one place the page names a format and a quality. The fetch now reads
  `model.${PREVIEW.format}` and `quality=PREVIEW.quality`, so the request URL is unchanged.
- **Debounce comment:** "a UI choice, not a runtime bound … not measured". The value stays 350.
  `INTERIM` no longer appears anywhere in `app.js`.
- **The UI-SPEC amendment** (note 13):
  - The hard constraint and Page Anatomy `#status`.
  - Rules 11, 13, 15 and 17, each naming its pinning test.
  - The Copywriting rows:
    - The bolt and nut fine-STL rows and the `fine_stl_cap` error row become one `Over-budget
      refusal (server)` row. It gives the L21 sentence shape, a real example and the
      `over_budget` 422 with `ctx.fields` and `ctx.artifact`.
    - New `Status: preview refused` and `Default-cap warning (server)` rows.
  - UI Considerations E5, E6 and E8, with the `Applicable:` count recounted from the table (82: 66
    resolved, 12 dismissed, 4 unresolved).
  - A Verification status bullet and Extension rule 3.

## Browser probe (scratch, not in the repo)

The probe used headless Chromium from spur's venv (the 05-21 precedent):
`PLAYWRIGHT_BROWSERS_PATH=/Users/half/git/halfb00t/spur/.venv/ms-playwright
/Users/half/git/halfb00t/spur/.venv/bin/python -I probe_07_14.py http://127.0.0.1:8014/`, against
`screw serve --port 8014` at 717f333, at 1440 px and 720 px wide.

- **Refused part:** `#d=20&length=60&s=30&k=12.5&thread_length=60`, which is ISO 4017 M20 x 60 at
  the default pitch 1.
  - No `model.stl` request was made and 17 panel values were drawn.
  - The status is the sentence
    `d, pitch, length, s, k and thread_length: the preview STL (stl-preview) of this bolt is predicted over its measured budget (L21), so it is refused before any build; the fine STL (stl-fine) and STEP (step) of this part fit. To get it, change one of these fields, or download an artifact that fits`.
    It is also the third of four warnings.
  - `Download STL` links `…&quality=fine` and `Download STEP` links `…&quality=fine`, with no title.
    The canvas is empty.
- **Default part afterwards:** one request to `model.stl?quality=preview`, and both links at
  `quality=fine`.
- **Layout defect:** the status sentence wraps (2 lines at 1440 px, 3 at 720 px) and its first line
  runs under `Fit`. At 1440 px the status box reaches x 1440 and `Fit` starts at x 1391.5; at
  720 px it is 720 and 671.5. See Deferred below.

## Deviations from Plan

**1. [Rule 3 - Blocking] Existing pins adjusted to the plan's literals**
- **Found during:** Task 1.
- **Issue:** the plan's lookup `format === 'stl' && quality === 'preview'` conflicted with three
  existing pins in `tests/test_parity.py`:
  - `test_the_ui_builds_both_download_links_…_names_no_quality` asserted no quoted `'stl'` and
    exactly one `'preview'`.
  - `test_the_badge_composes_…` listed the fetch URL `model.stl?${stlQ}` literally.
  - `test_a_kind_change_drops_the_old_mesh_…` counted `dropMesh()` at exactly 2.
- **Fix:** one constant, `PREVIEW`, carries both literals for the fetch and the lookup.
  - The names-no-quality pin now allows exactly one `'stl'` and still exactly one `'preview'`.
    `'fine'` and `'step'` stay at zero.
  - The fetch list reads `model.${PREVIEW.format}?${stlQ}`.
  - The `dropMesh()` count is 3, as the plan's acceptance criterion expects.
- **Commit:** 717f333.

**2. [Plan wording] The panel is drawn after `dropMesh()`, not before**
- **Issue:** `dropMesh()` clears `pendingWarnings`/`pendingNotes` and the messages area. Calling
  `renderInfo(info)` first and then `dropMesh()` would erase the part's warnings.
- **Fix:** the lookup comes first, and the refused branch is
  `dropMesh(); renderInfo(info); setDownloads(…); setStatus(…)`.
  - The plan asks for `meshWarnings`/`meshNotes` to be set "as showModel would". That is not done:
    `fail()` reads them only while a mesh is on screen (`mesh ? meshWarnings : []`), so with no
    mesh they are never shown.
  - Setting them would also break the existing pin that `meshWarnings = pendingWarnings` occurs
    once.
  - A later failure therefore shows its errors with no warnings and an empty status, as with no
    mesh at all. Rule 15 says this.
- **Commit:** 717f333.

**3. [Rule 1 - Copy] Comment wording**
- The page pin bans the phrase "fine STL" in `app.js`, so the new comment says "finer mesh".

**4. [Scope] Extra UI-SPEC items amended so the contract stays true**
- Beyond the plan's list, these were amended:
  - the Hard constraints bullet;
  - Page Anatomy `#status`;
  - the Primary CTA row, which cited the retired INTERIM caps and the 62 refused rows;
  - rule 11 (the debounce);
  - rule 17's stale test name (`…m8_x_70…`, now `…a_refused_preset_part…`);
  - a `Default-cap warning (server)` row. 07-12 added that server string without a contract row.
- The note lists all of them.

## Deferred Issues

- **Filed (nice):** `docs/tech_debt/active/2026-10-29-status-sentence-runs-under-fit.md`.
  - The refusal sentence's first line runs under `Fit`. Nothing is lost, because the whole sentence
    is also a warning.
  - The offset that clears the button, about 3.5rem, is not one of the six spacing tokens, so it
    needs the owner's decision under extension rule 4.
  - UI-SPEC E6 overflow is marked unresolved and points at the debt item.
- **Not touched:** `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` still lists the UI
  debounce row at `app.js:318-321`. The plan did not own that file. 07-16, or whichever plan retires
  that item, should drop or relabel the row.

## For the owner

- **Page vs preset:** this works as planned. The M20 x 60 pitch-1 case is refused on the page as
  well, because every field there differs from its default and so counts as named. A part the page
  caps is still refused through `--preset`, as L21 says. Nothing here conflicts with that.
- **Human check:** the plan's human check (`make serve`, type a refused part, then the default) is
  an end-of-phase UAT item. The scratch probe above covers its mechanics, but not the reading in
  both themes.

## Requirements

OPER-03 is not ticked. 07-15 and 07-16 (timeouts and runner verification) are still open.

## TDD Gate Compliance

- **RED:** the four new or changed pins in `tests/test_parity.py` were run before any `app.js`
  edit: 4 failed, 76 passed.
- **GREEN:** after the edit, 80 passed.
- **Commits:** the RED pins and the GREEN code went into one commit (717f333), as the plan's
  single-commit Task 1 says. The pre-commit `make verify` passed.

## Known Stubs

None.

## Threat Flags

None. The refusal reaches the DOM only through `setStatus` (`textContent`) and the existing
`showMessages` path (T-07-35). `dropMesh()` is on the refused branch, held by the source pin
(T-07-36).

## Self-Check: PASSED

- FOUND: src/screw/static/app.js, tests/test_parity.py, 01-UI-SPEC.md,
  docs/tech_debt/active/2026-10-29-status-sentence-runs-under-fit.md
- FOUND: 717f333, 63460c7 (ancestors of HEAD)
- `grep -c INTERIM src/screw/static/app.js`: 0
- `grep -c "dropMesh()" src/screw/static/app.js`: 3 (was 2)
- `grep -c "Amended in Phase 7" 01-UI-SPEC.md`: 1
- `grep -c test_the_ui_offers_the_downloads_that_fit_when_the_preview_is_refused 01-UI-SPEC.md`: 6
- `grep -c "the preview STL and the STEP are never refused" 01-UI-SPEC.md`: 0
