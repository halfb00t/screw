---
phase: 05-hex-nut-and-kernel-pair-proof
reviewed: 2026-10-21T00:00:00Z
depth: standard
files_reviewed: 65
files_reviewed_list:
  - .github/workflows/pair.yml
  - Makefile
  - bench/RESULTS.md
  - bench/end_cuts.py
  - bench/m18_probe.py
  - bench/mesh_deviation.py
  - bench/nut_fine_caps.py
  - bench/pair_expected.py
  - bench/thread_spike/maths.py
  - bench/thread_spike/pair.py
  - bench/thread_spike/verdict.py
  - docker/smoke.py
  - docs/architecture/decision_log.md
  - docs/architecture/overview.md
  - docs/ideas/2026-10-12-preview-stl-download-names-its-quality.md
  - docs/ideas/INDEX.md
  - docs/tech_debt/INDEX.md
  - docs/tech_debt/active/2026-10-14-first-pair-yml-dispatch.md
  - docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md
  - docs/tech_debt/active/2026-10-14-nut-interim-bounds.md
  - docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md
  - docs/tech_debt/active/2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md
  - docs/tech_debt/active/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md
  - docs/tech_debt/resolved/2026-10-14-nut-fine-stl-caps-unmeasured.md
  - pyproject.toml
  - src/screw/app.py
  - src/screw/calc/__init__.py
  - src/screw/calc/pair.py
  - src/screw/calc/presets.py
  - src/screw/calc/thread.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/solid/__init__.py
  - src/screw/solid/bolt.py
  - src/screw/solid/nut.py
  - src/screw/solid/pair.py
  - src/screw/static/app.js
  - src/screw/static/index.html
  - src/screw/static/style.css
  - src/screw/tables/__init__.py
  - src/screw/tables/gost16093.py
  - src/screw/tables/iso4014.py
  - src/screw/tables/iso4032.py
  - src/screw/tables/iso724.py
  - src/screw/tables/presets.py
  - src/screw/tables/rows.py
  - tests/conftest.py
  - tests/test_api.py
  - tests/test_bench.py
  - tests/test_calc.py
  - tests/test_cli.py
  - tests/test_cli_pair.py
  - tests/test_end_oracles.py
  - tests/test_grid.py
  - tests/test_import_boundaries.py
  - tests/test_mesh.py
  - tests/test_nut.py
  - tests/test_pair.py
  - tests/test_params.py
  - tests/test_parity.py
  - tests/test_presets.py
  - tests/test_solid.py
  - tests/test_tables.py
  - tests/test_tables_second_entry.py
  - tests/test_thread_maths.py
findings:
  critical: 0
  warning: 6
  info: 4
  total: 10
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-21
**Depth:** standard
**Files Reviewed:** 65
**Status:** issues_found

## Summary

Reviewed the nut solid, the end-cut oracles, the pair rule and the kernel pair proof, the nut fine-STL
cap, and the API, CLI and page wiring. I ran the nut builder at boundary inputs and the pair rule
with planted readings (scratch scripts under `scratchpad/review-05/`). Nothing was modified in `src/`.

The nut geometry holds up where it was fuzzed. About 25 nuts built at the countersink and chamfer
boundaries, small m, negative clearance and large clearance, and every one passed all piece gates.
The fine-STL cap table matches the committed records and is conservative at realistic clearances.
At M10 right, m 36, s 16, clearance 0.1 the total is 0.605 of the 64 MiB budget.

Defects found, no BLOCKER:

- **Nut builder:** a valid nut with across-flats below 1.73 mm is accepted by the model and the info
  document, then fails to build with an unactionable "Standard_Failure" 422 (WR-01).
- **Pair rule:** `cell_verdict` can return `proven` on a NaN control reading, although the module's
  own `volume_check` documents this exact trap (WR-02).
- **Pair report:** it prints a closed-form number nobody compared against and a negative "closed form"
  volume for large clearances (WR-03, WR-04). It reports `engagement_turns` as `p.m / p.pitch`, so
  `screw pair` and `screw info` can disagree on the same quantity (WR-05).
- **Shipped-solid evidence row:** it fails for every off-row nut with d >= 10 mm (WR-06).

The known, already-filed debt (huge-s lead-in gate, interim bounds, first `pair.yml` dispatch) is not
re-reported.

