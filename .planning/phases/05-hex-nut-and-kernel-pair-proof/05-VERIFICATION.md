---
phase: 05-hex-nut-and-kernel-pair-proof
verified: 2026-10-21T16:10:00Z
status: gaps_found
score: 28/29 must-haves verified
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
covered_digest: "v3:sha256:a1735b7637f03a85ed555e093ec9effe7acbf062e8ade411dc632af3c68a0432"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 19/20
  gaps_closed:
    - "WR-07 (05-22 truth 3 and the L15 amendment): the typed-clearance memory is keyed by formKind; the nut's Matching bolt link no longer carries the clearance, update() holds while a kind switch loads, Back rebuilds the bolt"
    - "WR-08 (partial): Reset and a link that writes another value forget the remembered clearance"
    - "IN-05 and IN-06 (rowOfFields guard, source pins): resolved as findings"
  gaps_remaining:
    - "WR-09 / 05-23 truth 'IN-06: no page error during the kind-switch window': a pick in the old kind's picker throws during the window"
  regressions: []
gaps:
  - truth: "05-23 must-have: 'IN-06: no page error during the kind-switch window. rowOfFields treats a catalogue row naming a field the form lacks as not held, and never throws'"
    status: partial
    reason: "The second sentence holds (rowOfFields is guarded and cannot be reached in the window, because update() returns first). The first sentence, 'no page error during the kind-switch window', is false on one path, WR-09. buildForm replaces the controls at once but the old kind's preset picker and catalogue stay on screen and live until loadPresets lands (app.js:323-325). A pick there runs pick(), which does write(fields.get(name).input, value) at app.js:234 with no guard. Bolt rows carry length, which the nut form lacks, so it throws 'Cannot read properties of undefined (reading 'input')'. Reproduced by me in a headless browser on HEAD 791e232: bolt page, Kind to nut with api/presets?kind=nut held, the stale Size select changed. Result: one pageerror, and the nut's controls briefly read d 6, pitch 1 (the bolt row's values) before the finished navigation rewrote them (after load: d 6, pitch 1, s 10, m 5.2, picker ISO 4032 / M6, nothing wrong persisted). No api request carried the value, the hash stayed #kind=nut, and the memory is untouched (a programmatic write is not an input event). So no wrong part, link, hash or download results; the effect is a console error and a few hundred ms of the old row's numbers in the controls, on a window that is one request long on localhost. The plan's own probe never touched the picker, so it did not see this, and nothing in the gate can."
    artifacts:
      - path: "src/screw/static/app.js"
        issue: "pick() (line 234) dereferences fields.get(name) unguarded; navigate()'s rebuild block (lines 315-331) leaves the old picker and catalogue live until loadPresets lands"
    missing:
      - "Call clearPicker() in navigate()'s rebuild block next to dropMesh(), so no picker or catalogue of the old kind is on screen while the new form is (05-REVIEW.md WR-09 gives the patch); or make pick() return while formKind !== currentKind"
      - "A source pin that the rebuild block clears the picker before awaiting buildForm(kind)"
      - "A line in the L15 amendment or UI-SPEC rule 36 only if the behaviour described changes; the stated invariant (no wrong part, hash, request or link) already holds"
---

# Phase 5: Hex Nut and Kernel Pair Proof Verification Report

**Phase Goal:** For any bolt a user can get the matching ISO 4032 nut at a chosen radial clearance, see the pair's numbers on the info panel, and get a kernel verdict on whether the pair mates, one that cannot report `proven` when its own control did not fire.
**Verified:** 2026-10-21T16:10:00Z
**Status:** gaps_found
**Re-verification:** Yes, after gap closure plan 05-23 (WR-07, WR-08). HEAD 791e232.

## Verdict in one paragraph

