---
phase: 03-real-helical-thread
reviewed: 2026-10-10T23:30:00Z
depth: standard
files_reviewed: 43
files_reviewed_list:
  - .github/workflows/grid.yml
  - bench/corpus.py
  - bench/memory.py
  - bench/README.md
  - bench/RESULTS.md
  - bench/thread_spike/helical.py
  - bench/thread_spike/maths.py
  - bench/thread_spike/measure.py
  - bench/thread_spike/pair.py
  - bench/thread_spike/worker.py
  - docs/architecture/decision_log.md
  - docs/architecture/overview.md
  - docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md
  - docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md
  - docs/tech_debt/INDEX.md
  - docs/tech_debt/resolved/2026-10-06-collapsed-thin-solid-served-as-200.md
  - docs/tech_debt/resolved/2026-10-06-repeated-query-key-silently-wins.md
  - docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md
  - docs/tech_debt/resolved/2026-10-06-ui-hides-warnings-on-failed-update.md
  - Makefile
  - pyproject.toml
  - README.md
  - scripts/pr_land.py
  - src/screw/__init__.py
  - src/screw/app.py
  - src/screw/calc/__init__.py
  - src/screw/calc/thread.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/solid/__init__.py
  - src/screw/solid/bolt.py
  - src/screw/solid/helical.py
  - src/screw/static/app.js
  - src/screw/static/style.css
  - tests/test_api.py
  - tests/test_bench.py
  - tests/test_calc.py
  - tests/test_cli.py
  - tests/test_grid.py
  - tests/test_params.py
  - tests/test_parity.py
  - tests/test_solid.py
  - tests/test_thread_maths.py
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-10
**Depth:** standard
**Files Reviewed:** 43
**Status:** issues_found

## Summary

Reviewed the Phase 3 range `e772716..HEAD`. The gate itself holds up. `check_solid` runs inside the function `lru_cache` wraps, a refusal raises and so is never cached, the NaN-safe comparison is right, and the `not abs(rel) <= T_GATE` form is tested. The seven `FINE_STL_ROWS` caps match `bench/results/thread-spike/2026-10-08-a-grid.jsonl` for the right-hand rows (I recomputed them from the records). The repeated-key refusal works on the API (every route) and the CLI (every flag). The JS builds all nodes with `textContent`. The grid workflow has no PR or push trigger and `contents: read` only. Test counts in RESULTS.md (843 collected, 60 grid cells) reproduce.

One real defect: a tiny `pitch` turns the model-boundary validator into an unhandled `OverflowError` (500 on the API, a raw traceback on the CLI). The rest are boundary-honesty problems against L02 and records that claim more than the code or the recorded runs show. These are an empty hash value that silently opens the default part, a left-hand fine-STL refusal that cites a measurement that was never made, a root-radius message whose own number can be refused, and a hand test that cannot see a tail segment of the wrong hand.

I probed the following myself with the project venv, single runs on macOS arm64 under load:
- `BoltParams(pitch=5e-324)` raises `OverflowError`.
- `GET /api/bolt/info?pitch=5e-324` returns 500.
- A mutant that builds the tail segment right-handed passes `test_the_hand_decides_which_way_the_thread_climbs_and_both_pass_the_same_gate`.
- `bolt d=100 length=200` fine STL: 53.3 s, 1.30 GB, peak RSS 9143 MiB.

## Critical Issues

### CR-01: A tiny pitch makes the model validator raise `OverflowError`, so the API answers 500 and the CLI prints a traceback instead of a 422

**File:** `src/screw/calc/thread.py:110-135` (called from `src/screw/params.py:112`)
**Issue:** `turn_cap_refusal` builds its message with `turns_of(length, pitch)`, which does `float(Fraction)`. When the quotient is above about 1.8e308 (any `pitch` below roughly `length / 1.8e308`, including every subnormal), `float()` raises `OverflowError: integer division result too large for a float`. pydantic only converts `ValueError` and `AssertionError` raised in a validator into a `ValidationError`, so this escapes the model boundary. `pitch` has `gt=0` and no other bound, and `5e-324` is a legal positive finite float.

