---
phase: 05-hex-nut-and-kernel-pair-proof
verified: 2026-10-22T09:00:00Z
status: human_needed
score: 37/37 must-haves verified
covered_files:
  - .github/workflows/pair.yml
  - .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-01-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-01-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-02-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-02-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-03-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-03-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-04-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-04-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-05-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-05-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-06-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-06-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-07-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-07-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-08-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-08-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-09-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-09-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-10-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-10-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-11-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-11-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-12-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-12-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-13-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-13-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-14-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-14-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-15-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-15-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-16-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-16-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-17-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-17-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-18-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-18-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-19-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-19-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-20-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-20-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-21-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-21-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-22-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-22-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-23-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-23-SUMMARY.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-24-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-24-SUMMARY.md
  - Makefile
  - bench/RESULTS.md
  - docs/architecture/decision_log.md
  - pyproject.toml
  - src/screw/app.py
  - src/screw/calc/__init__.py
  - src/screw/calc/pair.py
  - src/screw/calc/presets.py
  - src/screw/cli.py
  - src/screw/params.py
  - src/screw/solid/__init__.py
  - src/screw/solid/bolt.py
  - src/screw/solid/nut.py
  - src/screw/solid/pair.py
  - src/screw/static/app.js
  - src/screw/static/index.html
  - src/screw/tables/gost16093.py
  - src/screw/tables/iso4032.py
  - src/screw/tables/iso724.py
  - tests/data/pair_expected.tsv
  - tests/test_parity.py
covered_digest: "v3:sha256:4184668fc275f5c6d9e139db77626709fbcaed795067270c46f88c5c6236fb2f"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 28/29
  gaps_closed:
    - "WR-09 / 05-23 truth C4 ('IN-06: no page error during the kind-switch window'): navigate() now clears the old kind's form and picker directly after dropMesh(), before the new schema is fetched (63835c8). Reproduced closed in a headless browser on HEAD"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "UAT test 1 on the final build. `make serve`, kind nut, clearance empty, pick ISO 4032 then M6."
    expected: "The selects hold ISO 4032 / M6, the fields read M6 (d 6, pitch 1, s 10, m 5.2), nothing builds, the one error is the missing clearance."
    why_human: "The owner reported this as a failure (05-UAT.md test 1, G-05-1). The fix is verified by my headless run, but no human has re-run it, and browser behaviour is not in the gate (L01)."
  - test: "UAT test 3 on the final build. Type 0.1 on the nut, follow Matching bolt, then Matching nut. Also: type 0.1, Reset, switch to the bolt, and read its Matching nut link."
    expected: "The nut opens at 0.1 and builds. After Reset the bolt's Matching nut link carries no clearance."
    why_human: "The owner reported this as a failure (05-UAT.md test 3, G-05-3). My headless run agrees with the expected result; the owner's confirmation is the end-of-phase item."
  - test: "Throttled kind switch in a real browser (devtools network throttling), then Matching nut followed by Back."
    expected: "While the nut loads: no picker, no badge, no control of the old kind on screen, no console error. Back during the load reopens the bolt with its seven controls, picker ISO 4017 / M6 / 20 and badge."
    why_human: "The window is one localhost request long. My probes hold the request with a route handler, which is a faithful stand-in, but plan 05-24 names the real-browser run as the owner's end-of-phase item."
---

# Phase 5: Hex Nut and Kernel Pair Proof Verification Report

**Phase Goal:** For any bolt a user can get the matching ISO 4032 nut at a chosen radial clearance, see the pair's numbers on the info panel, and get a kernel verdict on whether the pair mates, one that cannot report `proven` when its own control did not fire.
**Verified:** 2026-10-22T09:00:00Z
**Status:** human_needed
**Re-verification:** Yes, after gap closure plan 05-24 (WR-09). HEAD bb13513.

## Verdict in one paragraph