The phase goal is achieved and 05-23 did what it set out to do. The previous gap (WR-07, a clearance typed in the
kind-switch window reaching the bolt's hash) is closed, and so is the softer one (WR-08, Reset and links leaving a
stale clearance in the memory). I re-ran both in a real headless browser on HEAD. One of 05-23's own truths is still
false as worded: "IN-06: no page error during the kind-switch window". The reviewer's WR-09 is real, I reproduced
it, and it fails that truth. It does not fail the phase goal or any roadmap success criterion, and it breaks no L02
rule (no wrong part, hash, request, link or printed measurement results). Because a must-have truth is contradicted
and the status tree has no "minor" setting, the status is `gaps_found`, not `passed`. The fix is one call in
`navigate()` and a pin.

## Decision on WR-09

**Does WR-09 fail 05-23's truth "IN-06: no page error during the kind-switch window ..."? Yes, on the first sentence.**
I did not take the reviewer's word. I read `app.js` and ran it.

- Source. `navigate()` line 322-331: `dropMesh()`, then `buildForm(kind)` (replaces `fields`, sets `formKind`), then
  `await loadPresets(kind)`. Only `refuseLink` calls `clearPicker()`. So from the moment `buildForm` returns until
  `loadPresets` returns, `pickerSelects`, their `change` listeners and `catalogue` belong to the old kind while `fields`
  belongs to the new one. `pick()` at line 234 does `write(fields.get(name).input, value)` for each field of the old
  row. The nut form has no `length` (and a bolt form has no `m`), so the lookup is `undefined` and it throws.
- Browser. `probe.py` (scratch, not in the repo): bolt page, nut presets request held, Kind select to nut, stale
  Size select changed. Output: `pageerrors in window after stale pick: ["Cannot read properties of undefined
  (reading 'input')"]`; controls in the window went from `d '', pitch ''` to `d '6', pitch '1'`; hash stayed `#kind=nut`;
  the only api requests were `schema?kind=nut`, `presets?kind=nut` and `nut/info?` (the last after the load); after the
  load the controls were `d 6, pitch 1, s 10, m 5.2`, picker `ISO 4032 / M6`, and the one error shown was the expected
  `Clearance (radial): Field required`. The reviewer's account matches in every detail.
- Scope of the truth. The truth is labelled IN-06 and its second sentence names `rowOfFields`, and that half is true
  and pinned. The first sentence is unqualified ("no page error"), and the plan's probe step is named "no page error
  while the kind switch loads (IN-06)". A page error does occur in the window, so the sentence as written is
  contradicted. I do not read it narrowly to rescue the score. The IN-06 finding itself said the same stale
  catalogue was the cause and that clearing it where the form is replaced was the better fix; 05-23 chose the
  smaller guard and left `pick()` open.
- Goal impact. None found. The goal is a nut at a chosen clearance, the pair numbers, and an honest kernel verdict.
  Nothing in WR-09 touches those: the `update()` guard (05-23) means no request or hash is produced in the window, the
  throw happens before `presetBasis` or `update()` are reached, the memory is not written, and the finished
  navigation overwrites every control. It is a transient wrong number in a form control the user just set from a
  stale picker, not a number the tool prints for cutting.
- Severity. Status is `gaps_found` because a must-have is contradicted. By effect it is a warning: narrow trigger (one
  localhost request), self-healing, fails before any side effect. It is not filed as debt (grep of `docs/` and
  `.planning/` finds WR-09 only in 05-REVIEW.md and its disposition), so the owner's choice is: close it with a
  small plan (recommended; the fix is one line and a pin), or accept it with an override that narrows the truth to
  its `rowOfFields` sentence. I do not suggest the override, because the deviation does not look intentional.

## Goal Achievement

### Observable Truths

