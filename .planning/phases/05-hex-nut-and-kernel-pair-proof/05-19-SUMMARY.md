---
phase: 05-hex-nut-and-kernel-pair-proof
plan: 19
subsystem: export, bench, security
tags: [nut, fine-stl, export-budget, t-05-12, t-05-10, r16, r17, l16, pre-registered-run]

requires:
  - phase: 05-hex-nut-and-kernel-pair-proof
    provides: R12 (measure the nut caps in their own run), 05-SECURITY.md T-05-12 open, L11/L13 rod method
provides:
  - R16 and R17 in 05-OWNER-READS.md (ceiling C = 5.0 mm and refuse above it; a refused check is not a stop)
  - bench/nut_fine_caps.py, the pre-registered rule and instrument, with its R17 amendment
  - two runs' records and RESULTS.md entries (the stopped first run, the amended second run)
  - calc.thread.NUT_FINE_STL_ROWS, NUT_FINE_STL_CLEARANCE, NUT_FINE_STL_RUN, nut_fine_stl_refusal
  - the nut branch of download_refusal wired to it (API 422 fine_stl_cap, CLI exit 2, info document)
  - decision log L16, the UI contract row, one debt item resolved and one filed
affects: [05-SECURITY.md re-audit (T-05-12, T-05-10), Phase 5 close, Phase 7 re-sweep (OPER-02)]

actuals:
  tokens: 130000
  tasks: 3
  commits: 8
plan_head_before: 1efb765d4ceea6576bca847bf3ef44eeb1159caf
plan_head_after: 568051d93b335bafe2f2ad2feed1d773545d79df

key-files:
  created:
    - bench/nut_fine_caps.py
    - bench/results/phase-05/nut-fine-caps.jsonl
    - bench/results/phase-05/nut-fine-caps-amended.jsonl
    - docs/tech_debt/active/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md
    - docs/tech_debt/resolved/2026-10-14-nut-fine-stl-caps-unmeasured.md
  modified:
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - tests/test_bench.py
    - tests/test_thread_maths.py
    - tests/test_calc.py
    - tests/test_api.py
    - tests/test_cli.py
    - bench/RESULTS.md
    - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md
    - docs/architecture/decision_log.md
    - docs/tech_debt/INDEX.md
    - docs/tech_debt/active/2026-10-14-nut-interim-bounds.md
    - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md

key-decisions:
  - "R16 (owner, 2026-10-20): option-a. C = 5.0 mm; a fine STL above C on a measured key is refused, naming clearance"
  - "R17 (owner, 2026-10-21): option 1. A check row the shipped build refuses is not a file and not a stop; amended re-run under a new run id"
  - "L16 records the nut's 30 caps and supersedes L15's nut fine-STL paragraph"

requirements-completed: [TYPE-03]

status: complete
completed: 2026-10-21
---

# Phase 5 Plan 19: The nut's measured fine-STL cap Summary

**A nut's fine STL past its measured cap of `m` (30 keys: ISO 262 coarse by both hands, from a pre-registered run at clearance 5 mm and s 1e5 mm), or at a clearance above 5 mm, is now refused before the cache, the slot and the pool, on the API, the CLI and the info document; the preview STL and the STEP are never refused.**

## Performance

