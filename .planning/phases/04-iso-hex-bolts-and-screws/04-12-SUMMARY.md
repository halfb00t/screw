---
phase: 04-iso-hex-bolts-and-screws
plan: 12
subsystem: api-cli
tags: [presets, catalogue, api, cli, parity, tabl-01, thrd-03]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-08: calc.presets.match; 04-09/04-10: the 294-row catalogue (tables.presets.catalogue, expand); 04-05: the shared thread_length conflict check and the CLI/API parity pattern"
provides:
  - "calc.presets.PresetEntry, PresetCatalogue, catalogue_document(kind), expand(kind, preset_id), AXES"
  - "GET /api/presets?kind= : the catalogue as one kernel-free document {kind, axes, rows}"
  - "screw presets <kind>: prints the identical JSON"
  - "--preset ID on screw info and screw export: expands the row into mm fields, explicit flags win, the conflict rule runs on the merged values"
  - "tests/test_presets.py; tests/test_parity.py HAND_WRITTEN positive flag rule"
affects: [04-13 (the page builds its picker from /api/presets), 04-14]

actuals:
  tokens: 6738
  tasks: 2
  commits: 2
plan_head_before: d5d236fdeac4b371281138aa87bc9531f728ef52
plan_head_after: bf99d28182a11236c41d92020e9155df812e6dbc

tech-stack:
  added: []
  patterns:
    - "the catalogue document is built in calc (kernel-free, lru_cache per kind), so the route and the CLI subcommand share one builder and cannot drift"
    - "the unknown-kind 404 is one helper (_known_kind) used by /api/schema and /api/presets"
    - "the preset is expanded in cli._params before the conflict check and the model; the model and the model routes never see a preset id"

key-files:
  created:
    - tests/test_presets.py
  modified:
    - src/screw/calc/presets.py
    - src/screw/app.py
    - src/screw/cli.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_parity.py
    - README.md

key-decisions:
  - "The 404 body of /api/schema moved into a small helper _known_kind that /api/presets reuses; the schema route's behaviour is unchanged (its existing test passes untouched)"
  - "HAND_WRITTEN in the parity test is introduced in Task 1 without --preset (so that commit is green) and gains --preset in Task 2 with the flag"
  - "Refused fine-STL ISO 4017 presets: 62, the number RESEARCH Alert 7 estimated, pinned as a literal"

patterns-established:
  - "Parity of flags is a positive rule: ['--help', *HAND_WRITTEN[command], *fields], with a teeth test that plants a stray flag"

requirements-completed: []

duration: about 40 min
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 12: The catalogue on the API and the CLI Summary

**`GET /api/presets?kind=bolt` and `screw presets bolt` serve and print one 294-row catalogue document; `--preset <id>` on `screw info` and `screw export` fills the mm fields, explicit flags win, and the model routes still take millimetres only.**

## Accomplishments

- One document `{kind, axes: [Standard, Size, Length], rows}`; each row has `id`, `display` (U+00D7, second-choice sizes bracketed), `designation`, `picker` (three strings), `fields` (d, pitch, length, s, k, thread_length in mm) and `citation`. The API and the CLI parse to the same JSON for every kind in `KINDS` (parity test).
- `/api/presets?kind=nut` is the `/api/schema` 404 `unknown_kind` (names the known kinds); no `kind` is a 422; a repeated `kind` is the duplicate 422; the OpenAPI document references `PresetCatalogue` for the route. `preset` on `/api/bolt/info` and `model.stl` is a 422 `extra_forbidden` with `loc ["query", "preset"]`; the empty query is the exact match of `iso4017:M6x20`.
- `--preset` (`info`: before the generated group; `export`: after `--quality`) uses `_Once`, so a repeat exits 2. An unknown id exits 2 with `error: preset: unknown id '<id>' for kind bolt; list them with screw presets bolt`; ids are case-sensitive. The explicit flags are laid over the expanded row and then the 04-05 conflict check and the model run on the merged values: `--preset iso4014:M10x80 --length 20` exits 2 with `error: thread_length and length: thread_length 26 mm is longer than length 20 mm; ...`; `--length 85` reports length 85, thread_length 26, preset custom.
- Every one of the 294 rows round-trips (parametrised): `BoltParams.model_validate(fields)`, `derive(...).preset` is the exact match with the row's id and display, `expand` returns the fields, and the row's own fields pass the conflict rule.
- Refused fine STLs (TYPE-02 boundary): 62 ISO 4017 presets (first `iso4017:M8x70`, last `iso4017:M20x200`), each with a built thread above its right-hand cap in `FINE_STL_ROWS`; 0 ISO 4014 presets; the longest ISO 4017 preset is 200 mm. The literal 62 equals RESEARCH Alert 7's estimate; the Phase 7 re-sweep moves it.
- README "## Use" shows `screw presets bolt` and `screw info bolt --preset iso4014:M10x80`; `test_readme_cli_examples_run` runs both.
- Verified: `make verify` exits 0, **2615 passed**, coverage 97.57% (floor 96.0%); `make lint-imports`: 9 kept, 0 broken.