Reproduced:
- `BoltParams(pitch=5e-324)` and `BoltParams(pitch=1e-310, length=1e5)` raise `OverflowError`.
- `GET /api/bolt/info?pitch=5e-324` returns `500 Internal Server Error`.
- `screw info bolt --pitch 5e-324` dies with a traceback.
- `pitch=1e-300` is fine, because `2e+301` still fits a float.

This breaks the standing rule that a direct conflict is a 422 naming the fields, and "a parameter is validated once at the model boundary". It is reachable unauthenticated from the web form, since a number input accepts `5e-324`. `calc._bolt` already catches `OverflowError` for the same function; the validator does not. Neither `tests/test_params.py` nor `tests/test_thread_maths.py` probes a pitch past the float range.

**Fix:**
```python
def turns_of(length: float, pitch: float) -> float:
    try:
        return float(_exact(length) / _exact(pitch))
    except OverflowError:
        return math.inf   # derive() already drops a non-finite row and warns
```
With this the refusal text reads "inf turns is past the 250-turn cap", which is true. Add API, CLI and `params` tests at `pitch=5e-324` and at `pitch=1e-310, length=1e5`, expecting 422, exit 2 and `ValidationError` of type `turn_cap`.

## Warnings

### WR-01: `#d=` (an empty hash value) silently opens the default part, and the records say such a link is refused

**File:** `src/screw/static/app.js:175-181` (records: `docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md`, `docs/architecture/decision_log.md` L12 "Links and keys")
**Issue:** The unreadable-value guard is `given !== null && given !== '' && read(input) === ''`. The `given !== ''` clause exempts a key that is present with an empty value. For `#d=`, `#length=` or `#pitch=`, `write(input, '')` leaves the control empty and `partQuery()` (line 190) skips empty values. The page then builds the default part under a link that named a field, and `writeHash` rewrites the link without the key. That is the silent change the item was filed for (L02: "a parameter the user did not set must never silently change the part"), and the API answers `?d=` with a 422. The resolved record and L12 say the page refuses an unreadable key "exactly as it refuses an unknown kind". That claim outruns the code for the empty value. `test_the_ui_refuses_a_link_it_cannot_honour` pins the exempting clause as source text (`given !== '' && read(input) === ''`), so the gap is locked in by the test.

**Fix:** Drop the `given !== ''` clause, so any present key whose control reads back empty is refused:
```js
: given !== null && read(input) === '';
```
Update the pinned statement in `tests/test_parity.py`. Add a sentence to the resolution record naming the empty value, or keep the exemption deliberately and say so in L12.

### WR-02: The fine-STL refusal applies the right-hand cap to left-hand parts and says "L11 measured it over the export budget"; the measured quantity is raw plus gzip, not the STL

**File:** `src/screw/calc/thread.py:138-173`, `src/screw/app.py:88-92`, `docs/architecture/decision_log.md` L12 "Caps"
**Issue:** I recomputed first-over-budget lengths per hand from the committed grid records:

| Size | Right hand, first over budget (mm) | Left hand, first over budget (mm) |
|---|---|---|
| M8 | 68 | none measured (fits to 80) |
| M10 | 57 | 73 |
| M12 | 61 | 78 |
| M14 | 59 | 79 |
| M16 | 53 | 76 |
| M18 | 66 | 92 |
| M20 | 65 | 92 |

`fine_stl_refusal` ignores `left_hand`, so a left-hand M10 at 60 mm is a 422 that says "L11 measured it over the export budget". L11 measured that part inside the budget, and the refusal covers a range nobody measured. D-02's own rule is to refuse only where L11 measured a limit.

The "over budget" criterion in the records is `fine raw + gzip-1 bytes > 67108864`, the sum of two blobs. At M8 L=68 the raw fine STL is 45,659,684 bytes, which is under 64 MiB. `_BlobCache.put` drops only a single blob larger than the budget, so for these rows the blobs evict each other instead of being "dropped without caching". The `app.py` comment ("L11 measured fine STLs over it from M8 L=68 up", "`put` drops an over-budget blob") and the user-facing message both misstate what was measured.