- **First run** (`2026-10-20-nut-fine-caps`, HEAD `0c349a7`): 3011.1 s in the process (`time -p` real 3012.79, user 12894.22, sys 1334.18); load1 9.89 at 2026-10-20T16:43:05+00:00 before, 9.46 at 17:33:16 after.
- **Amended run** (`2026-10-21-nut-fine-caps-amended`, HEAD `63c22a6`): 2935.7 s (`time -p` real 2937.34, user 12731.02, sys 1347.83), against the 7000 s deadline; load1 7.32 at 2026-10-21T01:48:42+00:00 before, 8.95 at 02:37:37 after. Both on a shared host; the rule reads bytes, never time.
- **Commits:** 8 before this summary's docs commit, measured from the plan-head ledger.
- **`make verify` after the last code commit:** `======================= 3410 passed in 128.02s (0:02:08) =======================` (3369 before the plan's fix; +41 tests). The pre-commit hook ran it, passing, on every commit.

## What happened, in order

1. R16 (owner's `option-a`) recorded; `bench/nut_fine_caps.py` committed with THE RULE before any row (`0c349a7`).
2. First run: 30 caps measured, 1086 ladder rows built, but 46 of 150 check rows were refused by the shipped lead-in countersink piece gate (s = 1e5, clearance -0.05, 0, 0.1). A pre-registered stop condition, so no cap shipped; record committed (`837b0bc`), plan stopped with a checkpoint (`5f8bc34`).
3. The owner ruled R17 (`option 1`, amended re-run). The amendment and R17 were committed before any row of the new run (`9b4fbb7`); the debt item for the refusal was filed (`63c22a6`).
4. Amended run: no stop condition; records and entry committed (`f1488ea`). The instrument is byte-identical between `9b4fbb7` and `f1488ea` (checked with `git diff --quiet`).
5. Task 3 executed: the fix (`b48ce65`) and L16 plus the UI contract (`568051d`).

## Cap equality

The 30 caps of the amended run equal the first run's. All 1236 rows match row for row (role, key, m, clearance, s): the raw and gzip-1 bytes are equal on every row, the outcomes agree (the first run's 46 failed rows are the amended run's 46 refused rows) and the 46 error strings are identical. The per-key table is character-for-character the same. No difference was found, so there is nothing to checkpoint.

## The 30 measured caps (m in mm; C = 5 mm, s = 1e5 mm)

| Size | M2 | M2.5 | M3 | M3.5 | M4 | M5 | M6 | M7 | M8 | M10 | M12 | M14 | M16 | M18 | M20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| right | 12 | 13 | 15 | 18 | 21 | 24 | 30 | 30 | 38 | 36 | 41 | 46 | 45 | 54 | 36 |
| left | 15 | 17 | 19 | 22 | 25 | 30 | 38 | 38 | 47 | 50 | 56 | 61 | 59 | 73 | 47 |

Each cap row fits at 0.954 to 0.995 of 64 MiB, and cap + 1 is over by 0.03 to 5.8 %. The closest to an ISO 4032 height is M20 right, 36 mm against 18 mm. The planner's M20 estimate was 37 to 39 mm; measured, right is 36 and left is 47.

## Task Commits

| Commit | What |
|---|---|
| `0c349a7` | feat(05-19): the run with its rule fixed before any row (R16, instrument, 11 tests) |
| `837b0bc` | docs(05-19): record the first run (stopped) |
| `5f8bc34` | docs(05-19): the stop summary and STATE |
| `9b4fbb7` | feat(05-19): R17 and the amended rule, before any row of the new run |
| `63c22a6` | docs(05-19): file the lead-in gate refusing a valid nut at huge s |
| `f1488ea` | docs(05-19): record the amended run |
| `b48ce65` | fix(05-19): refuse a nut's fine STL past its measured cap (code, tests, debt resolved) |
| `568051d` | docs(05-19): record L16, the nut's measured fine-STL caps (and the UI contract) |

Records: `bench/results/phase-05/nut-fine-caps.jsonl` (1238 lines, sha256 `8682c7023253c1320ba6645fd72021e9122bec16c232c9a4064b7219eba92ade`) and `nut-fine-caps-amended.jsonl` (1238 lines, sha256 `64ae355a043687e30bcf98d334f6b9adf1814005e5741a01591710915fa26324`).

## Behaviour shipped

- `nut_fine_stl_refusal(d, pitch, m, clearance, left_hand)`: None off the 30 keys (no rod cap, no nearest row, D-03); the clearance is judged first (`clearance: ` above 5.0 mm); then `m: ` past the key's cap. Both sentences name the run and offer the preview STL and the STEP; no braces.
- `download_refusal`'s nut branch calls it for stl/fine only. API: 422 `fine_stl_cap`, loc `["query"]`, backend never called, preview served. CLI: exit 2, `error: m: ...`, nothing written. Info document: the sentence on the stl/fine downloads entry and once in the warnings.
- Every GOST ISO 4032-2014 row at its own s and m_max, clearance 0.1, both hands, is served its fine STL (tested).
- Tests (every name contains `nut_fine_stl` or `nut_fine_caps`): the typed table equals the code and both runs' committed records, recomputed without importing bench; each header's preset equals `screw.solid.TESSELLATION["fine"]`; the cap, the next float above it and the first over-budget m; the clearance ceiling at `nextafter(5.0)`; off-key nuts; the replaced 05-05 absence pin; API and CLI.
- Existing tests changed because of the cap: only the 05-05 absence pin (`test_a_nut_download_is_never_refused_until_the_nut_fine_stl_caps_are_measured`, replaced). No other existing test needed to change.

## Debt

- **Resolved:** `docs/tech_debt/resolved/2026-10-14-nut-fine-stl-caps-unmeasured.md` (moved in `b48ce65`, INDEX row moved, `Resolved in:` line). `2026-10-14-nut-interim-bounds.md` retitled and repointed at the resolved path.
- **Filed:** `docs/tech_debt/active/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md` (Severity: must; trigger: before the nut's s ceiling is relied on, or Phase 7 OPER-02), with its INDEX row. It states that the s = 1e5 failure and the s <= 1e3 builds come from a scratch probe, not a record; it is user-visible as a 422 `build_error`, never a wrong part. The RESULTS.md amended entry cross-references it.

## Deviations from Plan

- **[Owner ruling R17 - amendment]** The rule was amended after the first run's data, by the owner, with a new run id and its own records file. The first run's records and entry stand unedited. The run's stop on 46 refused checks, and the amendment that followed, are the plan's own stop path, not a defect fixed inline.
- The plan's interface line gives `gzip1(data) -> (bytes, seconds)`; it returns `(compressed size, seconds)`. The instrument uses it as it is.
- The first launch of the first run failed in the shell (`time -p` under zsh) before Python started: no row ran, no file was written. Disclosed in the RESULTS.md entry.
- The plan's verify lines use `make test PYTEST_ARGS=...`; the targeted tests were run with `.venv/bin/python -m pytest ... -n0 --no-cov -k ...`, and the whole suite with `make verify`.
- The plan named a possible `math.inf` cap for a key that fits to the turn cap; no key did, so the typed table is all finite and no special handling was written.
- A diagnostic probe (scratch, run once after the first run, not committed, not a record) showed the gate failing at s = 1e5 and building at s <= 1e3 for three sizes. It informed the debt item and is labelled as a scratch reading everywhere it is cited.

## Known Stubs

None.

## Threat Flags

None new. The mitigation for T-05-12 and T-05-10 (the missing nut fine-STL refusal) is now in code, ready for the orchestrator's re-audit; 05-SECURITY.md was not edited. T-05-45 to T-05-50 as the plan registers them: the refusal precedes the cache, slot and pool (tested through the counting backend); the rule preceded both runs' rows and the instrument is unchanged between the amendment and the records commits; off-key nuts are uncapped and tested; the header preset is compared with the shipped one.

## Self-Check: PASSED

- FOUND: bench/nut_fine_caps.py, both records files (1238 lines each), the resolved and the new debt items
- FOUND: `def nut_fine_stl_refusal(` and `NUT_FINE_STL_ROWS` in src/screw/calc/thread.py; `nut_fine_stl_refusal(` in src/screw/calc/__init__.py
- FOUND: commits 0c349a7, 837b0bc, 5f8bc34, 9b4fbb7, 63c22a6, f1488ea, b48ce65, 568051d as ancestors of HEAD
- FOUND: `## L16` once in the decision log, L15's paragraph ends with the pointer; the UI-SPEC row title `Nut fine-STL refusal (none)` is gone and the `m: ` pattern is in
- RUN: the plan's debt verify printed `debt ok`; `make verify` passed (3410 tests)