## Warnings

### WR-01: A valid nut with across-flats below 1.73 mm fails to build with an unactionable error

**File:** `src/screw/solid/nut.py:96-108` (the profile's first point is `(r0 - 0.5 / tan_beta, below)`)
**Issue:** `face_chamfer` starts its revolve profile `0.5 / tan(30 deg) = 0.866` mm inside the
inscribed radius `r0 = s / 2`. When `s / 2 < 0.866` mm, i.e. `s < 1.732`, that point has a negative
radius and the revolved polygon crosses the axis. The kernel raises `Standard_Failure: BRep_API:
command not done`.

The parameter model accepts the nut: `s > d + 2c` is the only floor, so a sub-2 mm nut is legal. The
info document answers 200 with a volume row and offers the download links. Only the build fails.

Reproduced (right-hand, d 1.0, pitch 0.25, m 1.0, clearance 0.05):

| s | Result |
|---|---|
| 1.5 | `BuildError: Geometry kernel failed (Standard_Failure); check d, pitch, left_hand, s, m and clearance.` |
| 1.7 | same failure |
| 1.74 | builds |
| 1.8 | builds |
| 2.0 | builds |

The user gets a 422 or CLI exit 1 that names every field and none in particular. Nothing in
`tests/test_nut.py` builds a nut below s = 2.

**Fix:** keep the cutter profile's radii positive. Clamp the overshoot below the face, for example:

```python
overshoot = min(0.5, 0.5 * r0 * tan_beta)      # r0 - overshoot / tan_beta stays >= r0 / 2 > 0
below = z_face - sign * overshoot
return _revolved([(r0 - overshoot / tan_beta, below), (outer, below),
                  (outer, flat), (r0 + depth / tan_beta, flat)])
```

Add a test that builds an s = 1.5 nut, `NutParams(d=1.0, pitch=0.25, s=1.5, m=1.0, clearance=0.05)`
(d is 1.0, so it is below s). If sub-1.73 mm nuts are meant to be refused instead, refuse them in the
model naming `s`, not in the kernel.

### WR-02: `cell_verdict` returns `proven` when a control reading, or the nut body, is NaN

**File:** `src/screw/calc/pair.py:190` and `:222` (`_off_by` at `:144-148`)
**Issue:** `abs(nut_volume / body - 1.0) > T_PASS` and `_off_by(r, closed) > PAIR_BAND` are positive
comparisons. Every comparison with NaN is False, so a NaN is treated as inside the tolerance.
`calc/thread.py` documents this trap in `volume_check` and `piece_refusal`: "written as a negated
`<=` ... the positive form would pass a NaN volume". The pair rule, the safety-relevant claim of this
phase, does not follow it.

Reproduced with the real rule on an M6 c 0.10 cell:

- Three empty matched poses plus three control readings with `volume=nan` and `solids=1`: `cell_verdict`
  returns `('proven', ())`.
- `nut_volume=nan` with otherwise perfect readings: also `('proven', ())`.

`_is_empty` has the mirror problem. A NaN matched volume reads as non-empty, so it flips toward
`violated`, which is the safe direction. The control path is the unsafe one. A NaN can reach this code
through a kernel `Mass()` on a degenerate boolean result, or through `json.loads`, which accepts
`NaN`, on the committed records.

**Fix:** write both checks as negated `<=` and treat a non-finite volume as "not believed":

```python
if not abs(nut_volume / body - 1.0) <= T_PASS:
    return "inconclusive", (...)
...
elif not _off_by(r, closed) <= PAIR_BAND:
    reasons.append(...)
```

Also reject a non-finite `volume` in `_off_by`. Add a test with a NaN control and a NaN nut volume.

### WR-03: `prove` prints a `closed_control` it never compared, against its own contract

**File:** `src/screw/solid/pair.py:299-303` (set before the cell runs) and the `PairReport` docstring at `:177-181`
**Issue:** The `PairReport` docstring says "`closed_control` is `None` where no control was read ... (L02: a
closed form nobody compared against is not printed)". But `closed = closed_control(cell)` is assigned
before `_record` runs. It is printed whenever the pair is same-hand and `clearance > 0`, whatever
happened next:

