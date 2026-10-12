---
phase: 04-iso-hex-bolts-and-screws
reviewed: 2026-10-12T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - docs/architecture/decision_log.md
  - docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md
  - docs/ideas/INDEX.md
  - src/screw/calc/__init__.py
  - src/screw/static/app.js
  - tests/test_api.py
  - tests/test_calc.py
  - tests/test_parity.py
  - tests/test_presets.py
findings:
  critical: 0
  warning: 1
  info: 4
  total: 5
status: issues_found
---

# Phase 4: Code Review Report (incremental, G-04-3 gap closure)

**Reviewed:** 2026-10-12
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Scope: `git diff afb9d04..HEAD` in the nine listed files, centred on G-04-3 (`Download`,
`PartInfo.downloads`, `_downloads`, `downloadLinks`, `setDownloads`). The production change is
sound. I traced `_bolt` against the pre-change code: `t` is the same `built_thread_length` value on
both paths, so the fine-STL warning is unchanged in text and position and now cannot disagree with
`downloads`. The route (`_serve`), `screw export` and the document all call `download_refusal`.
`setDownloads` resets every anchor on each call, keeps the first non-refused entry per format, never
touches the hash, builds nodes with `textContent` and `title` only, and holds no format or warning
literal. The `Literal` pair in `calc` is pinned to the route enums through OpenAPI. Rule checks:
no `Any`, `screw.calc` imports no `cadquery`, the `calc.thread` and `params` boundaries hold.
The comments I could check against code are accurate (`TESSELLATION` values, STEP ignoring
quality).

Gate evidence: `ruff check src tests` passed; `mypy --strict src tests` passed (38 files);
`lint-imports` 9 kept, 0 broken; the 32 new/changed tests (`-k "download or openapi or labels or
the_ui"` over the four test files) passed. I did not run the full `make verify`.

No bug or security defect found in the shipped behaviour. The one warning is a test that does not
test the code it names.

## Warnings

### WR-03: The "rule 17" link test checks a Python copy of the algorithm, not app.js

**File:** `tests/test_parity.py:535-586` (also the vacuous assertion at `tests/test_parity.py:529`)
**Issue:** `_links_by_rule_17` re-implements in Python the first-served-entry-per-format and
"label gets `(quality)` only after an earlier refusal" logic, and
`test_the_download_labels_are_static_and_the_refused_fine_stl_reads_download_stl_preview` asserts
that this copy returns `Download STL (preview)`. Nothing runs `setDownloads`. A regression in the
JS (for example dropping the `linked` guard so a later served entry overwrites the link, or
labelling the first entry too) leaves this test green. The companion source-text test is
`assert "title" in body`, which is vacuous: `a.removeAttribute('title')` in the same function
already satisfies it. The only coverage of the shipped link behaviour is therefore substring
matches on source text. This is the exact path G-04-3 exists to protect (L02: never link a download
the server refuses, never let a coarser mesh pass for the fine one).
**Fix:** Either execute `setDownloads` for real, or tighten the source assertions to the
behaviour. The first is cheapest if the repo already has Node in CI: extract the function, run it
against a stub DOM with the three documents (default, capped, STL-all-refused) and assert `href`,
`textContent`, `title`, `aria-disabled`. If JS execution stays out of scope (L01), at least replace
the vacuous check:
```python
assert "a.title = refusals.get(download.format)" in body
assert "if (linked.has(download.format)) continue;" in body
```
and say in the test docstring that `_links_by_rule_17` documents the rule, it does not verify the
page.

## Info

### IN-05: Stale, now-false comment above the thread-length warning in `_bolt`

**File:** `src/screw/calc/__init__.py:~172-173` (`# The page's Download STL link asks for the fine
default, so without this a click on a capped part opens raw JSON ...`)
**Issue:** The comment sits above `_thread_length_warning`, not above the fine-STL block it
describes (misplaced before this change). G-04-3 makes it false as well: the page no longer asks
for the fine default where it is refused; it links the preview STL. The new comment on the
`downloads` lines is correct, so the old one is misleading noise next to it.
**Fix:** Delete the two comment lines, or move them out; the new comment at the `_downloads(p)` call
already carries the why.

### IN-06: `downloadLinks` selects every `.downloads a`, while the lookup uses `#dl-<format>`

**File:** `src/screw/static/app.js:393-395, 413`
**Issue:** The reset loop strips `href`, sets `aria-disabled` and clears `title` on every anchor in
`.downloads`, but anchors are enabled by `$('#dl-${download.format}')`. Two selection handles for
one set. The test pins only the `id="dl-<fmt>"` anchors in index.html, so a third anchor added to
that container (a help link, a "copy link" action) would be silently disabled forever and no test
would fail. Also, `$('#dl-...')` on a server-supplied `format` would throw on a format with no
anchor; today the OpenAPI test keeps the sets equal.
**Fix:** Build the map from the ids the page owns:
`new Map([...document.querySelectorAll('.downloads a[id^="dl-"]')].map((a) => [a, a.textContent]))`,
and look the anchor up from a `format -> anchor` map instead of re-querying the DOM.

### IN-07: Two new tests compare `_downloads` to the call it is built from

**File:** `tests/test_calc.py:~296-303` (`test_every_registered_kinds_document_agrees_with_its_download_rule`),
`tests/test_presets.py:~161-173` (`entry.refusal == download_refusal(p, ...)`)
**Issue:** `_downloads(p)` is `[Download(..., refusal=download_refusal(p, fmt, quality)) ...]`, so
asserting `entry.refusal == download_refusal(p, entry.format, entry.quality)` is true by
construction and catches nothing (the `step is never refused` and "every format has a link" checks
beside it are the real content). The route-versus-document agreement that matters is covered by
`test_every_download_the_document_lists_is_answered_by_the_route_as_it_says`.
**Fix:** Keep the independent assertions (STEP never refused, every format served, the
falls-back set equals the fine-refused set) and drop the tautological equality, or compare against
`fine_stl_refusal` directly.

### IN-08: Stub bytes for ISO 4017 M8 x 70 land in the session-wide export cache

**File:** `tests/test_api.py:1048-1082`
**Issue:** The docstring avoids cache pollution for the plain part (`d=5.55`) but the capped part is
the catalogue row `iso4017:M8x70`. Its three served downloads (STL preview, STEP fine, STEP
preview) are stored as `b"stub"` in `app._EXPORTS`, and the next `seen[before:]` assertion also
depends on the cache being cold, so re-running the test in one process (pytest-repeat, a watch
mode) fails with an empty `seen`. No other test downloads that row today, so nothing fails now; a
future real download of M8 x 70 would receive `b"stub"` depending on order.
**Fix:** Use a capped part off every row, as the module docstring prescribes, for example
`{"d": 8, "pitch": 1.25, "length": 67.6, "thread_length": 67.6}` with a unique `s`/`k`, or clear the
keys the test wrote in a `finally`.

---

_Reviewed: 2026-10-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
