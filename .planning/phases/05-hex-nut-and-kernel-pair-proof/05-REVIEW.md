---
phase: 05-hex-nut-and-kernel-pair-proof
reviewed: 2026-10-21T00:00:00Z
rereviewed: 2026-10-21
rereview_base: e30b919
rereview_base_previous: ad09d46
depth: standard
files_reviewed: 70
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
  - docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md
  - docs/ideas/INDEX.md
  - docs/tech_debt/INDEX.md
  - docs/tech_debt/active/2026-10-14-first-pair-yml-dispatch.md
  - docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md
  - docs/tech_debt/active/2026-10-14-nut-interim-bounds.md
  - docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md
  - docs/tech_debt/active/2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md
  - docs/tech_debt/active/2026-10-21-brittle-pair-and-cli-tests.md
  - docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md
  - docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md
  - docs/tech_debt/active/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md
  - docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md
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
  warning: 1
  info: 1
  total: 2
findings_at_e30b919:
  critical: 0
  warning: 2
  info: 3
  total: 5
findings_initial:
  critical: 0
  warning: 6
  info: 4
  total: 10
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-21
**Re-reviewed:** 2026-10-21 (diff base ad09d46, after plans 05-20, 05-21, 05-22); 2026-10-21 again (diff base e30b919, after plan 05-23)
**Depth:** standard
**Files Reviewed:** 70
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

**Re-review verdict (2026-10-21).** All six warnings and IN-01 are closed by plan 05-20, each by the
fix the finding asked for, and none introduced a regression I could find. IN-02 to IN-04 are filed
as debt with the owner's sign-off. Plans 05-21 and 05-22 (page only) add two new warnings, both in
`app.js`: the typed-clearance memory is written under the wrong kind during a kind switch (WR-07), and
it outlives the field it describes after Reset or a link (WR-08). Three smaller items follow
(IN-05 to IN-07). No critical issue. Evidence I ran: `pytest tests/test_parity.py tests/test_pair.py
tests/test_end_oracles.py tests/test_cli_pair.py` gave 326 passed, 240 deselected (the deselected are
the `grid` and `pair` marked tests the default config skips, never part of `make verify`); `node --check` on `app.js` parses; 52 real-kernel
nut builds (s 1.11 to 3.5, both hands, d 0.5 and 1.0) all one valid solid; 60 off-row nuts at d 10 to
200 produce a valid evidence `BoltParams`.

**Second re-review verdict (2026-10-21, plan 05-23, diff base e30b919, commits 53cd338 and 58bbc9f).**
05-23 resolves WR-07, WR-08, IN-05 and IN-06 as findings, each by the fix asked for, with the
owner's two choices on top (the `update()` guard and the `navigate` rebuild). I found no regression in
the WR-07 and WR-08 paths. One new warning (WR-09): the old kind's preset picker stays live, and
unguarded, for the whole kind-switch window, so a pick there throws a `TypeError` and writes the old
kind's row into the new kind's controls. That contradicts the plan's own truth "no page error during
the kind-switch window". Open now: WR-09 and IN-07 (IN-07 is in `tests/test_nut.py`, outside this
delta, unchanged). No critical issue. Evidence I ran: `node --check src/screw/static/app.js` parses;
`pytest tests/test_parity.py -n0 --no-cov` gave 71 passed (not `make verify`, which I did not run);
two headless-Chromium probes against `screw serve` (spur's Playwright, scripts in the session
scratchpad, not in the repo), whose results are quoted under each finding.

## Warnings

### WR-01: A valid nut with across-flats below 1.73 mm fails to build with an unactionable error

**Status after 05-20: fixed in 4edaf3e.** `face_chamfer` now overshoots by `min(0.5, r0 * tan_beta / 2)`,
so the first profile radius stays at `s / 4` or more. Verified: 52 real-kernel builds (s 1.11, 1.2, 1.5,
1.7, 1.7320508, 1.74, 2.0, 2.5, 3.0, 3.4, 3.46, 3.47, 3.5; d 1.0 and 0.5; both hands; m 0.3 to 2) all
gave one valid solid. The same class of defect remains for the countersink cutter at a coarse pitch,
filed as debt (`docs/tech_debt/active/2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md`).

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