- When the cell fails (`outcome == "failure"`), no control is compared, and the report still prints a
  closed form next to `reasons=["cell failure: ..."]`. `test_a_failing_boolean_ends_the_cell_inconclusive`
  never asserts `closed_control`.
- When the nut body is off the closed form, `cell_verdict` returns before it ever reaches the control
  check. The report still prints the control's closed form (see WR-04).

**Fix:** set `closed` only when the verdict reached the control comparison. The simplest honest rule:
`closed = closed_control(cell) if (not mixed and verdict in ("proven", "violated")) else None`. For a
`violated` verdict the matched-pose reads end the cell before any control is compared. In that case
too the number is not used, so use `proven` only if the docstring is kept as written. Pin the chosen
rule in a test.

### WR-04: At clearance of about d/2 or more the proof prints a negative "closed form" volume as its reason

**File:** `src/screw/solid/pair.py:126-137` (`blank` uses a plain cylinder of radius d) and `src/screw/calc/pair.py:190-192`
**Issue:** The proof body is a cylinder of radius `d`, not the hex nut. The void's crest radius is
`d/2 + c`, so for `c >= d/2` the void leaves no wall in the blank. The nut itself is valid, because
`s > d + 2c` makes the hex wide enough. The CLI refuses only on the nominal rod's root radius
(`cmd_pair`), not on this.

Reproduced with `prove(NutParams(d=6, pitch=1, s=20, m=5.2, clearance=3.5), shipped=False)`. It returns
`inconclusive` with the reason:

> the nut body is 2.20739 mm3, not the closed form -39.6362 mm3 within 0.0001: no reading is believed

A negative closed-form volume is printed as if it were a measurement. The report also prints
`closed_control=0.0`. The R16 ruling admits clearances up to 5 mm on a 2 mm nut, so this is reachable
by a documented input.