**Fix:** Either key the rows on `(d, pitch, left_hand)` with the left-hand caps above (the M8 left row has no measured stop), or keep the single conservative cap and reword both texts, for example "the fine STL plus its gzip copy was measured over the 64 MiB export budget for the right-hand rod; applied to both hands". Correct the `app.py` comment the same way.

### WR-03: The root-radius message offers "the largest pitch for this d" with 6 significant figures, and the printed value is itself refused for about half of all diameters

**File:** `src/screw/calc/thread.py:121-127`
**Issue:** `largest = d / (2 * thread_depth(1.0))` is the supremum, at which the root radius is exactly 0 and is refused (`root > 0`). It is printed with `:g`, so it is rounded to nearest. Over `d = 0.1 .. 199.9` in 0.1 steps, 993 of 1999 diameters print a value that rounds up and is refused again. Example: `d=1.1`, limit 1.0161364..., printed `1.01614`. A user who follows the instruction loops on the same 422. The tests only check `"5.54" in refusal` for `d=6`, where the value happens to round down.

**Fix:** Print a value that is accepted. Round the limit down and trim a few ulps, for example `math.floor(largest * 1e4) / 1e4`, or say "below {largest:g}". Test it by feeding the printed number back into `root_radius_refusal` for a sweep of diameters.

### WR-04: Root radii up to about 1e-4 mm pass validation and the kernel then fails with a generic message, so "above 0" is not the real boundary

**File:** `src/screw/calc/thread.py:115-127`, `src/screw/solid/__init__.py:125-134`
**Issue:** `root_radius_refusal` accepts any root radius above 0. Probe at `d=6` (single run): pitch 5.54 (root 1.4e-3 mm), 5.541 and 5.542 (root 3.0e-4 mm) build; pitch 5.5425 (root 3.4e-5 mm) and above fail inside OpenCascade with `Standard_Failure`, which `_build_checked` rewrites as "Geometry kernel failed (Standard_Failure); check d, pitch and length." (a 422 `build_error`). Nothing is served wrongly, since the gate holds. But the user-visible contract L12 states ("a root radius at or below zero is a 422 naming d and pitch") does not match the real limit. There is a window where the model says the pair is fine and the build says "check d, pitch and length" without naming the cause, and the window is not recorded as unmeasured. Between 5.542 and 5.5425 it is unmeasured where it flips.

**Fix:** Measure the smallest root radius that builds (as a fraction of `d` or `pitch`), set it as an INTERIM minimum in `root_radius_refusal` with the same message, and list it in the interim-bounds item. Short of that, make the generic `Standard_Failure` text say "d and pitch leave almost no root".

### WR-05: A valid, in-cap request with default pitch (`d=100&length=200`) exceeds both interim backstops; the records and the bench corpus do not say so

**File:** `src/screw/params.py:18-31`, `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`, `bench/corpus.py:18-25`, `bench/README.md` ("The corpus")
**Issue:** I ran the bench corpus's heaviest entry through `screw.solid.export` (one run, macOS arm64, load 15). It is a plain `pitch`-omitted request: 200 turns, off the seven rows, so no fine cap applies, and `GET /api/bolt/model.stl?d=100&length=200` reaches it.

| Request | Time | Output | Peak RSS |
|---|---|---|---|
| fine STL | 53.3 s | 1,303,132,684 bytes | 9143 MiB |
| preview STL | 4.1 s | 256,952,984 bytes | 1588 MiB |

The 30 s `SCREW_BUILD_TIMEOUT` and the 4g `mem_limit` are both exceeded, and those numbers are for the in-process export alone, before gzip or the bytes cache. The debt item's worst case is `d=100, pitch=5, length=1250`, and it records that "which backstop fires first was not measured". The default-pitch case is far easier to reach: no unusual pitch, round numbers, and the bench corpus itself.