**Status after 05-20: fixed in fcdc0ab.** Both comparisons are negated `<=` in `cell_judgement`
(`calc/pair.py`), and `prove` refuses a non-finite volume at the three places it reads one
(`_finite` in `solid/pair.py`: the blank, each boolean, each evidence pose). Tests cover NaN, inf and
-inf for the body and for each of the three controls; a planted matched NaN stays `violated` as the
02-SPIKE rule is written (a NaN is not empty), which the docstring and a test pin.

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

**Status after 05-20: fixed in 4aa0126.** `cell_judgement` returns `(verdict, reasons, closed)` with
`closed` set only where the rule reached the controls (a proven cell, an empty or off-band control, a
control that cannot fire) and `None` where it ended first; `cell_verdict` is a two-element wrapper.
`prove` prints that third element. Nine parametrized cases pin the rule, and an orchestration test
pins the failure, violation and empty-control reports. The choice made differs slightly from the
suggested one-liner (it also prints the form for an empty or out-of-band control, because the reasons
quote it), and the `PairReport` docstring was rewritten to match.

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

**Status after 05-20: fixed in 0db1b73.** `prove` now has a `c >= d / 2` branch, the R8 shape: it reads
nothing, calls no `common`, is `inconclusive` by definition, and the reason names `d and clearance`
and prints no closed form. The blank is not grown (D-05); the argument that the verdict could not
change is sound (c >= d/2 exceeds the thread depth 5H/8 for any nut the CLI accepts, so the control's
closed form is 0). A kernel-free test shows the nut-body form is positive at `nextafter(d/2, 0)` for
every ISO 262 coarse size, and a CLI test pins exit 2 with the reason.

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

**Status after 05-20: fixed in 946e730.** `engagement_turns=turns_of(p.m, p.pitch)`. The new test runs
m 5.4, pitch 0.6 and asserts the report equals both `9.0` and the info document's row.

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

**Status after 05-20: fixed in 83e5b77.** `_shipped` does `fields.setdefault("s", p.s)`. Verified:
60 off-row nuts (d 10 to 200, fine pitches, c 0.05 to 2.0, s = d + 2c + 0.01) all produce a valid
`BoltParams`; the new real-kernel test builds the M12 x 1.5 case through `build` and reads three
`built` poses. The comment's claim that ISO 4017 and ISO 4032 print the same `s` at the 14 shared sizes
holds against the tables (checked: no difference). The "neither s nor k enters a reading" argument
(nut top at the highest matched pose lies below the head) is pinned kernel-free for every ISO 262
coarse size and holds for any pitch, because the tip cone length is a constant 0.5413 P.

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

### WR-07: The typed-clearance memory is written under the wrong kind while the page switches kinds

**Status after 05-23: resolved (53cd338).** `formKind` is declared at `app.js:17`, set at `:100`
directly after `clearForm()` (`:99`) with no `await` between that and the end of `buildForm`
(the function has one `await` pair, both before `:99`), and cleared in `clearForm` (`:81`).
`rememberTyped` returns while `formKind === null` and keys both the read and the write by `formKind`
(`:702-707`); `currentKind` no longer appears in it. The owner's two additions hold in the source:
`update()` returns at `:504` (its first statement) while `formKind !== currentKind`, and `navigate`
rebuilds on `kind !== currentKind || kind !== formKind` (`:315`). Probe, run by me: switch the Kind
select to `nut` with `api/presets?kind=nut` held 1.5 s, type clearance 0.1 in the window. The hash read
`#kind=nut`, no request contained `clearance`, no page error. After the load the finished navigation
wrote the link's empty clearance over the typing (`:340`, field `''`, unchanged behaviour, and
`forgetUntyped` then drops the entry). Typing 0.2 after the load gave the nut's `Matching bolt` link
`#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`. The Back case (the `navigate` rebuild) I verified by
reading `:315-331` only; the plan's own probe record is in 05-23-SUMMARY.md and I did not re-run it.
Original finding follows.