**Fix:** in `prove`, refuse before the kernel when the proof body cannot exist, i.e. when
`_nut_body(cell) <= 0` or `d / 2 + c >= d`. Give a reason that names `d` and `clearance` ("the proof
body, a cylinder of radius d, is cut through by a void of radius d/2 + c"). Alternatively, build the
blank with radius `max(d, d/2 + c + d/4)` and update the closed form to match.

### WR-05: `engagement_turns` in the pair report is float division; `screw info` uses the exact quotient

**File:** `src/screw/solid/pair.py:313`
**Issue:** `engagement_turns=p.m / p.pitch` is plain float division. The info document deliberately
uses `turns_of(p.m, p.pitch)` for the same quantity: the exact decimal quotient. Its docstring gives
the failure case "5.4 / 0.6 reads 9.0, not 9.000000000000002".

For `m=5.4, pitch=0.6` I measured `5.4 / 0.6 = 9.000000000000002`. `screw pair` prints that and
`screw info` prints `9.0` for the same nut. This breaks the cross-front-end parity rule and the
"number someone will cut metal to" rule, for a purely cosmetic reason that the codebase has already
solved. `solid.pair` already imports from `screw.calc`, so `turns_of` is in reach.

**Fix:** `engagement_turns=turns_of(p.m, p.pitch)` (`from screw.calc.thread import turns_of`). Pin it
with a test at m 5.4, pitch 0.6.

### WR-06: The shipped-solid evidence row fails for any off-row nut with d >= 10 mm

**File:** `src/screw/solid/pair.py:240-250` (`_shipped` builds the bolt from `counterpart.fields`)
**Issue:** `counterpart_for` returns only `d`, `pitch` and `left_hand` for a nut that is not on an ISO
4017 row. `_shipped` then validates a `BoltParams` with the bolt's frozen default `s=10`. For d >= 10
that fails `head_too_small` (`s` must exceed `d`), and `except Exception` turns it into three
`failure` readings.

Reproduced with a fine-pitch M12 x 1.5 nut, `NutParams(d=12, pitch=1.5, s=19, m=10, clearance=.1)`:
the counterpart fields are `{'d': 12.0, 'pitch': 1.5, 'left_hand': False}`, and the bolt validation
fails with "s and d: the across-flats width s 10 mm must exceed the diameter d 12 mm".

The report is honest, since the error is recorded. But the evidence row, a stated deliverable
(D-05/D-06), silently cannot exist for any fine-pitch nut of M10 and above. `tests/test_pair.py` only
exercises M6 and M3, whose defaults happen to fit.

**Fix:** the nut's own `s` is always above `d` (`nut_too_thin`), so carry it:

```python
fields = {**counterpart.fields}
fields.setdefault("s", p.s)
bolt = build(BoltParams.model_validate({**fields, "left_hand": rod_hand, "length": length,
                                        "thread_length": length}))
```

Add a test with an off-row d >= 10 nut.

## Info

### IN-01: The countersink-factor comment misstates the smallest `da_max / d`

**File:** `src/screw/calc/thread.py:664-665`
**Issue:** The comment says "the smallest is 1.08, at M10 and M20". From the table in
`tables/iso4032.py`, M14 is `15.1 / 14 = 1.0786`, which is smaller than 1.08. The largest (1.16 at
M2,5) is right, and the model's 1.16 factor does not depend on the smallest, so no behaviour changes.
It is a comment that carries a number the next reader will trust.
**Fix:** "the smallest is 1.079, at M14".

### IN-02: A fillet ring can overhang the head's flats with no warning

**File:** `src/screw/solid/bolt.py:69-78` (`fillet_ring`) with `calc/thread.py:699-708` (`fillet_radius`)
**Issue:** `fillet_radius` is keyed on `(d, pitch)` alone, and `head_too_small` only requires `s > d`.
The ring's outer radius at the head underside is `d/2 + r`. For `s - d < 2r` the ring reaches past the
head's inscribed radius `s/2`.

Reproduced: `BoltParams(d=6, pitch=1, s=6.2, k=4, length=20, thread_length=10)`. `r = 0.25`, the ring
outer radius is 3.25, `s/2` is 3.1. It builds as one valid solid with the volume the oracle expects,
so no gate trips, and the info document says nothing. The solid is self-consistent but physically odd:
a fillet wider than the head it sits under.
**Fix:** either refuse the ring (cap and warn, naming `s`) when `d/2 + r > s/2`, as `end_depths` does
for the nut's countersink, or add the case to the standing "ends modelled" warnings.

### IN-03: `screw pair` exit codes collide with the exit codes of failures

**File:** `src/screw/cli.py:186` and `:209`
**Issue:** `PAIR_EXIT` maps `violated` to 1 and `inconclusive` to 2. Exit 2 is also what every refused
parameter returns, with empty stdout. Exit 1 is also what Python returns after an uncaught exception.
`cmd_pair` has no handler around `prove`; `closed_control(cell)` runs outside `_record`'s
`try/except`, for instance. A script that branches on `$?` reads a crashed proof as "violated" and a
refused parameter as "inconclusive". The tests pin the 0/1/2 mapping for verdicts, but not the
collision.
**Fix:** document that the JSON on stdout is the discriminator (non-empty means a verdict), or give
verdicts distinct codes and let crashes keep 1. Wrapping `prove` and exiting with a code outside
{0, 1, 2} on an unexpected exception is cheap.

### IN-04: Brittle or low-value tests in the pair and CLI suites

**File:** `tests/test_pair.py:726`, `tests/test_pair.py:493-496`, `tests/test_cli_pair.py:41`
**Issue:**
- `test_the_shipped_row_is_called_evidence_in_the_docstring` asserts that the word "evidence" occurs
  in `prove.__doc__`. That pins prose, not behaviour; the behaviour (the shipped row never changes the
  verdict) is already covered by the "planted non-empty shipped reading" test.
- The orchestration tests replace `solid_pair.rod_piece`, `solid_pair.blank` and `solid_pair.build` by
  `monkeypatch`. The kernel cannot run `common` in-process, so a seam is justified, but these couple
  the tests to the module's internal names. A rename silently passes if the fixture's lambda is kept.
- `test_a_nut_too_thin_for_its_void_exits_2_...` asserts a 5 s wall-clock bound. Under
  `pytest -n 8` on a loaded runner that can flake, and the property it guards (no kernel import) is
  already covered by `test_a_refusal_leaves_the_kernel_out_of_the_process`.
**Fix:** drop the docstring test, keep the seam but pass `rod`/`blank` through `prove`'s parameters if
a seam is wanted, and drop the timing assertion.

---

_Reviewed: 2026-10-21_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