Roadmap success criteria SC1 to SC6 and the page truth (1 to 7), then 05-21 (A1 to A6), 05-22 (B1 to B7) and the
nine must-have truths of 05-23 (C1 to C9). The prior report's 20 truths carry forward; B3 is now VERIFIED.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: ISO 4032 nut M2-M20 from a preset or mm fields on API and CLI; matching part both ways from the same d, pitch, hand; lead-ins; parity green | VERIFIED | Kernel, calc, tables, API and CLI unchanged since the prior report: `git diff e7ac42e HEAD` over `src/ tests/ Makefile pyproject.toml bench/ .github/` touches only `src/screw/static/app.js` and `tests/test_parity.py`. `tests/test_parity.py` 71 passed (my run, `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`); the orchestrator's `make verify` gave 3465 passed, exit 0 |
| 2 | SC2: `clearance` is radial mm, positive enlarges the nut thread, no default; panel shows the INFO-01 set and the 6g/6H limits | VERIFIED | Unchanged. In the browser the nut with clearance empty issues no `model.stl` request and shows `Clearance (radial): Field required` |
| 3 | SC3: `proven \| violated \| inconclusive` with the control; an empty control is `inconclusive`, never `proven`; c <= 0 inconclusive; both hands; full grid pre-registered | VERIFIED | Unchanged (no file under `calc/pair.py`, `solid/pair.py`, `cli.py` changed). Prior report ran the real kernel with planted readings; its evidence stands. Not re-run |
| 4 | SC4: the pair proof is not an API endpoint; import-linter forbids `app` and `pool` importing it | VERIFIED | Unchanged files; part of `make verify` (orchestrator, exit 0) |
| 5 | SC5: STL and STEP from the same solid; chord deviation recorded; `ControlSurfaceDeflection` on | VERIFIED | Unchanged; in the green gate |
| 6 | SC6: the M18 empty control diagnosed in one bounded task; no verdict rule changed; M18 ships `inconclusive` | VERIFIED | Unchanged; owner UAT test 5 passed |
| 7 | The page: preset pick, empty clearance with no stale part, matching-part link, kind switch, pair rows, M18 note render and behave | VERIFIED | Owner UAT tests 2, 4, 5, 6 passed; tests 1 and 3 re-run by me in a browser (A1, B1). The owner's own re-run of tests 1 and 3 on the final build is still the end-of-phase confirmation (05-UAT.md; browser behaviour is not in the gate, L01) |
| A1 | 05-21: empty clearance, ISO 4032 then M6 holds the selects, nothing builds | VERIFIED | Unchanged since the prior browser run; `probe.py` here: after the load with clearance empty the picker reads `['ISO 4032','M6']`, fields `d 6, pitch 1, s 10, m 5.2`, error `Field required`, no `nut/model.stl` |
| A2 | 05-21: after a failed update the selects show the first row the fields hold exactly, else blank | VERIFIED | `rowOfFields` (app.js:206-215), pinned and passing; the 05-23 guard (`control === undefined` returns false) only adds a case |
| A3 | 05-21: the badge reads only an info document | VERIFIED | `showMatch` line 197 unchanged |
| A4 | 05-21: a successful info document drives selects and badge from `info.preset` | VERIFIED | `exact` branch unchanged |
| A5 | 05-21: diagnosis reproduced before the fix | VERIFIED | 05-21-SUMMARY (prior report) |
| A6 | 05-21: UI-SPEC amended; browser test idea filed | VERIFIED | unchanged |
| B1 | 05-22: type 0.1 on a nut, Matching bolt, Matching nut: the nut opens at 0.1 and builds | VERIFIED | `probe.py` on HEAD: typed 0.1; bolt link `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`; following it, the bolt's Matching nut link `#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2`; following that, hash `#kind=nut&clearance=0.1`, controls `d 6, pitch 1, s 10, m 5.2, clearance 0.1`, no errors, no pageerror |
| B2 | 05-22: with nothing typed the link is as before; typing empty forgets; nothing invented | VERIFIED | `rememberTyped` deletes on `''` (app.js:705); no default introduced |
| B3 | 05-22: the remembered value never reaches the bolt: not its hash, a bolt request, a download link | VERIFIED | Was FAILED. `probe2.py`: nut catalogue held, d, pitch and clearance 0.1 typed inside the window; requests in the window were `schema?kind=nut` and the held `presets?kind=nut` only, hash `#kind=nut`; after the load 0.2 typed; the nut's Matching bolt link read `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`, following it left no error, and the bolt's Matching nut link read `#kind=nut&clearance=0.2&d=6&...&m=5.2`. `lastTyped.get`/`set` are read/written only in `showCounterpart` and `rememberTyped`/`forgetUntyped` |
| B4 | 05-22: `PartInfo.counterpart` never carries `clearance`; calc, app.py, cli.py unchanged | VERIFIED | `git diff` over `src/`: `app.js` only |
| B5 | 05-22: app.js names no field or kind; the server's fields win | VERIFIED | app.js:444 `{ kind, ...lastTyped.get(counterpart.kind), ...counterpart.fields }`; grep of app.js for `clearance`, `bolt`, `nut` outside comments returns nothing; naming test passes |
| B6 | 05-22: L15 amendment; UI-SPEC rule 37 | VERIFIED | present; its claim that the value never reaches the bolt's hash now holds (B3) |
| B7 | 05-22: RED and GREEN in the SUMMARY | VERIFIED | prior report |
| C1 | 05-23 WR-07: a clearance typed while a kind switch loads is remembered under the kind of the form on screen; the nut's Matching bolt link is the plain bolt link, following it builds, and the bolt's Matching nut link carries the clearance typed after load (0.2) | VERIFIED | Same run as B3. Source: `formKind = kind` directly after `clearForm()` in `buildForm` (line 99-100), `formKind = null` in `clearForm` (81), `rememberTyped` keyed by `formKind` (701-708); `lastTyped.set(` occurs once |
| C2 | 05-23 window, owner choice (a): while `formKind !== currentKind` `update()` returns before the hash or a request; only `schema?kind=nut` in the window; hash stays `#kind=nut` | VERIFIED | app.js:504 `if (currentKind === null \|\| formKind !== currentKind) return;` is the first statement. `probe2.py` window requests `['api/schema?kind=nut', 'api/presets?kind=nut']` (the presets request is the held catalogue fetch, not an `info`), hash `#kind=nut`, no pageerror |
| C3 | 05-23 owner choice "fix in navigate": navigate rebuilds when `kind !== currentKind \|\| kind !== formKind`; Back before the catalogue loads reopens the bolt with its own seven controls, Kind on bolt, one `bolt/model.stl` 200 | VERIFIED | app.js:315 holds the condition. `probe2.py` Back case: names `['d','pitch','length','left_hand','thread_length','s','k']`, kind `bolt`, `bolt/model.stl` statuses `[200, 200]` (the initial build and the rebuilt one), no pageerror, no error message |
| C4 | 05-23 IN-06: no page error during the kind-switch window. `rowOfFields` treats a catalogue row naming a field the form lacks as not held, and never throws | FAILED (partial) | Second sentence: VERIFIED (app.js:210-211, pinned, and unreachable in the window because `update()` returns first). First sentence: a stale-picker pick throws `Cannot read properties of undefined (reading 'input')` in the window (WR-09). Reproduced, see Decision on WR-09 and Gaps |
| C5 | 05-23 WR-08 (owner ruling): type 0.1 on a nut, Reset, switch to the bolt: its Matching nut link is `#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2`; a link that writes another value forgets 0.1 | VERIFIED | `probe.py`: after Reset and Kind select to bolt, link `#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2`. The link-overwrite case is in the plan's probe and the SUMMARY (`link:` step PASS); source: `forgetUntyped` after the write loop (app.js:341) and in Reset (729). I did not re-run the link-overwrite case separately |
| C6 | 05-23: the 05-22 round trip and the 05-21 pick are unchanged | VERIFIED | B1 and A1 above; a link that writes the same 0.1 keeps it (the round trip reaching `clearance=0.1` after Matching nut) |
| C7 | 05-23: typing is the only writer; `rememberTyped(` twice, `lastTyped.set(` once, `forgetUntyped` only deletes; app.js names no field or kind; nothing persisted; `counterpart` unchanged; calc, app.py, cli.py, index.html untouched | VERIFIED | grep: `lastTyped.set(` 1, `rememberTyped(` defined once and called once (the definition and the call are the two occurrences), `forgetUntyped` defined and called twice; `forgetUntyped` body (709-714) only `delete`s; no storage API; `git diff e30b919 HEAD` touches only `app.js`, `test_parity.py`, `decision_log.md` under `src/ tests/ docs/` |
| C8 | 05-23: the L15 amendment (one dated paragraph naming WR-07, the update guard, WR-08) and UI-SPEC rules 14, 19, 32, 35, 36, 37 in the code's commit | VERIFIED | `docs/architecture/decision_log.md`: one added paragraph, 27 insertions, 0 deletions (`git diff e30b919 HEAD`), its description matches the source and the probe. 01-UI-SPEC.md carries the dated plan 05-23 note and rules 36, 37, E16 text. The amendment's sentence "on every path neither the remembered value nor the form's value reaches the bolt's hash, a bolt request or a download link" holds on the paths I ran, including the WR-09 path (no request, hash unchanged) |
| C9 | 05-23: reproduced before the fix; RED, mid, GREEN outputs in the SUMMARY | VERIFIED | 05-23-SUMMARY.md lines 175 (`RESULT FAIL` nine steps), 192 (`RESULT FAIL` two WR-08 steps), 203 (`RESULT PASS []`) |