**File:** `src/screw/static/app.js:678-686` (`rememberTyped` and the `input` listener), with `currentKind` assigned only at `:315`
**Issue:** `rememberTyped` keys the memory by `currentKind`. In `navigate()` the new kind's form is
built first (`buildForm`, `:308`, which replaces the fields and `defaults` synchronously) and
`currentKind = kind` is assigned only after `await loadPresets(kind)` (`:310`, `:315`), a network round
trip. For that whole window the screen shows the new kind's form while `currentKind` still names the
old kind (or is `null` on first load and after a refused link). An `input` event in the window runs
`rememberTyped` with the new form's `input.name` and `defaults`, and writes under the old key.

Trace, bolt to nut: the user switches the Kind select to `nut` and types a clearance at once.
`defaults.clearance` is `undefined`, so the guard at `:679` passes, and the value is stored by
`lastTyped.set('bolt', { clearance: '0.1' })`. Two consequences:

- The nut's memory misses the value, so a later bolt's `Matching nut` link opens the nut empty although
  the user typed a clearance (the case 05-22 exists to fix).
- On the nut page, `Matching bolt` is built from `lastTyped.get('bolt')`, which now holds `clearance`.
  The link becomes `#kind=bolt&clearance=0.1&...`, and `navigate()` refuses it with `Unknown field
  "clearance" for kind "bolt"` (`:318-323`). Nothing clears that entry for the rest of the page session,
  because every bolt field has a default and so never writes the memory.

The window is one request on localhost, so it is narrow, but the failure is persistent once hit and
nothing in the gate can observe it (see IN-05). I read this from the code; I did not run a browser.

**Fix:** key by the kind the form was built for, not by the kind of the last finished navigation.
Set a `formKind` in `buildForm` next to `defaults`, in the same synchronous block, and use it:

```js
let formKind = null; // the kind of the controls on screen; set where the controls are built
// buildForm(), after clearForm():  formKind = kind;
// clearForm():                     formKind = null;
function rememberTyped(input) {
  if (formKind === null || defaults[input.name] !== undefined) return;
  const typed = { ...lastTyped.get(formKind) };
  ...
  lastTyped.set(formKind, typed);
}
```

Add a source pin that `lastTyped.set(` is keyed by `formKind`, not `currentKind`.

### WR-08: The remembered clearance outlives the field after Reset or a link, so the Matching nut link carries a number the nut no longer shows

**Status after 05-23: resolved (58bbc9f).** `forgetUntyped(input)` (`app.js:709-714`) reads
`lastTyped.get(formKind)` and deletes an entry whose control now reads differently. It has two call
sites: `navigate` at `:341`, directly after the write loop (`:340`) and before the unreadable-value
refusal (`:346-352`) can return, and the Reset handler at `:729`, directly after its write loop. It only
deletes (`lastTyped.set(` still occurs once, in `rememberTyped`), so typing stays the one writer. Probes,
run by me: (1) type 0.2 on a nut, Reset, switch the Kind select to the bolt: its `Matching nut` link is
`#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2`, no clearance. (2) Type 0.3, follow `Matching bolt`,
then `Matching nut`: the nut opens at 0.3 and the link keeps it (the round trip). (3) Open
`#kind=nut&clearance=0.4`, then the bolt: its `Matching nut` link carries no clearance. Two properties
to know, neither a defect: the comparison is by string, so an external link that spells the same number
differently (`0.10` for a typed `0.1`) drops the entry, which errs toward carrying nothing; and a Kind
select round trip nut, bolt, nut writes the empty hash value into the clearance and so forgets it,
where the `Matching` link keeps it, as the amendment says ("the kind selector"). Original finding
follows.

**File:** `src/screw/static/app.js:698-701` (Reset), `:325` (`navigate` writes every control), `:428` (`showCounterpart`); comment at `:675-677`
**Issue:** The code comment says "Typing a field empty forgets it, so a link never carries an empty
or stale number", and the plan's truth is "never an empty or stale number". Only an `input` event
touches the memory. Reset writes `defaults[name]` (`undefined`, so empty) into the clearance control
without an event, and `navigate` writes the hash value into it without one. The memory keeps the old
number in both:

1. On a nut, type 0.1, press Reset. The field is empty and the nut does not build (R10). Switch to the
   bolt: `Matching nut` is `#kind=nut&clearance=0.1&...` and opens a nut at 0.1, a value the user
   cleared.
2. On a nut, type 0.1, then open a shared link or press Back to a nut at 0.3. The field shows 0.3, the
   memory holds 0.1, and the bolt's link carries 0.1.

