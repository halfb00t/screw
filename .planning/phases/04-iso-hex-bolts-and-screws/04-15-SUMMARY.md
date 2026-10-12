---
phase: 04-iso-hex-bolts-and-screws
plan: 15
subsystem: api
tags: [pydantic, openapi, info-document, downloads, fastapi, cli, gap-closure]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "download_refusal and the INTERIM 64 MiB fine-STL cap (D-02, D-21); the preset catalogue (D-10); the info document (D-17)"
provides:
  - "PartInfo.downloads: one Download(format, quality, refusal) per format and quality the model route serves, from download_refusal"
  - "the same member on /api/bolt/info and in screw info bolt (FRNT-05)"
  - "per-row proof that the document agrees with the shared rule on all 294 catalogue rows"
affects: [04-16 page half of G-04-3, verify-work UAT test 3, any future kind's info builder]

plan_head_before: 79c052273ee6b2d4558443eb7190deee3a5ddcd4
plan_head_after: afeffd8d3182c41d3bcb712b77a6c4b41067a3ab

actuals:
  tokens: 4600
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A required info-document member is built by calling the same rule the route and the CLI call, never a parallel computation"
    - "A response enum is pinned to the route's own OpenAPI enum in a test, not to a list typed in the test"

key-files:
  created: []
  modified:
    - src/screw/calc/__init__.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_parity.py
    - tests/test_presets.py

key-decisions:
  - "The fine-STL warning is appended from the refused downloads (distinct, entry order) at its old place after the no-row warning: same text, same position, now one call with the member (L02)"
  - "Both qualities are listed for STEP although solid ignores quality for STEP: the route accepts both, so both entries are true"

requirements-completed: [TABL-01, TYPE-02]

coverage:
  - id: D1
    description: "The info document carries a required downloads member (stl fine, stl preview, step fine, step preview), each refusal equal to download_refusal"
    requirement: TYPE-02
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_a_capped_part_refuses_exactly_its_fine_stl_download_by_the_shared_rule"
        status: pass
      - kind: unit
        ref: "tests/test_calc.py#test_every_registered_kinds_document_agrees_with_its_download_rule"
        status: pass
    human_judgment: false
  - id: D2
    description: "The Download enums and entry order are pinned to the model route's fmt and quality parameters in OpenAPI"
    requirement: TABL-01
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_openapi_documents_the_typed_contracts"
        status: pass
    human_judgment: false
  - id: D3
    description: "For ISO 4017 M8 x 70 the route answers every entry as the document says; the CLI and API print equal downloads; export exits 2 with the same sentence and writes no file"
    requirement: TYPE-02
    verification:
      - kind: integration
        ref: "tests/test_api.py#test_every_download_the_document_lists_is_answered_by_the_route_as_it_says"
        status: pass
      - kind: integration
        ref: "tests/test_parity.py#test_the_downloads_of_iso_4017_m8_x_70_are_one_sentence_on_the_cli_the_api_and_export"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every catalogue row's document agrees with download_refusal, keeps a served entry per format, and the preview-fallback rows are exactly the fine-STL-refused rows (pinned 62 untouched)"
    requirement: TYPE-02
    verification:
      - kind: unit
        ref: "tests/test_presets.py#test_every_catalogue_rows_document_agrees_with_the_shared_download_rule"
        status: pass
      - kind: unit
        ref: "tests/test_presets.py#test_the_rows_whose_stl_falls_back_to_the_preview_are_the_fine_stl_refused_rows"
        status: pass
      - kind: unit
        ref: "tests/test_presets.py#test_the_fine_stl_refused_presets_are_counted"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 15: Download state on the info document Summary

**The info document gains a required `downloads` member (stl fine, stl preview, step fine, step preview, each with the `download_refusal` sentence or null), served identically by `/api/bolt/info` and `screw info`, with the model route and `screw export` refusing exactly the entry it refuses and every catalogue row checked against the rule.**

This is the server half of gap G-04-3. Plan 04-16 builds the page's links from the member.

## Performance

- **Duration:** about 8 min
- **Started:** 2026-10-12T09:47:56Z (first write; the workflow reads came before)
- **Completed:** 2026-10-12T09:54:23Z (last task commit; SUMMARY follows)
- **Tasks:** 2
- **Files modified:** 5 (1 source, 4 test)

## Accomplishments

- `Download`, `DownloadFormat`, `DownloadQuality`, `PartInfo.downloads`, `_DOWNLOADS` and `_downloads(p)` in `screw.calc`. `_downloads` calls `download_refusal(p, fmt, quality)`, the call `app._serve` and `cmd_export` make, so the document, the route and the CLI cannot disagree (T-04-29).
- ISO 4017 M8 x 70: the document refuses exactly the STL fine entry with the fine-STL sentence; the other three entries are null. The route answers a 422 `fine_stl_cap` with that `msg`, and `screw export bolt --preset iso4017:M8x70 -o x.stl` exits 2 printing `error: <sentence>` and writes no file.
- The fine-STL warning keeps its text and its place (after the no-row warning); it is now appended from the refused entries (L02).
- Per-catalogue-row proof: all rows agree with the rule entry by entry, each format keeps a served entry, and the preview-fallback rows equal the fine-STL-refused rows, both derived from the catalogue. The pinned 62 in `test_the_fine_stl_refused_presets_are_counted` is byte-identical to `d3eb46f`.

## TDD record (Task 1, `type="tracer" tdd="true"`)

RED was written first and not committed (the pre-commit hook forbids a red suite).

- Command: `make test PYTEST_ARGS="tests/test_api.py tests/test_parity.py -q -n0 --no-cov"`
- Result: `3 failed, 172 passed`. Failing tests, each on the planned assertion:
  - `tests/test_api.py::test_openapi_documents_the_typed_contracts` (`PartInfo` properties lacked `downloads`)
  - `tests/test_api.py::test_every_download_the_document_lists_is_answered_by_the_route_as_it_says` (no `downloads` in the info document)
  - `tests/test_parity.py::test_the_downloads_of_iso_4017_m8_x_70_are_one_sentence_on_the_cli_the_api_and_export` (`KeyError: 'downloads'`)
- `tests/test_calc.py` was run in the same command: it failed at collection (`ImportError: cannot import name 'Download' from 'screw.calc'`) because its new tests import the class under test. That is a missing symbol, not a fixture fault, but it is not an assertion RED; the three assertion failures above are the machine-readable RED evidence. `gsd_run check tdd-red-evidence` was not run (no persisted report record).
- GREEN: `247 passed` over the three files after the implementation; `make verify` green at both commits.

## Task Commits

1. **Task 1 (tracer): the download state through the document, the model route and the CLI** - `90ad513` (feat)
2. **Task 2: every catalogue row's document against the shared rule** - `afeffd8` (test)

**Plan metadata:** the docs commit that follows this file.

The tracer feedback gate: Task 1's `<verify>` carries only `<automated>` and the mode is `end-of-phase`, so no checkpoint. The verify commands were re-run after the commit (CLI one-liner on M8 x 70 and the grep), passed, and expansion (Task 2) went ahead.

## Files Created/Modified

- `src/screw/calc/__init__.py` - `Download`, aliases, `PartInfo.downloads`, `_DOWNLOADS`, `_downloads`; the fine-STL warning now read from the entries; the stale comment above the thread-length warning removed
- `tests/test_calc.py` - five download tests; the capped-part warning test's comment reworded
- `tests/test_api.py` - `downloads` and the `Download` component pinned to the route's OpenAPI enums and `quality` default; the route-agreement test
- `tests/test_parity.py` - the FRNT-05 three-way test
- `tests/test_presets.py` - the two catalogue-wide tests

## Decisions Made

- Distinct refusals are appended as warnings in entry order (`dict.fromkeys`), so a future kind with several refused entries cannot repeat a sentence.
- No `app.py` or `cli.py` edit: both already emit `derive(...)`; the parity test is the proof.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff B023 on a stub defined inside a loop**
- **Found during:** Task 1 commit (the pre-commit `make verify`)
- **Issue:** the route-agreement test defined its stub inside the per-document loop, closing over a per-iteration list
- **Fix:** hoisted `seen` and `stub` out of the loop; each entry slices `seen` from a length taken before its request
- **Files modified:** tests/test_api.py
- **Verification:** `ruff check .` clean, commit hook green
- **Committed in:** `90ad513`

### Plan wording adjusted

- The plan's route-agreement bullet says "for the default part all four reach the stub". The byte cache is session-wide, and the default part is downloaded by other tests, so a cache hit would answer before the stub. The test uses `d=5.55`, a diameter no other test downloads (the convention at the top of `tests/test_api.py`), as the part with no refused entry. The assertion it makes is the plan's: all four entries reach the stub.

---

**Total deviations:** 1 auto-fixed (1 blocking), 1 test-fixture adjustment
**Impact on plan:** none on the shipped behaviour.

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None. `downloads` is a new member of an existing document on an existing route; no new endpoint, auth path or file access.

## User Setup Required

None - no external service configuration required.

## Housekeeping

- No `docs/tech_debt/` or `docs/ideas/` item filed.
- No `.planning/WINDOWS.md` entry: no stub, skipped test or unrun verify.
- Final gate: `make verify` -> `2633 passed in 65.05s`, coverage 97.33% (floor 96.0%).

## Next Phase Readiness

- Plan 04-16 can read `info.downloads` as described in its `<interfaces>`: four entries in the page's order, `refusal` string or null, per-format first entry not refused is the link.
- G-04-3 stays open until 04-16 lands the page; `/gsd-verify-work` re-runs UAT test 3 after both.

## Self-Check: PASSED

- `src/screw/calc/__init__.py` contains `class Download(BaseModel)`, `downloads: list[Download]` and `download_refusal(p, fmt, quality)` inside `_downloads`.
- Commits `90ad513` and `afeffd8` are ancestors of HEAD.
- Acceptance commands: the three-file pytest run (247 passed), the CLI one-liner on M8 x 70, the presets run (306 passed), the 62-count byte-identity check against `d3eb46f`, and `make verify` all passed.

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-12*