**Score:** 28/29 truths verified (0 present, behavior-unverified). The one failure is C4.

### Prohibitions (05-23 `must_haves.prohibitions`)

| Prohibition | Tier | Status | Evidence |
|-------------|------|--------|----------|
| No writer of `lastTyped` other than `rememberTyped`; `forgetUntyped` only deletes | test | HELD | source above; the pins `test_the_typed_memory_is_keyed_by_the_kind_of_the_form_on_screen` and `test_reset_and_a_navigation_forget_a_typed_value_the_field_no_longer_holds` are in the 71 passing |
| `update()` changed only on its first-line condition; `partQuery`, `writeHash`, `setDownloads`, `refuseLink`, `pick` unchanged; navigate changed only by the rebuild condition and the forget line | test | HELD (pick unchanged, and that is exactly WR-09) | diff read; the pinned write-loop statement is byte for byte (line 340) |
| No change to calc, app.py, cli.py, index.html; `counterpart` keeps D-02's shape | test | HELD | `git diff e7ac42e HEAD` over `src/` |
| No field or kind named in app.js, nothing persisted, no existing decision-log line edited, no WR-08 code without the L15 paragraph and UI-SPEC rules | test | HELD | 0 deleted lines in `decision_log.md`; grep of app.js; L15 paragraph and rules in the same range (58bbc9f) |
| No `--no-verify`; `.planning/HANDOFF.json` and `.continue-here.md` not staged | judgment | HELD, NON-AUTHORITATIVE | `git status` shows both still untracked, not committed; the commit hooks cannot be seen from the tree. Flagged for a human glance, not green |