The phase goal is achieved and 05-24 closed the one remaining gap. WR-09 (a pick in the old kind's picker during a
kind switch threw and wrote the old row into the new kind's controls) is gone: I re-ran the reproduction on HEAD and
the picker is hidden with no select, the nut's `d` and `pitch` stay empty, there is no page error, and only
`schema?kind=nut` is requested. No earlier truth regressed: the 05-23 probe passes all 17 steps unchanged, and my
own runs of UAT tests 1 and 3, Back during the schema fetch, and the kind switch both ways all read as the plan
says. The review's new WR-10 (a failed schema fetch leaves a blank form under the old part's panel) is real and I
reproduced it, but it is a failure-path recoverability defect that no must-have truth and no roadmap success
criterion names, and it prints no wrong number, so it is a recorded warning, not a gap. The status is
`human_needed`, not `passed`, only because the owner reported UAT tests 1 and 3 as failures and has not yet re-run
them on the final build; that confirmation is the end-of-phase item the plans themselves name.

## Decision on WR-09 (the gap under re-verification)

**Closed.** Evidence from the code and from a browser, not the SUMMARY.

- Source, `src/screw/static/app.js:331-333`: `dropMesh(); clearForm(); clearPicker(); if (!(await buildForm(kind))) return;`.
  `git diff 791e232 HEAD -- src tests` touches only `app.js` (14 lines) and `tests/test_parity.py` (28 lines).
  `clearForm` empties the form, `fields`, `defaults` and sets `formKind = null`; `clearPicker` hides `#picker`,
  empties `pickerSelects`, and nulls `catalogue`, `shownPreset` and the badge. From the first `await` until
  `buildForm` returns, `formKind` is `null` (so `update()` returns at line 504), `catalogue` is `null`, and no select
  exists, so `pick()` cannot run. The `rowOfFields` guard stays as a second line.