## Task Commits

1. **Task 1: The catalogue on the API and the CLI, one document** - `2f7dac4` (feat)
2. **Task 2: --preset fills the fields, explicit flags win, every row round-trips** - `bf99d28` (feat)

The first attempt at each commit was rejected by the pre-commit hook for ruff findings (PT018 compound asserts; RUF001 for a literal U+00D7 in a test string). Fixed and re-committed; nothing was committed red.

## Files Created/Modified

- `src/screw/calc/presets.py` - `PresetEntry`, `PresetCatalogue`, `AXES`, `catalogue_document`, `expand`.
- `src/screw/app.py` - `GET /api/presets`, `_known_kind`, docstring route line; imports `.calc.presets` only (contract 5 holds).
- `src/screw/cli.py` - `presets` subcommand and `cmd_presets`, `_add_preset`, `--preset` expansion in `_params`.
- `tests/test_presets.py` (new) - round trip, `--preset` behaviours, refused count.
- `tests/test_api.py`, `tests/test_cli.py`, `tests/test_parity.py` - route, subcommand, OpenAPI, `HAND_WRITTEN` positive rule with a stray-flag teeth test, CLI = API document, `--preset` in the repeated-option list.
- `README.md` - the two examples (catalogue/preset section only).

## Decisions Made

- `_known_kind` factors the existing 404 so both routes give the identical body; the `/api/schema` test is unchanged and green.
- `expand(kind, id)` and `catalogue_document(kind)` raise `TypeError` for a kind without a catalogue, like `derive`; today `KINDS` holds only `bolt`, so the TypeError branch is exercised with `"nut"`.
- `fields` (a dict) and `picker` (a list) are the document's shapes; `PresetRow.choice` stays the int that decides the bracket, as the plan's artifact note says.

## TDD Gate Compliance

The pre-commit gate rejects a failing suite, so no separate RED commit was possible (as in every earlier TDD plan of this phase). RED was demonstrated by reverse-applying the source diff (my own uncommitted change) over the new tests, then re-applying it:

- **Task 1 RED:** tests written after the code, then the source reverted for a run: `pytest tests/test_parity.py tests/test_api.py tests/test_cli.py -n0 --no-cov`: 7 failed, 227 passed (catalogue route, 404, no-kind, OpenAPI, parity, `screw presets` all failing). GREEN: 234 passed. A weaker RED than test-first.
- **Task 2 RED:** same method, `--preset` source reverted: `pytest tests/test_presets.py tests/test_parity.py tests/test_cli.py`: 9 failed, 382 passed. GREEN: 391 passed. One test fault found on GREEN and fixed in the test: `iso4014:M10x90` is itself a catalogue row, so the override test uses `--length 85`.
- **GREEN:** `2f7dac4` and `bf99d28`, `make verify` green in the hook on each and again afterwards. No REFACTOR commit. `gsd check tdd-red-evidence` not run (pytest console output is not a supported format; same as 04-05 to 04-11).

## Deviations from Plan

None - plan executed as written. Two notes:

- The plan lists `tests/test_parity.py` under Task 1 and the `HAND_WRITTEN` positive rule under Task 2. I introduced `HAND_WRITTEN` in Task 1 with the flags that existed then and added `--preset` in Task 2, so each commit is green. Final state is as pinned.
- The plan's Task 2 sketch says `test_the_cli_flags_are_the_model` compares the three sets separately; it loops over `HAND_WRITTEN.items()` and compares `["--help", *hand_written, *fields]` exactly for both commands.

## Issues Encountered

None beyond the hook's ruff rejections above.

## Known Stubs

None.

## Threat Flags

None. `/api/presets` and the `--preset` flag are the surfaces the plan's threat model covers: T-04-18 (mitigate) dict lookup in `expand`, unknown id exits 2, `_Once` refuses a repeat - tested; T-04-19 (accept) same `!r` echo as `/api/schema`; T-04-20 (mitigate) in-memory rows, `lru_cache` per kind, no kernel.

## Next Phase Readiness

04-13 can build the picker from `GET /api/presets?kind=bolt` (`axes` for the select labels, each row's `picker` for the options, `fields` for the values the pick writes, `display` for the badge). The model routes refuse a `preset` key, so the page must write the six mm fields into the link, never an id.

Filed: no docs/ideas or docs/tech_debt item.

## Self-Check: PASSED

- `tests/test_presets.py` present; `src/screw/calc/presets.py` has `class PresetCatalogue` and `def catalogue_document(`; `src/screw/app.py` has `@app.get("/api/presets")`; `src/screw/cli.py` has `def cmd_presets(` and `"--preset"`.
- Commits `2f7dac4` and `bf99d28` are ancestors of HEAD; `git rev-list --count d5d236f..HEAD` is 2.