Case 2 is the "typed means an input event" rule the plan states on purpose (05-22-PLAN.md line 472 and
the amendment). Case 1 is not named in the amendment, which says only that Reset "never writes" the
memory, and the owner's ruling was "last typed on a nut". The number is the user's own, so L02's
"plausible number" test does not fail, but a user who pressed Reset reads the cleared field as
forgotten, and the link contradicts it. It is the L02 failure shape the plan's threat T-05-64 names.

**Fix:** make Reset forget what it empties, which keeps "typed" literal and the owner's ruling intact
(the field is empty, so there is nothing to carry), and drop an entry a link overwrote with a different
value:

```js
function forgetUntyped(name, written) {          // write() for a field with no default
  const typed = lastTyped.get(formKind);
  if (typed && name in typed && String(written ?? '') !== typed[name]) delete typed[name];
}
// Reset handler and navigate's write loop: call it for each field with defaults[name] === undefined.
```

If the owner prefers "the clearance the nut last held", the plan already records that as a one-line
move of the writer into `update()`; surface it in the amendment either way.

### WR-09: The old kind's preset picker stays live during a kind switch, and a pick there throws and writes the old kind's row into the new kind's controls

**Status: new, open (re-review of 05-23).**

**File:** `src/screw/static/app.js:234` (`pick`, `write(fields.get(name).input, value)`), with the stale
picker kept by `:315-331` (`navigate`, `buildForm` at `:99`) and cleared only by `clearPicker` (`:84`,
called from `refuseLink`, `:278`); pinned as source text at `tests/test_parity.py:656`
**Issue:** `buildForm` replaces the controls and `formKind` at once, but the picker and `catalogue`
stay the old kind's until `loadPresets` lands (`:325`). In that window `pick(i)` takes a row of the old
catalogue and writes each of its fields into `fields.get(name)`, and the new form lacks some of them.
Bolt rows carry `d, pitch, length, s, k, thread_length`; the nut form has `d, pitch, left_hand, m,
clearance, s`. The loop writes `d` and `pitch`, then throws on `length`. 05-23 closed the same window
for `update()` (the guard at `:504`) and for `rowOfFields` (`:210-211`) but not for `pick`, and this
is the "stale catalogue" cause IN-06 named.

Reproduced, run by me: bolt page loaded, Kind select to `nut` with `api/presets?kind=nut` held 1.5 s, then
the stale picker's Size select set to `M2.5`. Result: page error `Cannot read properties of undefined
(reading 'input')`, and the nut's controls read `d 2.5, pitch 0.45`, the bolt row's values, until the
finished navigation rewrote them (`:340`; after the load `d 6, pitch 1, s 10, m 5.2`). No request went to
the API (the `update()` guard holds), and the hash stayed `#kind=nut`. So the effect is a console
error and a few hundred milliseconds of the wrong numbers in the controls, not a wrong part or link.
It contradicts the 05-23 truth "no page error during the kind-switch window" and the SUMMARY's D4, whose
probe never touched the picker. Nothing in the gate can see it.

**Fix:** do not leave the old picker on screen when the form it filled goes. Smallest: call
`clearPicker()` in `navigate`'s rebuild block, next to `dropMesh()` (`:322`), so the selects are hidden and
`catalogue` is `null` (`showMatch` and the `pick` handlers then have nothing to act on), and `loadPresets`
rebuilds them. `clearPicker` also blanks the badge and `shownPreset`, which a kind switch means anyway.
Failing that, make `pick` return while `formKind !== currentKind`, and update the `write(fields.get(name)
.input, value)` pin at `tests/test_parity.py:656` only if the lookup itself changes. Add a source pin that
the rebuild block clears the picker before `await buildForm(kind)`.

## Info

### IN-01: The countersink-factor comment misstates the smallest `da_max / d`

**Status after 05-20: fixed in 4218e54.** The comment now says "the smallest is 1.079, at M14: 15.1 / 14",
the decision log carries an inline erratum, and `test_the_countersink_comment_cites_the_smallest_and_largest_da_over_d_of_the_table`
recomputes both extremes from `iso4032.NUTS` and reads them in the comment.