### Deferred Items

None. WR-09 is not addressed by Phase 6 or later (ROADMAP has no stale-picker or kind-switch item). PAIR-02 (the default clearance) is Phase 6 and is not claimed here.

### Advisory (New Scope, Unevidenced)

None. WR-09 is evidenced by a reproduction.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/static/app.js` | `formKind`, update guard, navigate rebuild condition, guarded `rowOfFields`, key `rememberTyped` by `formKind`, `forgetUntyped` and its two call sites | VERIFIED for every item 05-23 lists; WIRED WITH ONE GAP | all six present at the stated lines; `pick()` and the stale picker are the WR-09 gap |
| `tests/test_parity.py` | the WR-07, WR-08 source tests and updated pins | VERIFIED | 71 passed. They pin source text, so they cannot see WR-09 (IN-05's remaining half, the owner's browser-test idea) |
| `docs/architecture/decision_log.md` | L15 amendment of plan 05-23 | VERIFIED | one paragraph, dated, names WR-07, the guard, WR-08 |
| `01-UI-SPEC.md` | rules 14, 19, 32, 35, 36, 37, E16, Verification status, extension rule 3, dated note | VERIFIED | rules 36 and 37, the dated note, Verification status line and extension rule 3 read; the other numbered rules were not re-read line by line |
| Phase 5 kernel, calc, tables, API, CLI | as in the prior reports | VERIFIED | unchanged since e7ac42e |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `buildForm` | `formKind` | `clearForm(); formKind = kind;` | WIRED | lines 99-100 |
| `update` | hash and requests | first-line return while `formKind !== currentKind` | WIRED | line 504; observed in the window |
| `navigate` | `dropMesh`, `buildForm`, `loadPresets` | rebuild when `kind !== currentKind \|\| kind !== formKind` | WIRED | line 315; Back case observed |
| `rememberTyped` | `lastTyped` | `lastTyped.set(formKind, typed)` | WIRED | line 707 |
| navigate write loop and Reset | `forgetUntyped` | `for (const { input } of fields.values()) forgetUntyped(input);` | WIRED | lines 341 and 729 |
| `rowOfFields` | `fields` | `control === undefined` returns false | WIRED | lines 210-211 |
| old picker | `pick` | `select` `change` listener, `catalogue` | NOT GUARDED | stays live across `navigate`'s rebuild until `loadPresets` lands (WR-09) |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| Matching-part link | `lastTyped` + `info.counterpart` | the user's `input` events and the info document | yes, keyed by the form on screen | FLOWING |
| Picker selects | `catalogue`, `rowOfFields()` | `GET /api/presets?kind=` and the form | yes; stale for one request after a kind switch | FLOWING (WR-09 window) |
| Nut info panel, `PairReport` | as the prior reports | unchanged | yes | FLOWING |

### Behavioral Spot-Checks

Scratch Playwright probes against `.venv/bin/screw serve --port 8061` (spur's Playwright, headless shell), in
`/private/tmp/claude-501/-Users-half-git-halfb00t-screw/1390206a-030d-4e4c-b605-e2cc70f8b492/scratchpad/verify/`, not in the repo (L01). The server is stopped.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| WR-09: stale-picker pick during the kind-switch window | `probe.py` | pageerror `Cannot read properties of undefined (reading 'input')`; controls `d 6, pitch 1` for a moment; hash `#kind=nut`; no bad request; state healed after load | CONFIRMED (gap) |
| Round trip, UAT 3: 0.1, Matching bolt, Matching nut | `probe.py` | `#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2`, nut at 0.1 | PASS |
| WR-08: 0.1, Reset, switch to bolt | `probe.py` | link `#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2` (no clearance) | PASS |
| WR-07: type in the window, retype after load | `probe2.py` | window requests only schema and the held presets; nut->bolt link plain; bolt link builds; bolt->nut link `clearance=0.2` | PASS |
| Back before the catalogue loads | `probe2.py` | bolt rebuilt with seven controls, `bolt/model.stl` 200, no error | PASS |
| Page source assertions | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` | 71 passed | PASS |
| Full gate | not re-run by me; orchestrator: `make verify` at HEAD, 3465 passed, exit 0 | accepted | PASS |

I did not re-run the real-kernel `screw pair` runs or the nut, mesh and presets suites: nothing under `calc/`, `solid/`, `tables/`, `cli.py` or `app.py` changed since the prior report, which ran them.

### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared by the phase. SKIPPED.

### Requirements Coverage

Every ID in the phase list is claimed by at least one PLAN's `requirements:` frontmatter (05-23 claims TYPE-04; the rest as in the earlier reports) and each maps to Phase 5 in REQUIREMENTS.md. PAIR-02 maps to Phase 6 and no Phase 5 plan claims it. No orphans. REQUIREMENTS.md currently reads `Gaps Found` for the nine rows (f0c73e8 reverted them); it needs to read Complete only when the phase passes.

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| TYPE-03 | 05-02, 04, 05, 06, 07, 13, 18, 19, 20, 21 | SATISFIED | 14 cited rows; page picks hold with an empty clearance (A1) |
| TYPE-04 | 05-10, 05-18, 05-22, 05-23 | SATISFIED | API and CLI both ways; the page's link round trip works (B1, B3, C1) and no longer breaks on the WR-07 path. WR-09 does not touch the link |
| THRD-05 | 05-02, 11, 12, 13, 18, 20 | SATISFIED | unchanged |
| PAIR-01 | 05-04, 05, 09, 10, 18 | SATISFIED | unchanged |
| PAIR-03 | 05-01, 03, 05, 09, 14, 15, 16, 18, 20 | SATISFIED | unchanged; kernel evidence stands |
| PAIR-04 | 05-01, 03, 14, 15, 16, 18, 20 | SATISFIED | unchanged; first ubuntu grid run is filed debt |
| INFO-01 | 05-02, 06, 07, 08, 09, 18 | SATISFIED | unchanged |
| INFO-02 | 05-02, 08, 09, 18 | SATISFIED | unchanged |
| FRNT-06 | 05-02, 17, 18 | SATISFIED | unchanged |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/screw/static/app.js` | 234, 315-331 | `pick()` dereferences `fields.get(name)` unguarded while the old kind's picker is live | Warning (WR-09; fails 05-23 truth C4) | console error and a transient wrong number in the controls; no wrong part, hash, request or link |
| `tests/test_parity.py` | pins on page source | tests pin source text and none runs the page | Info (IN-05, owner's open idea) | cannot see WR-09 |

No TBD, FIXME, XXX, TODO or HACK in `app.js`.

### Known debt that bears on the goal (unchanged)

Filed under `docs/tech_debt/active/`; none breaks a success criterion on the sizes the goal names: first ubuntu dispatch of `pair.yml` (must), `screw pair` exit codes 1 and 2 collide with failure exits (must), fillet ring can overhang the head flats (must), the countersink-cutter and lead-in-gate items (must), interim nut bounds, the unpurchased ISO standards. IN-07 (the nut narrow-s test band) stays open in the review disposition; it is a test gap with no defect found, outside the page.

### Human Verification Required

Not frontmatter items, because `gaps_found` takes precedence. The owner's end-of-phase re-run stands.

1. **UAT test 1 on the final build.** `make serve`, kind nut, clearance empty, pick ISO 4032 then M6. Expected: selects hold, fields M6, nothing builds. My headless run agrees; no human has looked.
2. **UAT test 3 on the final build.** Type 0.1 on the nut, Matching bolt, Matching nut. Expected: the nut opens at 0.1 and builds. Also: type 0.1, Reset, switch to the bolt, and confirm its Matching nut link carries no clearance.

### Gaps Summary

One gap, page only, and small: the old kind's preset picker is left live while a kind switch loads, so a pick in it
throws and briefly writes the old kind's row into the new kind's controls (WR-09). It contradicts the first sentence
of 05-23's IN-06 truth. It is not a phase-goal failure: the nut, the pair numbers and the kernel verdict, and the
`proven`-only-when-the-control-fired rule, all hold, and no L02 rule is broken. WR-07 and WR-08 are closed and
re-run in a browser, and no earlier truth regressed. The fix is one `clearPicker()` call in `navigate()`'s rebuild
block (or a guard in `pick()`) with a source pin, and the owner's re-run of UAT tests 1 and 3. No kernel, calc, API
or CLI work is needed.

---

_Verified: 2026-10-21T16:10:00Z_
_Verifier: Claude (gsd-verifier)_