- Browser, my probe on HEAD (headless Chromium, `screw serve --port 8071`, scratch, not in the repo):
  - Nut catalogue held, Kind to nut: picker `{hidden: true, selects: 0, badge: ''}`, nut controls `d '', pitch ''`
    (before the fix they read the bolt row's values), hash `#kind=nut`, page errors `[]`, requests in the window
    `['schema?kind=nut']`. After the load: picker `ISO 4032 / M6`, badge empty, fields `d 6, pitch 1, s 10, m 5.2,
    clearance ''`, hash `#kind=nut`, no nut build, requests `schema, presets, nut/info`.
  - Nut schema held, then the Matching nut link and Back: window `{inputs: 0, hidden: true, selects: 0, badge: ''}`,
    no requests. Back reopened the bolt with names `d, pitch, length, left_hand, thread_length, s, k`, kind `bolt`,
    picker `ISO 4017 / M6 / 20`, badge `matches ISO 4017 M6 × 20`, `bolt/model.stl` `[200]`, no page error.
  - `probe_05_23.py` (the plan's own earlier probe, run unchanged against HEAD): 17 PASS lines, `RESULT PASS []`.
- Pin: `test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones` is in the 72 passed of
  `tests/test_parity.py` (my run: `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`, 72 passed).
- What I did not re-run: the BASE reproduction (the five FAIL steps in 05-24-SUMMARY.md). The prior report already
  reproduced the catalogue half at 791e232; the schema half at BASE rests on the SUMMARY and the planner's measurement.

## Decision on WR-10 (review finding, not a gap)

**Does WR-10 break any must-have truth or the goal? No.** I reproduced it; it is a warning.

- Reproduction (my run, `api/schema?kind=nut` answered 500 after a bolt loaded, Kind select to nut): `inputs: 0`,
  picker hidden, hash `#kind=nut`, message `Could not load the part: 500 Internal Server Error`, kind select reads
  `nut`, and the bolt's info panel (`Hexagon head screw ISO 4017 - M6 x 20`, its rows), a Matching nut link and two
  bolt download links (`api/bolt/model.stl?quality=fine`, `api/bolt/model.step?quality=fine`) stay. The review's
  account matches. The cause is `navigate()`'s unwrapped `await buildForm(kind)`: `clearForm()` has already run, and
  `.catch(reportLoadError)` only adds the message, whereas the `loadPresets` catch beside it calls `refuseLink`.
- Why not a gap. Every must-have I checked is about the working path: the nut at a chosen clearance, the pair rows,
  the verdict and its control, the matching-part link, and the kind-switch window while the server answers. Nothing
  names a schema-fetch failure. The 05-24 truths are worded about the loading window and Back, both of which hold.
  The L02 rule "a number the tool prints is a number someone will cut metal to" is not broken: the panel and the
  downloads are the bolt's own valid ones and the error is on screen. Before 05-24 the same stale panel stayed on
  screen with the old form usable, so the panel part predates this plan; what 05-24 changed is that the old form is
  now gone too.
- Residual cost. A recoverability regression on a server-error path: no controls until the user picks another kind
  or reloads (the review says re-picking `nut` fires no `change`; I recovered with a programmatic select that does
  fire one, so I did not independently confirm that sentence). It stays `open` in 05-REVIEW-DISPOSITION.md. I
  recommend a small plan (wrap `buildForm` as `loadPresets` is wrapped, plus a pin), but it need not block the phase.
  Not filed as tech debt by me: the review and its disposition already carry it. The owner may want a
  `docs/tech_debt/active/` item (severity must) if it is deferred past the phase.
- IN-08 (the WR-09 test pins source text, not behaviour): confirmed from the test body. It is the same class as
  IN-05, which the owner keeps as an open idea (a browser-level test); the behaviour is covered by the scratch
  probes. Not a gap.

## Goal Achievement

### Observable Truths

Roadmap success criteria SC1 to SC6 and the page truth (1 to 7), then 05-21 (A1 to A6), 05-22 (B1 to B7), 05-23
(C1 to C9) and the eight must-have truths of 05-24 (D1 to D8). C4 was FAILED in the prior report and is now VERIFIED.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: ISO 4032 nut M2-M20 from a preset or mm fields on API and CLI; matching part both ways from the same d, pitch, hand; lead-ins; parity green | VERIFIED | Kernel, calc, tables, API and CLI unchanged: `git diff 791e232 HEAD -- src tests` touches only `app.js` and `tests/test_parity.py`. 72 passed in `test_parity.py` (my run); the `TYPE-04` counterpart tests (20 selected) pass. Orchestrator: `make verify` at HEAD, 3466 passed, exit 0 |
| 2 | SC2: `clearance` is radial mm, positive enlarges the nut thread, no default; panel shows the INFO-01 set and the 6g/6H limits | VERIFIED | Unchanged. In the browser the nut with clearance empty issues no `nut/model.stl` and shows `Clearance (radial): Field required` |
| 3 | SC3: `proven \| violated \| inconclusive` with the control; an empty control is `inconclusive`, never `proven`; c <= 0 inconclusive; both hands; full grid pre-registered | VERIFIED | No file under `calc/pair.py`, `solid/pair.py`, `cli.py` changed since the report that ran the real kernel with planted readings. Evidence stands; not re-run |
| 4 | SC4: the pair proof is not an API endpoint; import-linter forbids `app` and `pool` importing it | VERIFIED | Unchanged files; part of `make verify` (orchestrator, exit 0) |
| 5 | SC5: STL and STEP from the same solid; chord deviation recorded; `ControlSurfaceDeflection` on | VERIFIED | Unchanged; in the green gate |
| 6 | SC6: the M18 empty control diagnosed in one bounded task; no verdict rule changed; M18 ships `inconclusive` | VERIFIED | Unchanged; owner UAT test 5 passed |
| 7 | The page: preset pick, empty clearance with no stale part, matching-part link, kind switch, pair rows, M18 note render and behave | VERIFIED | Owner UAT tests 2, 4, 5, 6 passed. Tests 1 and 3 re-run by me in a browser on HEAD (A1, B1). The owner's own re-run is the human item below |
| A1 | 05-21: empty clearance, ISO 4032 then M6 holds the selects, nothing builds | VERIFIED | My run: kind nut, then Standard ISO 4032 and Size M6 picked: selects `['ISO 4032','M6']`, fields `d 6, pitch 1, s 10, m 5.2, clearance ''`, no nut build. Also `probe_05_23.py` step `pick:` PASS |
| A2 | 05-21: after a failed update the selects show the first row the fields hold exactly, else blank | VERIFIED | `rowOfFields` (app.js:206-216), pinned and passing |
| A3 | 05-21: the badge reads only an info document | VERIFIED | Unchanged; the badge reads `matches ISO 4032 M6` once the nut is built at 0.1 (my run) |
| A4 | 05-21: a successful info document drives selects and badge from `info.preset` | VERIFIED | Same run: after the build at 0.1, picker `ISO 4032 / M6`, badge `matches ISO 4032 M6` |
| A5 | 05-21: diagnosis reproduced before the fix | VERIFIED | 05-21-SUMMARY (prior report) |
| A6 | 05-21: UI-SPEC amended; browser test idea filed | VERIFIED | unchanged |
| B1 | 05-22: type 0.1 on a nut, Matching bolt, Matching nut: the nut opens at 0.1 and builds | VERIFIED | My run: nut built `nut/model.stl?clearance=0.1` 200; Matching bolt link `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`; following both links back: hash `#kind=nut&clearance=0.1`, fields `d 6, pitch 1, s 10, m 5.2, clearance 0.1`, no page error. `probe_05_23.py` round-trip steps PASS |
| B2 | 05-22: with nothing typed the link is as before; typing empty forgets; nothing invented | VERIFIED | `probe_05_23.py` `cleared:` and `fresh page:` steps PASS |
| B3 | 05-22: the remembered value never reaches the bolt: not its hash, a bolt request, a download link | VERIFIED | `probe_05_23.py` window steps PASS (only `schema?kind=nut` requested, hash `#kind=nut`, nut's Matching bolt link carries no clearance, the bolt builds). My download-link read on the nut: `api/nut/model.stl?clearance=0.1&quality=fine` only |
| B4 | 05-22: `PartInfo.counterpart` never carries `clearance`; calc, app.py, cli.py unchanged | VERIFIED | `git diff` over `src/`: `app.js` only |
| B5 | 05-22: app.js names no field or kind; the server's fields win | VERIFIED | Naming tests in the 72 passed; `{ kind, ...lastTyped.get(counterpart.kind), ...counterpart.fields }` unchanged |
| B6 | 05-22: L15 amendment; UI-SPEC rule 37 | VERIFIED | present; `decision_log.md` unchanged since the prior report |
| B7 | 05-22: RED and GREEN in the SUMMARY | VERIFIED | prior report |
| C1 | 05-23 WR-07: a clearance typed while a kind switch loads is remembered under the kind of the form on screen | VERIFIED | `probe_05_23.py` window steps PASS, including the bolt's Matching nut carrying the clearance typed after load (0.2). Source: `formKind = kind` after `clearForm()` in `buildForm`, `rememberTyped` keyed by `formKind` |
| C2 | 05-23 window, owner choice (a): while `formKind !== currentKind` `update()` returns before the hash or a request | VERIFIED | app.js:504 first statement; the window shows only `schema?kind=nut` and hash `#kind=nut` (my run and the 05-23 probe) |
| C3 | 05-23 owner choice "fix in navigate": Back before the catalogue loads reopens the bolt with its own seven controls | VERIFIED | `probe_05_23.py` `back:` PASS (names, kind `bolt`, `bolt/model.stl` 200, no pageerror). Also my schema-held Back run |
| C4 | 05-23 IN-06: no page error during the kind-switch window. `rowOfFields` treats a catalogue row naming a field the form lacks as not held, and never throws | VERIFIED | Was FAILED (partial). Second sentence: guard at app.js:210-211, pinned. First sentence: with the nut catalogue held, no picker exists in the window, so no pick can run; page errors `[]` through the window and after the load (my run, and `probe_05_23.py` step `no page error while the kind switch loads (IN-06)` PASS). See WR-09 above |
| C5 | 05-23 WR-08: Reset, switch to bolt: Matching nut link has no clearance; a link that writes another value forgets 0.1 | VERIFIED | `probe_05_23.py` `reset:` and `link:` steps PASS |
| C6 | 05-23: the 05-22 round trip and the 05-21 pick are unchanged | VERIFIED | B1 and A1 above; `probe_05_23.py` 17/17 |
| C7 | 05-23: typing is the only writer; `lastTyped.set(` once; nothing persisted; calc, app.py, cli.py, index.html untouched | VERIFIED | Pins in the 72 passed; 05-24's diff adds no writer of `lastTyped` and no `formKind =` assignment |
| C8 | 05-23: L15 amendment and UI-SPEC rules in the code's commit | VERIFIED | unchanged; 05-24 did not edit L15 (its invariant held before and after) |
| C9 | 05-23: reproduced before the fix; RED, mid, GREEN outputs in the SUMMARY | VERIFIED | prior report |
| D1 | 05-24 WR-09: with the nut's catalogue held, once the nut's controls are on screen `#picker` is hidden with no select and the badge is empty; no page error; the nut's `d` and `pitch` stay empty | VERIFIED | My run on HEAD: `{hidden: true, selects: 0, badge: ''}`, `d '', pitch ''`, page errors `[]` |
| D2 | 05-24 schema half: with the nut's schema held, no control or picker of the bolt is on screen, nothing of the bolt is requested or built, the hash stays `#kind=nut` | VERIFIED | My run: `inputs 0`, picker `{hidden: true, selects: 0, badge: ''}`, hash `#kind=nut`, requests `[]`, page errors `[]`. No control exists to pick from. The BASE failure (bolt rebuilt, nut shown as last valid part) is the SUMMARY's, not re-run |
| D3 | 05-24: Back while the nut's schema loads reopens the bolt whole: seven controls, Kind bolt, picker `ISO 4017 / M6 / 20`, badge `matches ISO 4017 M6 × 20`, one `bolt/model.stl` 200, no page error | VERIFIED | My run, exactly those values |
| D4 | 05-24 edge probe (no catalogue): until `loadPresets` lands `catalogue` is null and `#picker` holds no select; after the load the nut's picker holds `ISO 4032 / M6` over the nut's defaults, badge empty, nothing builds | VERIFIED | My run (D1 window, then after load: `['ISO 4032','M6']`, `{d 6, pitch 1, s 10, m 5.2, clearance ''}`, `nut/info?` only, no nut model request). `showMatch` returns before reading a null catalogue (app.js, reviewer traced) |
| D5 | 05-24: the two clears break no truth of 05-21, 05-22 or 05-23; a kind switch both ways shows the kind's own picker and badge | VERIFIED | `probe_05_23.py` 17/17 on HEAD. My run: nut at 0.1 badge `matches ISO 4032 M6`; back on the bolt `matches ISO 4017 M6 × 20` |
| D6 | 05-24: `test_a_kind_change_clears_the_old_form_and_picker_before_it_fetches_the_new_ones` pins the order and the clear statements | VERIFIED | Test body read (tests/test_parity.py:998-1025), in the 72 passed. It proves order only (IN-08), not behaviour; behaviour is D1 to D5 |
| D7 | 05-24: UI-SPEC rules 30, 32, 36, dated note, Verification status, Extension rule 3 describe the built behaviour in the code's commit; L15 not edited | VERIFIED | `git show 63835c8` touches `01-UI-SPEC.md` (11 lines), `app.js`, `test_parity.py`; the diff carries the dated note, rules 30, 32, 36, the Verification-status bullet and Extension rule 3; `decision_log.md` not in the commit |
| D8 | 05-24: reproduced before the fix; WR-09 reads `fixed` with the fix sha in the disposition | VERIFIED | 05-24-SUMMARY.md lines 126-176 (RED five FAIL, GREEN `RESULT PASS []`); `05-REVIEW-DISPOSITION.md`: `WR-09 | warning | fixed | 63835c8 ...` |

**Score:** 37/37 truths verified (0 present, behavior-unverified).

### Prohibitions (05-24 and 05-23 `must_haves.prohibitions`)

| Prohibition | Tier | Status | Evidence |
|-------------|------|--------|----------|
| No writer of `lastTyped` other than `rememberTyped`; `forgetUntyped` only deletes | test | HELD | 05-24 adds no write; pins in the 72 passed |
| No change to calc, app.py, cli.py, index.html; `counterpart` keeps D-02's shape | test | HELD | `git diff 791e232 HEAD -- src tests` is `app.js` and `test_parity.py` only |
| No field or kind named in app.js, nothing persisted, no existing decision-log line edited | test | HELD | naming tests pass; `decision_log.md` not touched by 63835c8 |
| No `--no-verify`; `.planning/HANDOFF.json` and `.continue-here.md` not staged | judgment | HELD, NON-AUTHORITATIVE | `git status` shows both still untracked (with `.planning/ui-reviews/`). The commit hooks cannot be seen from the tree. Flagged for a human glance, not green |

### Deferred Items

None. WR-10 and IN-08 are not addressed by Phase 6 or later in the roadmap. PAIR-02 (the default clearance) is Phase 6
and is not claimed here.

### Advisory (New Scope, Unevidenced)

None. WR-10 is evidenced by a reproduction and recorded above as a warning.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/static/app.js` | navigate's rebuild block clears the old form and picker after `dropMesh`, before the schema fetch; the why comment; `rowOfFields` comment corrected | VERIFIED | lines 205-216 and 321-333; wired (executes on every kind change) |
| `tests/test_parity.py` | the WR-09 source pin | VERIFIED | lines 998-1025; 72 passed |
| `01-UI-SPEC.md` | rules 30, 32, 36, dated note, Verification status, Extension rule 3 | VERIFIED | in 63835c8's diff |
| `05-REVIEW-DISPOSITION.md` | WR-09 `fixed` with sha | VERIFIED | row present; WR-10 and IN-08 `open` |
| Phase 5 kernel, calc, tables, API, CLI | as in the prior reports | VERIFIED | unchanged since 791e232 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `navigate` | `clearForm`, `clearPicker` | `dropMesh(); clearForm(); clearPicker(); if (!(await buildForm(kind))) return;` | WIRED | app.js:330-333; pinned; observed in the window |
| `clearForm` | `update` guard | `formKind = null` so `update()` returns at app.js:504 | WIRED | window shows no request and no hash write |
| `clearForm` | navigate rebuild condition | `kind !== formKind` is true after an overtaking navigation | WIRED | Back during the schema fetch rebuilds the bolt (D3) |
| `clearPicker` | `showMatch` | `catalogue === null` makes `showMatch` return before reading it | WIRED | no pageerror anywhere in the window |
| `buildForm` throw | `refuseLink` / form restore | none | NOT WIRED (WR-10) | the failed-schema path ends in `reportLoadError` only, with the form cleared. Warning, outside the must-haves |
| old picker | `pick` | `select` `change` listener | CLOSED | the selects are removed from the DOM before the new form exists |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| Picker selects | `catalogue`, `rowOfFields()` | `GET /api/presets?kind=` and the form | yes; empty for the window instead of stale | FLOWING |
| Matching-part link | `lastTyped` + `info.counterpart` | the user's `input` events and the info document | yes, keyed by the form on screen | FLOWING |
| Nut info panel, `PairReport` | as the prior reports | unchanged | yes | FLOWING |
| Info panel, downloads after a schema failure | last info document | the old part | stale by design of the failure path (WR-10) | STATIC on that path only |

### Behavioral Spot-Checks

Scratch Playwright probes against `.venv/bin/screw serve` on ports 8071 and 8072 (spur's Playwright with the cached
headless shell), in `/private/tmp/claude-501/-Users-half-git-halfb00t-screw/b60a8896-f654-4a31-9a6a-bc185d8360cd/scratchpad/`
(`p.py`, `p23.py`), not in the repo (L01). Both servers are stopped.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| WR-09 catalogue half: kind switch, nut catalogue held | `p.py` | picker hidden, 0 selects, d/pitch empty, no pageerror, only `schema?kind=nut`, healed state after load | PASS |
| WR-09 schema half and Back during the schema fetch | `p.py` | 0 inputs, picker hidden, no requests; Back rebuilds the bolt (7 controls, picker, badge, stl 200) | PASS |
| UAT test 1: empty clearance, pick ISO 4032 then M6 | `p.py` | selects `['ISO 4032','M6']`, fields M6, no nut build | PASS |
| UAT test 3: 0.1, Matching bolt, Matching nut | `p.py` | `#kind=nut&clearance=0.1`, fields incl. clearance 0.1, no pageerror | PASS |
| 05-23 regression probe (17 steps) | `p23.py http://127.0.0.1:8072/` | 17 PASS, `RESULT PASS []` | PASS |
| WR-10: schema answered 500 on a kind switch | `p.py` | 0 inputs, bolt panel, bolt downloads and Matching link remain, error shown | CONFIRMED (warning) |
| Page source assertions | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` | 72 passed | PASS |
| TYPE-04 evidence tests | `make test PYTEST_ARGS="tests/test_calc.py tests/test_parity.py -q -n0 --no-cov -k 'following_a_bolts_counterpart or following_a_nuts_counterpart or same_counterpart or kind_change_clears'"` | 20 passed | PASS |
| Full gate | not re-run by me; orchestrator: `make verify` at HEAD bb13513, 3466 passed, exit 0 | accepted | PASS |

I did not re-run the real-kernel `screw pair` runs or the nut, mesh and presets suites: nothing under `calc/`, `solid/`,
`tables/`, `cli.py` or `app.py` changed since the reports that ran them.

### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared by the phase. SKIPPED.

### Requirements Coverage

Every ID in the phase list is claimed by at least one PLAN's `requirements:` frontmatter (grep of
`05-*-PLAN.md`; 05-18 claims all nine; 05-23 and 05-24 claim TYPE-04) and each maps to Phase 5 in REQUIREMENTS.md.
PAIR-02 maps to Phase 6 and no Phase 5 plan claims it. No orphans.

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| TYPE-03 | 05-02, 04, 05, 06, 07, 13, 18, 19, 20, 21 | SATISFIED | 14 cited rows; page picks hold with an empty clearance (A1) |
| TYPE-04 | 05-10, 05-18, 05-22, 05-23, 05-24 | SATISFIED | API and CLI both ways (`test_following_a_bolts_counterpart_gives_the_nut_row_of_its_size`, `test_following_a_nuts_counterpart_gives_a_bolt_with_the_nuts_d_pitch_and_hand`, `test_the_cli_and_the_api_print_the_same_counterpart`, all passing in my run); the page's round trip works (B1, C1). **The executor's `[x]` / Complete in REQUIREMENTS.md (lines 34 and 134) is confirmed by this evidence.** WR-09 and WR-10 do not touch the link |
| THRD-05 | 05-02, 11, 12, 13, 18, 20 | SATISFIED | unchanged |
| PAIR-01 | 05-04, 05, 09, 10, 18 | SATISFIED | unchanged |
| PAIR-03 | 05-01, 03, 05, 09, 14, 15, 16, 18, 20 | SATISFIED | unchanged; kernel evidence stands |
| PAIR-04 | 05-01, 03, 14, 15, 16, 18, 20 | SATISFIED | unchanged; first ubuntu grid run is filed debt |
| INFO-01 | 05-02, 06, 07, 08, 09, 18 | SATISFIED | unchanged |
| INFO-02 | 05-02, 08, 09, 18 | SATISFIED | unchanged |
| FRNT-06 | 05-02, 17, 18 | SATISFIED | unchanged |

REQUIREMENTS.md currently reads `[x]` / Complete for TYPE-04 only; the other eight rows (THRD-05, PAIR-01, PAIR-03,
PAIR-04, TYPE-03, INFO-01, INFO-02, FRNT-06) still read `Gaps Found` (lines 124-152). All nine are SATISFIED on
the evidence above, so TYPE-04's early tick is not contradicted, but the table is inconsistent until the other eight
move to Complete. That edit belongs to the orchestrator once the owner confirms the human items.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/screw/static/app.js` | 331-333 | `await buildForm(kind)` unwrapped after `clearForm()`; a schema failure leaves a blank form under the old part's panel | Warning (WR-10, open) | server-error path only; no wrong number; recovery by choosing another kind or reloading |
| `tests/test_parity.py` | 998-1025 | the WR-09 test pins statement order, not behaviour | Info (IN-08, open; same class as IN-05) | cannot see a regression of the window; the scratch probes can |

No TBD, FIXME, XXX, TODO or HACK in `app.js`.

### Known debt that bears on the goal (unchanged)

Filed under `docs/tech_debt/active/`; none breaks a success criterion on the sizes the goal names: first ubuntu
dispatch of `pair.yml` (must), `screw pair` exit codes 1 and 2 collide with failure exits (must), fillet ring can
overhang the head flats (must), the countersink-cutter and lead-in-gate items (must), interim nut bounds, the
unpurchased ISO standards. IN-07 (the nut narrow-s test band) stays open in the review disposition; it is a test gap
with no defect found, outside the page.

### Human Verification Required

These are the owner's end-of-phase items (also in the frontmatter). The code and my headless runs agree with the
expected results; no human has looked at the final build.

1. **UAT test 1 on the final build.** `make serve`, kind nut, clearance empty, pick ISO 4032 then M6.
   Expected: selects hold, fields M6, nothing builds. Why human: the owner reported this as failed (G-05-1) and the
   browser is not in the gate (L01).
2. **UAT test 3 on the final build.** Type 0.1 on the nut, Matching bolt, Matching nut. Expected: the nut opens at 0.1
   and builds. Also type 0.1, Reset, switch to the bolt and confirm its Matching nut link carries no clearance.
   Why human: the owner reported this as failed (G-05-3).
3. **Throttled kind switch, then Matching nut and Back, in a real browser.** Expected: no picker, badge or old
   control on screen while the nut loads, no console error, and Back reopens the bolt whole. Why human: the window is
   one localhost request long; my probes simulate the delay by holding the request.

### Gaps Summary

No gaps. The one gap of the previous report (WR-09, 05-23 truth C4) is closed in code and in a browser, and nothing
regressed. The warning WR-10 (a failed schema fetch on a kind switch leaves a blank form beside the old part's
panel) is real, recorded open, and breaks no must-have truth or roadmap success criterion; the owner may close it with
a small plan (wrap `buildForm` in navigate as `loadPresets` is wrapped) or file it as debt. What remains for the phase
is the owner's confirmation of UAT tests 1 and 3 and the throttled-switch check on the final build.

---

_Verified: 2026-10-22T09:00:00Z_
_Verifier: Claude (gsd-verifier)_