This phase made `INTERIM_MAX_MM`'s stated premise false (the `params.py` comment says the bound exists so one valid request cannot outgrow `mem_limit`) and shipped with the item tagged `must`. A single unauthenticated GET can hold a worker for the full timeout and drive the container toward OOM. That is an availability exposure the owner accepted in D-18, but the recorded example understates it. `bench/corpus.py` and `bench/README.md` describe the corpus as exercising the harness and "far below the D-14 corner" without saying that `make bench.memory` and `bench.latency` now drive entries that time out and exceed `mem_limit`.

**Fix:** Add the `d=100, length=200` row (above, with host and load) to the debt item and to the corpus docstring. Decide whether the item should be re-tagged `blocker`, since AGENTS.md's "paid-API drain" rubric is the nearest category for a one-request resource exhaustion. Measure memory at the 30 s kill point so the item can say which backstop fires first.

### WR-06: The hand test cannot see a tail segment of the wrong hand, and the volume gate cannot either

**File:** `tests/test_solid.py:217-245` (builder: `src/screw/solid/helical.py:97-111`)
**Issue:** `_inside_at` probes only `z = 2.25 * pitch`, inside the first 3-turn base segment of the M6x20 rod. The tail segment is built by a separate `twist(..., left_hand)` call. I patched `twist` so the tail drops `left_hand` (the rod is then left-handed for 18 mm and right-handed for 2 mm). The existing probe still reads `(False, True)` and the test passes. A probe at `z = 19.25` reads `(True, False)`, which is the wrong hand. The volume gate cannot see hand, as the test's own comment says, so a regression in how the tail or the folded last segment receives `left_hand` ships a mixed-hand thread with no failing check. The hand is a user-visible, link-stable parameter (D-09).

**Fix:** In `test_the_hand_decides...`, probe each hand at both the base region and the tail (`z = 18 + 0.25 * pitch`) and at a translated copy (`z = 3 + 2.25 * pitch`). Do the same for one length that folds a short tail (`d=3.5, pitch=0.6, length=5.4`).

## Info

### IN-01: `derive()` prints numbers for a length the builder is known to refuse

**File:** `src/screw/calc/__init__.py:48-85`
**Issue:** `GET /api/bolt/info?length=1e-9` is a 200 with `turns` and `volume` rows (2.3e-8 mm3), while `model.stl` for the same part is a 422 (`MIN_TAIL_MM`, D-17), and `screw info bolt --length 1e-9` prints the same document. L12 accepts this ("no lower bound ... in params"), but `MIN_TAIL_MM` is kernel-free knowledge. A warning on the info document, as `fine_stl_refusal` already does, would keep "a number the tool prints" honest. The constant lives in `solid/helical.py`, so it would have to move to `calc/thread.py` first.
**Fix:** Move `MIN_TAIL_MM` to `calc/thread.py`, import it back in the builder, and add a warning (not a refusal) to `_bolt` below it.

### IN-02: A comment in `_serve` is now attached to the wrong code

**File:** `src/screw/app.py:406-419`
**Issue:** The block "A plain local, not middleware or contextvars -- minted once here ..." describes `request_id = uuid.uuid4().hex[:8]`. The new refusal block was inserted between the comment and the line it documents, so the comment now reads as describing `download_refusal`.
**Fix:** Move the refusal block above the comment, or move the comment down to `request_id`.

### IN-03: `check_solid` ignores the volume estimator's own error estimate

**File:** `src/screw/solid/__init__.py:86-94`
**Issue:** `BRepGProp.VolumeProperties_s(..., eps, ...)` returns the achieved relative error (8.2e-7 at M6x20, probed). `precise_volume` discards it. If integration did not converge to `PRECISE_EPS`, the reading is less trustworthy than the gate assumes, and `T_GATE` is only ten times the largest observed disagreement. Not shown to fail on any measured row.
**Fix:** Return the estimate and refuse when it exceeds, say, `T_GATE / 10`, or record in L12 that the estimate is deliberately unused.

### IN-04: Redundant assertion in the grid cell test

**File:** `tests/test_grid.py:73`
**Issue:** `assert built == len(lengths)` can never fail on its own. A row where `thread()` raised appends to `failures` and the line above already asserts `not failures`. Harmless, but it reads as a coverage check it is not.
**Fix:** Delete it, or count `built` after `check_solid` and assert on that.

---

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