**File:** `src/screw/calc/thread.py:664-665`
**Issue:** The comment says "the smallest is 1.08, at M10 and M20". From the table in
`tables/iso4032.py`, M14 is `15.1 / 14 = 1.0786`, which is smaller than 1.08. The largest (1.16 at
M2,5) is right, and the model's 1.16 factor does not depend on the smallest, so no behaviour changes.
It is a comment that carries a number the next reader will trust.
**Fix:** "the smallest is 1.079, at M14".

### IN-02: A fillet ring can overhang the head's flats with no warning

**Status after 05-20: filed as debt** `docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md`
(severity must, indexed). The entry's arithmetic matches this finding. Note for the next reader: after
WR-06 the evidence bolt of an off-row nut takes the nut's own `s`, which can sit just above `d + 2c`, so
the evidence row can also build a bolt with an overhanging ring. It does not enter any reading.

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

**Status after 05-20: filed as debt** `docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md`
(severity must, indexed, flagged as an owner decision because D-06's codes are published). Plan 05-20's
new inconclusive-by-definition case (c >= d/2) still prints its JSON and exits 2, so the stdout
discriminator the entry relies on holds there too.

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

**Status after 05-20: filed as debt** `docs/tech_debt/active/2026-10-21-brittle-pair-and-cli-tests.md`
(severity nice, indexed). One claim in this finding is withdrawn: the second bullet said a rename
"silently passes". `monkeypatch.setattr` defaults to `raising=True`, so a rename fails the fixture
loudly; the cost is coupling, not a silent pass, as the debt entry corrects. The docstring test
(`test_the_shipped_row_is_called_evidence_in_the_docstring`) is still in `tests/test_pair.py`.

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

## Re-review after 05-20, 05-21, 05-22 (diff base ad09d46)

Scope: `git diff ad09d46..HEAD` over `src/screw/static/app.js`, `src/screw/calc/{pair,thread}.py`,
`src/screw/solid/{nut,pair}.py`, the five touched test files, the decision log, the idea entry and the
four debt entries. Checked against 05-20, 05-21 and 05-22 PLAN must-haves and threat models and the
L02 rules.

**05-20.** Each fix closes its finding (statuses are on the findings above) and I found no
regression. Points I checked specifically: the negated `<=` does not turn a legitimate inconclusive
into a different verdict (the written rule's clause order is intact, and the 240-cell expected table
re-derives byte-identically per the decision log); `_finite` raises inside `_record`'s `try`, so a NaN
body or boolean ends the cell as a recorded `failure` with the readings taken so far; the new `c >= d/2`
branch sits after `c <= 0` and before the mixed-hand split, so it covers both pairings; the overshoot
formula returns the old 0.5 mm exactly for `s >= 2 sqrt(3)` (a test pins `zmin == -0.5` at s 3.5, 4.0
and 10).

**05-21 (selects follow the fields after a failed update).** `rowOfFields` is exact (`held !== ''`,
`Number(held) === value`, no `Math.`), matches the server rule and order (`calc.presets.match` and
`match_nut` compare row fields only, `left_hand` and `clearance` excluded, as the page does), is
reachable only with a null preset, and a successful info document always carries a preset member
(`app.py:307`, `:311`, `:413`, `:417`), so a successful part cannot take this branch. The badge
branch is unchanged and stays empty after a failure. A failed update that does not touch the row
fields (the nut's missing clearance) now keeps the pick, which is the G-05-1 claim. No finding beyond
IN-06.

**05-22 (matching nut link carries the clearance last typed).** Checked: the server's fields are spread
last, so a remembered value cannot override `d`, `pitch`, `s`, `m` or the hand; only fields with no
default are remembered (`defaults[input.name] !== undefined` returns); `URLSearchParams` encodes keys
and values and a number control returns a valid float or empty, so there is no link injection; nothing
is persisted (no `localStorage`, `sessionStorage` or `document.cookie`); `lastTyped` is read only in
`showCounterpart`; `PartInfo.counterpart` still never carries `clearance`; a stale mesh is still
dropped on a kind change. Two defects found in how the memory is keyed and cleared (WR-07, WR-08).

### IN-05: The new page tests pin source text, so the claims they name are not exercised, and two of the pins are fragile

**Status after 05-23: resolved for the fixes the finding asked for (53cd338); the browser-run gap stays
with the owner's idea entry.** Done: the call count is `re.findall(r"(?<!function )rowOfFields\(", APP_JS)
== ["rowOfFields("]` (`tests/test_parity.py:705-707`); the `remember` pin is `delete typed[input.name]`
exactly, `lastTyped.get(formKind)` and `lastTyped.set(formKind, typed)`, with `currentKind` asserted
absent (`:896-903`); the no-reader loop now includes `showMatch`, `buildForm` and `write` (`:908-910`).
Two new tests pin the `formKind` set and clear and the `update()` guard as its first statement
(`:915-930`) and the `forgetUntyped` call sites (`:932-950`). 71 pass. Two remarks. The test comment at
`:705-706` says the pattern means "a comment that names the function cannot hide a second call", which is
not what it does: the regex still matches `rowOfFields(` inside a comment (I appended
`// see rowOfFields() for why` to a copy of `app.js` and it returned two matches), so a comment naming
the call still fails the gate; it now also catches a call with arguments, which the old
`count("rowOfFields()")` missed. The comment is inaccurate, the gate is no worse. And the spread-order
and anonymous-handler bullets are unchanged: the Reset and Kind-select handlers cannot be named, and
`:874` pins the spread order as source text.

**File:** `tests/test_parity.py:687-708` (`test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly`), `:884-905` (`test_the_matching_link_carries_only_a_value_typed_in_this_page_into_a_field_with_no_default`)
**Issue:** The G-05-1 and G-05-3 tests assert that substrings occur in `app.js`. None runs the page,
so none would catch the two defects above, a wrong spread order that still contains the pinned
substring, or a regression of the UAT symptom itself. The owner already holds the underlying decision
(a browser test in the gate, `docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md`), so the
gap is known; the following are separate and cheap:

- `assert APP_JS.count("rowOfFields()") == 2` counts every occurrence including comments and
  docstrings, so a comment that writes `rowOfFields()` fails the gate for no behavioural reason.
- `assert "delete " in remember` is satisfied by any `delete`, including one on the wrong object.
- The "no reader" loop covers eight named functions but not `showMatch`, `buildForm` or `write`, and
  the Reset and kind-select handlers are anonymous so cannot be named at all.
- `test_a_bolts_matching_nut_link_with_a_typed_clearance_opens_a_nut_that_builds` composes the link in
  Python (`{**fields, "clearance": "0.1"}`). It is the honest server half, and it cannot show that the
  page orders the spread so the server's fields win.

**Fix:** until the owner decides on a browser test, count `rowOfFields(` calls with the definition
excluded by pattern (`re.findall(r"(?<!function )rowOfFields\(", ...)`), pin `delete typed[input.name]`
exactly, and add `lastTyped.set(formKind, typed)` to the pin when WR-07 is fixed. If the owner takes
option (a) of the idea entry, the Reset, back-navigation and kind-switch cases in WR-07 and WR-08 are
the first three tests.

### IN-06: `rowOfFields` dereferences `fields.get(name)` unguarded while the catalogue can belong to the previous kind

**Status after 05-23: resolved for `rowOfFields` (53cd338); the cause it names is only half removed, see
WR-09.** `rowOfFields` now reads `const control = fields.get(name); if (control === undefined) return
false;` (`app.js:210-211`), pinned at `tests/test_parity.py:694-698`. The trigger the finding traced, a
failed update in the window, can no longer happen: `update()` returns first (`:504`). The finding's
"better" fix (clear `catalogue` and the picker where the form is replaced) was not made, and the same
stale catalogue is still reachable through `pick()`, which has the same unguarded lookup (`:234`). Original
finding follows.

**File:** `src/screw/static/app.js:199-204` (`rowOfFields`), with the stale window at `:304-316`
**Issue:** On a kind change `navigate()` rebuilds the form (`buildForm`) but leaves `catalogue`
holding the old kind's rows until `loadPresets` resolves; `clearPicker` runs only from `refuseLink`.
`rowOfFields` calls `read(fields.get(name).input)` for every field of every old-kind row. If an update
fails in that window (an `input` event before `currentKind` is set queues one, and it fetches the old
kind's route with the new form's fields, so it answers a 422), `showMatch(null)` runs, and a bolt row
field the nut form lacks (`k`, say) makes `fields.get('k')` `undefined`: a `TypeError` thrown inside
`fail`, which is itself inside `update`'s `try`, so the `catch` calls `fail` again and the rejection
escapes `update()` to the timer. Before 05-21, `showMatch(null)` only blanked the selects and could not
throw here. The effect is a console error, not a wrong part, because the next navigation's `update`
replaces the state; it is the same window as WR-07 and the same fix removes the cause.

**Fix:** guard the lookup, and treat a missing control as "does not hold the row":

```js
const control = fields.get(name);
if (control === undefined) return false;
const held = read(control.input);
```

Better, clear `catalogue` and the picker where the form is replaced, so the two are never out of step.

### IN-07: The nut narrow-s tests do not cover the band where the chamfer overshoot changed from 0.5 mm

**Status: new, open.**

**File:** `tests/test_nut.py:510-536`
**Issue:** The overshoot is `min(0.5, r0 * tan 30 / 2)`, which is 0.5 mm for `s >= 2 sqrt(3) = 3.4641`
and smaller below it. The build tests use s 1.11, 1.5 and 1.7 (all below `sqrt(3) = 1.732`, where the
old code failed), and the "unchanged" test uses s 3.5, 4.0 and 10. Nothing builds a nut in
`1.732 <= s < 3.464`, the band where the cutter changed (overshoot 0.43 to 0.5 mm) although the old
code built there. I built s 1.74, 2.0, 2.5, 3.0, 3.4, 3.46 and 3.47 in the scratch run, both hands in
the sampled set, and all pass, so no defect; but the band is the only place a shipped build's cutter
differs from its pre-05-20 shape and no test says it still passes its piece gate.
**Fix:** add `2.0, 2.5, 3.4` to `test_a_narrow_nut_below_root_three_across_flats_builds_inside_the_gate`'s
`s` parameters (the name then should say "narrow", not "below root three"), and assert the cutter's
`zmin` equals `-min(0.5, s / 2 * tan30 / 2)` at 3.4 and 3.5 so the cap's switch point is pinned.

## Re-review after 05-23 (diff base e30b919)

Scope: `git diff e30b919 HEAD` over `src/screw/static/app.js`, `tests/test_parity.py` and
`docs/architecture/decision_log.md` (commits 53cd338 and 58bbc9f; 126 insertions, 19 deletions across the
three). The whole of `app.js` was read for context. Checked against 05-23-PLAN.md's truths and the L02
rules.

**WR-07: resolved. WR-08: resolved. IN-05: resolved (the asked-for fixes). IN-06: resolved (the guard).**
Evidence is under each finding. Points I traced that found no defect: (a) `navigate`'s rebuild condition
can never skip a form that is not the link's kind, because `formKind !== currentKind` and
`kind === currentKind` and `kind === formKind` cannot all hold, so no overtaken navigation leaves the
`update()` guard closed; the one remaining way to a closed guard is an overtaking navigation whose schema
fetch throws, which shows "Could not load the part" and leaves the nut form with no updates, an error
path and no longer a silent wrong request; (b) `forgetUntyped` runs only after `buildForm` has set
`formKind` to `kind`, and the one `await` between (`loadPresets`) is guarded by `formSeq`, so
`lastTyped.get(formKind)` is the entry of the form being written; (c) `forgetUntyped` runs before
`navigate`'s unreadable-value refusal, so a refused link still forgets; (d) `rememberTyped` copies the
entry and `showCounterpart` spreads it, so `forgetUntyped`'s in-place delete cannot alias a link already
built; (e) the picker is outside `#params` (`index.html:20`, `:23`), so a picker `input` event never
reaches `rememberTyped`; (f) the decision log amendment's description of the code (the rebuild
condition, the guard, `forgetUntyped`, the two new tests) matches the source. Two behaviours worth
knowing and not findings: typing into a field in the kind-switch window is overwritten by the finished
navigation and forgotten (as before 05-23, now consistent between field and memory), and
`update()`'s early return does not clear the debounce a window keystroke queued, so a duplicate
update runs after the load and aborts the first (pre-existing, harmless).

**New:** WR-09. IN-07 is untouched by this delta and stays open.

---

_Reviewed: 2026-10-21_
_Re-reviewed: 2026-10-21 (base ad09d46)_
_Re-reviewed: 2026-10-21 (base e30b919, plan 05-23)_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
