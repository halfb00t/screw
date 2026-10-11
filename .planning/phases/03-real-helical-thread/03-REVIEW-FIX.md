---
phase: 03-real-helical-thread
fixed_at: 2026-10-11T00:00:00Z
review_path: .planning/phases/03-real-helical-thread/03-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 3: Code Review Fix Report

**Fixed at:** 2026-10-11
**Source review:** .planning/phases/03-real-helical-thread/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (CR-01, WR-01, WR-03, WR-06, IN-02, IN-04, the explicit list from the owner)
- Fixed: 6
- Skipped: 0
- Not touched, deferred by the owner: WR-02, WR-04, WR-05, IN-01, IN-03

**Where it ran:** `workflow.use_worktrees` is `false` in `.planning/config.json`, so no worktree, temp branch
or recovery sentinel was created. Every edit, commit and the final gate ran in the main checkout on
`gsd/phase-03-real-helical-thread`. All numbers below are reproducible from this tree.

## Fixed Issues

### CR-01: A tiny pitch makes the model validator raise `OverflowError`

**Files modified:** `src/screw/calc/thread.py`, `tests/test_params.py`, `tests/test_thread_maths.py`, `tests/test_api.py`, `tests/test_cli.py`
**Commit:** c28de09
**Applied fix:** `turns_of` returns `math.inf` on `OverflowError`, as the finding says. The refusal text then reads
"length and pitch: inf turns is past the 250-turn cap, ..." which is true, and `derive()` still drops a non-finite row with a warning.
Tests, each at `pitch=5e-324` and at `pitch=1e-310, length=1e5`:
- maths: `turns_of` is `inf`; the refusal contains "inf turns is past the 250-turn cap".
- `params`: `ValidationError`, type `turn_cap`, `ctx.fields == ["length", "pitch"]`, message starts "length and pitch: inf turns is past the 250-turn cap".
- API: `/api/bolt/info` and `/api/bolt/model.stl` give 422, type `turn_cap`, fields `["length", "pitch"]` (added to the existing parametrised test).
- CLI: `screw info bolt --pitch 5e-324` and `--pitch 1e-310 --length 1e5` exit 2 with `error: length and pitch: inf turns`, and stderr has no `Traceback`.

With the source change reverted the new tests fail with `OverflowError: integer division result too large for a float`
(9 failures), and pass with it. The first commit attempt was rejected by the hook for one E501 line in `tests/test_cli.py`; it was
wrapped and the commit then went through (one commit, no `--no-verify`).

### WR-01: `#d=` (an empty hash value) silently opens the default part

**Files modified:** `src/screw/static/app.js`, `tests/test_parity.py`, `docs/tech_debt/resolved/2026-10-06-ui-drops-foreign-hash-keys.md`
**Commit:** e48b8ac
**Status:** fixed: requires human verification (source-text pin only, no browser in the gate)
**Applied fix:** dropped the `given !== ''` exemption, so the guard is `given !== null && read(input) === ''`; the code comment now
says why. `test_the_ui_refuses_a_link_it_cannot_honour` pins the new statement and asserts `"given !== ''"` is gone from the source.
The resolved record gained one sentence naming the empty value; nothing else in it changed. Like the original item, whether a
browser reads back `''` for `#d=` is not run in a browser here (L01); a `write(input, '')` leaving the number input empty is the
reviewer's reading and the existing assumption in the record. L12's text ("repeated, foreign or unreadable key") already covers it.

### WR-03: The root-radius message prints a "largest pitch" that is itself refused

**Files modified:** `src/screw/calc/thread.py`, `tests/test_thread_maths.py`
**Commit:** 78cc346
**Status:** fixed: requires human verification (new rounding logic; the sweep proves it on 1999 diameters)
**Applied fix:** a new `_largest_accepted_pitch(d)` truncates the supremum toward zero to at most 6 significant figures (`Decimal`,
`ROUND_DOWN`) and re-checks with the same `d / 2 - thread_depth(p) > 0` the refusal uses, dropping a digit when 6 figures still land on
the boundary. If no candidate is accepted (`d=5e-324`, where `d / 2` underflows) the message carries no pitch at all, per L02, rather than a plausible one. The
text now reads "...; the largest pitch for this d, to 6 significant figures, is 5.54256" (the `"5.54"` assertion still holds).
Tests: a sweep over `d = 0.1 .. 199.9` in 0.1 steps (1999 diameters) parses the printed number, feeds it back into `root_radius_refusal`
and asserts it is accepted and within 1e-5 relative of the supremum; a parametrised check at `d` of 1e-300, 1e-4, 1.1, 6, 1e5; and the
no-number case. With the old `:g` formatting the d=1.1 case fails (printed 1.01614 against a limit of 1.016136).

### WR-06: The hand test cannot see a tail segment of the wrong hand

**Files modified:** `tests/test_solid.py`
**Commit:** 7799d2b
**Applied fix:** `_inside_at` takes `z`; `test_the_hand_decides...` is parametrised over M6x20 (probes at `z = 2.25`, `3 + 2.25`,
`18 + 0.25`: base, translated copy, tail) and the folding length `d=3.5, pitch=0.6, length=5.4` (probes at `2.25p`, `3p + 2.25p`,
`3.6 + 0.25p`; confirmed `5.4 // 1.8` gives 3 full segments with an 8.9e-16 mm remainder, so the last twist is the folded one). Both
hands are asserted at every height, plus the existing single-solid/valid/volume checks.

Mutation proof (temporarily changed `twist(d, pitch, length - z0, clearance, left_hand)` to drop `left_hand` in
`src/screw/solid/helical.py`; restored with `git checkout -- src/screw/solid/helical.py`, `git diff --quiet src/` clean afterwards):

```
M6x20-base-copy-tail:  AssertionError: 18.25   assert (True, False) == (False, True)
folded-tail:           AssertionError: 3.75    assert (True, False) == (False, True)
2 failed, 30 deselected
```

On the unmutated source: `2 passed, 30 deselected`. The mutation is not in any commit.

### IN-02: A comment in `_serve` is attached to the wrong code

**Files modified:** `src/screw/app.py`
**Commit:** cca06d3
**Applied fix:** moved the refusal block above the "plain local, not middleware or contextvars" comment so it sits directly over
`request_id = uuid.uuid4().hex[:8]`. Comment move only, no code change.

### IN-04: Redundant assertion in the grid cell test

**Files modified:** `tests/test_grid.py`
**Commit:** aef047d
**Applied fix:** deleted `assert built == len(lengths)` together with the `built` counter it alone used. The four M2 grid cells
(`-m grid -k 'M2-'`) still pass.

IN-02 and IN-04 are separate commits (unrelated concerns, one commit per finding).

## Skipped Issues

None of the six was skipped. WR-02, WR-04, WR-05, IN-01 and IN-03 were not attempted by owner instruction (they need
measurements or rule decisions).

## Final gate

`make verify`, run once after the last commit in the main checkout, exit 0:

```
Required test coverage of 96.0% reached. Total coverage: 96.53%
============================= 860 passed in 37.53s =============================
```

Ruff, mypy `--strict`, import-linter and the unfinished-work scan passed in the same run. The pre-commit hook ran the same
`make verify` and passed on each of the six commits.

---

_Fixed: 2026-10-11_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
