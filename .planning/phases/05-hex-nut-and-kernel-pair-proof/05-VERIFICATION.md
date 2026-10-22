---
phase: 05-hex-nut-and-kernel-pair-proof
verified: 2026-10-22T10:00:00Z
status: human_needed
score: 47/47 must-haves verified
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
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-25-PLAN.md
  - .planning/phases/05-hex-nut-and-kernel-pair-proof/05-25-SUMMARY.md
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
covered_digest: "v3:sha256:0f37cd37bd8dbfae057a85311c9e74858f91e79eaab3db681db8b3f7814535b7"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 37/37
  gaps_closed:
    - "WR-10 (review, warning, outside the must-haves in the prior report): a failed schema fetch on a kind switch left a blank form under the old part's panel, downloads and matching-part link; fixed by 05-25 (b857016), reproduced closed in a headless browser on HEAD ddd07df"
    - "IN-08 (info): the WR-09 pin pinned statement order with file-wide counts; re-bodied with a comment-stripping helper (b857016)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "UAT test 1 on the final build. `make serve`, kind nut, clearance empty, pick ISO 4032 then M6."
    expected: "The selects hold ISO 4032 / M6, the fields read M6 (d 6, pitch 1, s 10, m 5.2), nothing builds, the one error is the missing clearance."
    why_human: "The owner reported this as a failure (05-UAT.md test 1, G-05-1). Verified in my headless run on HEAD (probe_05_23 step `pick:` PASS), but no human has re-run it, and browser behaviour is not in the gate (L01)."
  - test: "UAT test 3 on the final build. Type 0.1 on the nut, follow Matching bolt, then Matching nut. Also: type 0.1, Reset, switch to the bolt, and read its Matching nut link."
    expected: "The nut opens at 0.1 and builds. After Reset the bolt's Matching nut link carries no clearance."
    why_human: "The owner reported this as a failure (05-UAT.md test 3, G-05-3). probe_05_23 round-trip and reset steps PASS on HEAD; the owner's confirmation is the end-of-phase item."
  - test: "WR-09 / WR-10 browser check in a real browser (05-25 owner end-of-phase item). (a) Devtools: block the request `api/schema?kind=nut`, switch Kind to nut, then unblock and pick nut again. (b) Throttle the network, switch the kind to nut and watch the window. (c) Follow Matching nut, then press Back during the load."
    expected: "(a) Blocked: no form control, no panel rows, no Matching link, both downloads without href, no picker or badge, the status empty, the one message `Could not load the part: <network error>`, the Kind select deselected; picking nut again opens the nut's six controls, its picker ISO 4032 / M6 and `Clearance (radial): Field required`. (b) Throttled: while the nut loads, no picker, badge, panel, link, download or control of the bolt is on screen and the console has no error. (c) Back during the load reopens the bolt whole: seven controls, picker ISO 4017 / M6 / 20, badge `matches ISO 4017 M6 x 20`, its panel and downloads, and it builds."
    why_human: "The windows are one localhost request long and browser behaviour is not in the gate (L01). My probes hold or fail the request with a route handler, a faithful stand-in; 05-24 and 05-25 name the real-browser run as the owner's end-of-phase item. A real browser's own network error text and the real select's change behaviour are only visible there."
---

# Phase 5: Hex Nut and Kernel Pair Proof Verification Report

**Phase Goal:** For any bolt a user can get the matching ISO 4032 nut at a chosen radial clearance, see the pair's numbers on the info panel, and get a kernel verdict on whether the pair mates, one that cannot report `proven` when its own control did not fire.
**Verified:** 2026-10-22T10:00:00Z
**Status:** human_needed
**Re-verification:** Yes, after gap closure plan 05-25 (WR-10, IN-08). HEAD ddd07df, working tree clean for tracked files (untracked: `.planning/HANDOFF.json`, `.continue-here.md`, `.planning/ui-reviews/`).

## Verdict in one paragraph

The phase goal is achieved and 05-25 closed the one open warning of the prior report. I reproduced WR-10's failure
path in a headless browser on HEAD: with `api/schema?kind=nut` answering 500 on a Kind switch, nothing of the bolt
stays on screen (0 controls, 0 panel rows, no Matching link, both downloads without `href`, picker hidden, status
empty), the one message is `Could not load the part: 500 Internal Server Error`, the Kind select is deselected, no page
error. Picking nut again retries and opens the nut. The same failure through the Matching nut link is refused the same
way and Back reopens the bolt whole. A late 500 for a switch the user already left refuses nothing. No earlier truth
regressed: the 05-23 probe passes 17 of 17, and `make verify` is green (3467 passed, exit 0) in my own run. The
status is `human_needed`, not `passed`, only because the owner reported UAT tests 1 and 3 as failures, has not re-run
them on the final build, and the WR-09/WR-10 real-browser check is the owner's end-of-phase item (browser behaviour is
not in the gate, L01).

## What changed since the prior report (9f68e69 to ddd07df)

`git diff --stat 9f68e69 HEAD`: `src/screw/static/app.js` (21 lines), `tests/test_parity.py` (67 lines),
`01-UI-SPEC.md` (31), `05-REVIEW-DISPOSITION.md`, `05-REVIEW.md`, `05-SECURITY.md`, `05-UI-REVIEW.md`,
`05-VALIDATION.md`, `05-25-PLAN.md`, `05-25-SUMMARY.md`, ROADMAP/STATE. Nothing under `src/screw/calc`, `solid`,
`tables`, `app.py`, `cli.py`, `params.py`, `index.html`, and no change to `docs/architecture/decision_log.md`
(`git diff 9f68e69 HEAD -- docs/architecture/decision_log.md` is empty; `git diff --stat bb13513 9f68e69 -- src tests docs`
is empty too). So every kernel, calc, table, API and CLI truth of the prior report stands on unchanged files and on a
fresh green gate.

md5 of the three files the plan grounded: `app.js` `b77c651e...` (matches the plan's pinned result),
`tests/test_parity.py` `71ee546a...`, `01-UI-SPEC.md` `fd5268ae...` (both match the SUMMARY).

## Decision on WR-10 and IN-08 (the items under re-verification)

**WR-10 closed.** Source, `src/screw/static/app.js:295-355`:

- `const mine = ++formSeq;` (line 299).
- In the kind-change block, after `dropMesh(); clearForm(); clearPicker();` come `$('#dims').replaceChildren();
  showCounterpart(null); setDownloads(null); setStatus('');`, all before the first `await`. The helpers do what the
  names say (`showCounterpart(null)` sets `hidden`; `setDownloads(null)` strips every `href`; read at app.js:466-495).
- One `try` holds both `if (!(await buildForm(kind))) return;` and `if (!(await loadPresets(kind))) return;`. The
  `catch` runs `if (mine !== formSeq) return;` and only then `return refuseLink(...)`. `refuseLink` (app.js:277-287)
  sets `selectedIndex = -1`, which is the retry.
- Only `navigate()` changed (`git diff 9f68e69 HEAD -- src`); `refuseLink`, `buildForm`, `loadPresets`, `update`,
  `renderInfo`, the startup block are untouched. No TBD/FIXME/XXX/TODO/HACK in `app.js`.

Browser evidence, my probes on HEAD (headless Chromium via spur's Playwright, `screw serve --port 8081`; scratch in
`.../scratchpad/verify-05/`, not in the repo; server stopped):

| Check | Reading |
|---|---|
| Schema 500 on Kind switch from bolt (`p25.py`) | `{inputs: 0, dims: 0, link: None, picker: {hidden: true, sel: 0, badge: ''}, kindIdx: -1, hash: '#kind=nut', status: ''}`, message `Could not load the part: 500 Internal Server Error`, page errors `[]` |
| Retry: schema answering again, select nut | 6 controls, picker 2 selects, status empty, kindIdx 1, no page error |
| Matching nut link, schema held then 500 (`p25b.py`) | window: 0 inputs, panel 0, link None, downloads None, picker empty; after 500: `kindIdx -1`, hash kept `#kind=nut&d=6&...`, the one message |
| Back after that refusal | bolt whole: 7 controls, picker `ISO 4017/M6/20`, badge `matches ISO 4017 M6 x 20`, panel 9, both bolt downloads |
| Overtaken: nut schema held, select bolt, then the late 500 | bolt whole before and after (7 controls, picker, badge, panel 9, link, two downloads), message empty, page errors `[]` |
| Catalogue window (`p25c.py`, `api/presets?kind=nut` held) | nut controls 6, panel 0, link None, downloads None, picker empty, status empty; after the load picker `ISO 4032/M6`, message `Clearance (radial): Field required`; nut at 0.1: panel 11, link `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`, downloads `api/nut/model.stl?clearance=0.1&quality=fine` and `.step`, no page error |
| 05-23 regression probe (`p23.py http://127.0.0.1:8081/`, the 05-23 plan's own probe, unchanged) | 17 PASS, `RESULT PASS []` |

**IN-08 closed.** Test body read (`tests/test_parity.py:998-1040`): `_rebuild_block()` strips `//` comment lines and
squashes whitespace; the WR-09 pin now asserts the seven clears come before the first `await` and counts nothing
file-wide; the WR-10 pin asserts one `try` with both awaits, and that the guard precedes the refusal in the `catch`.
`make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`: **73 passed**. I did not re-run the plan's mutant
script (`mutants_05_25.py`, in the SUMMARY: `MUTANTS PASS []`, eleven ok lines); that part rests on the SUMMARY. The pin
still tests source order, not behaviour; the behaviour is covered by the probes above and the idea
`docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md` stays the owner's call. Not a gap.

## Goal Achievement

### Observable Truths

Truths 1 to 7, A1 to A6, B1 to B7, C1 to C9 and D1 to D8 are carried forward from the prior report. The code they
rest on is unchanged except `navigate()`'s kind-change block; I re-checked each family against HEAD (see "Regression
check"). F1 to F10 are the ten must-have truths of 05-25.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: ISO 4032 nut M2-M20 from a preset or mm fields on API and CLI; matching part both ways; lead-ins; parity green | VERIFIED | Unchanged files; `make verify` 3467 passed, exit 0 (my run); `tests/test_parity.py` 73 passed |
| 2 | SC2: `clearance` is radial mm, positive enlarges the nut thread, no default; panel shows the INFO-01 set and the 6g/6H limits | VERIFIED | Unchanged; nut with empty clearance shows `Clearance (radial): Field required` and issues no model request (p25c) |
| 3 | SC3: `proven \| violated \| inconclusive` with the control; an empty control is `inconclusive`, never `proven`; c <= 0 inconclusive; both hands; full grid pre-registered | VERIFIED | `calc/pair.py`, `solid/pair.py`, `cli.py` unchanged since the report that ran the real kernel with planted readings; in the green gate |
| 4 | SC4: the pair proof is not an API endpoint; import-linter forbids `app` and `pool` importing it | VERIFIED | Unchanged; the contract is part of `make verify` (exit 0) |
| 5 | SC5: STL and STEP from the same solid; chord deviation recorded; `ControlSurfaceDeflection` on | VERIFIED | Unchanged; in the green gate |
| 6 | SC6: the M18 empty control diagnosed in one bounded task; no verdict rule changed; M18 ships `inconclusive` | VERIFIED | Unchanged; owner UAT test 5 passed |
| 7 | The page: preset pick, empty clearance with no stale part, matching-part link, kind switch, pair rows, M18 note render and behave | VERIFIED | Owner UAT tests 2, 4, 5, 6 passed; tests 1 and 3 re-run by me on HEAD (`p23.py` steps `pick:`, round trip, `cleared:`); owner re-run is the human item |
| A1-A6 | 05-21: the ISO 4032 / M6 pick holds with an empty clearance; `rowOfFields`; badge reads only an info document | VERIFIED | `p23.py` `pick:` PASS (selects `ISO 4032 / M6`, nothing builds); my p25c: after the load the picker is `ISO 4032/M6` and the badge empty until the nut builds |
| B1-B7 | 05-22: typing is remembered per kind; Matching bolt then Matching nut opens the nut at 0.1; never reaches the bolt; `counterpart` never carries `clearance`; app.js names no field or kind; L15 amendment | VERIFIED | `p23.py` round-trip, `cleared:`, `fresh page:` and window steps PASS (17/17); naming tests in the 73 passed; `decision_log.md` unchanged |
| C1-C9 | 05-23: typing keyed by the form on screen, update guard in the window, Back before the catalogue loads, no page error, Reset and link forgetting, `lastTyped.set(` once | VERIFIED | `p23.py` 17/17 on HEAD; pins in the 73 passed; 05-25's diff adds no writer of `lastTyped` and no `formKind =` assignment |
| D1-D8 | 05-24: the old form and picker off screen for the whole switch, Back during either fetch, no page error, the WR-09 pin, UI-SPEC | VERIFIED | `p23.py` window/back steps; p25c catalogue window (picker empty, no select); p25b Back; the WR-09 pin is in the 73 passed (now re-bodied by 05-25, see F8) |
| F1 | 05-25: schema 500 on a Kind switch leaves nothing of the bolt: `{inputs 0, dims 0, link null, downloads [null, null], picker hidden/0 selects/badge ''}`, one error `Could not load the part: 500 Internal Server Error`, select deselected, hash `#kind=nut`, status empty, no page error | VERIFIED | My `p25.py` run, exact values (table above) |
| F2 | 05-25 recovery: picking any kind retries (nut opens six controls, picker `ISO 4032 / M6`, `Clearance (radial): Field required`); the same failure through Matching nut is refused with the hash kept and Back reopens the bolt whole and it builds; reload retries | VERIFIED | `p25.py` retry step, `p25b.py` link/Back steps. Reload retrying is by construction (startup is a navigation, app.js:295 path) and not separately run; the bolt's rebuild after Back shows `bolt/model.stl` requested |
| F3 | 05-25 startup: a failed first schema fetch is refused like any switch (`Could not load the part: ...`, select deselected); a failed `/api/kinds` still shows the startup message | VERIFIED | Code path read: startup enters the same kind-change block (`currentKind` null), the same `try` and `catch`; the `/api/kinds` path is untouched (`git diff` shows only the navigate hunk). I did not run a failing-first-schema startup in a browser; the SUMMARY's `probe_05_25.py` step `startup` is the only direct run. The retry-after-failure mechanism it depends on is the one I ran (F1/F2) |
| F4 | 05-25 owner decision, stale panel: from the start of a switch until the new kind's first info document the old panel, link and downloads are off screen in the schema and catalogue windows; the new kind writes them again (nut at 0.1: 11 rows, `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`, nut downloads at 0.1; empty clearance keeps all three empty) | VERIFIED | p25 (schema window via the 500, link None, dims 0, downloads None), p25b link window, p25c catalogue window and nut at 0.1 (exact values: 11 rows, link, both downloads). Bolt-side 9-row panel with link carrying 0.1 is in `p23.py` round-trip (`bolt's Matching nut carries 0.1`) and p25b Back (panel 9, bolt downloads) |
| F5 | 05-25 status: a failed bolt's `Showing the last valid part` does not stay over the empty canvas; the status reads empty during the switch and after | VERIFIED | `setStatus('')` before the first await (app.js:341); p25 FAIL snapshot `status: ''`, p25c windows `status: ''`. The failed-bolt precondition was not separately staged by me |
| F6 | 05-25 overtaken switch: a 500 for a switch the user left leaves the bolt whole (seven controls, `ISO 4017 / M6 / 20`, badge, panel, link, downloads, no error) | VERIFIED | p25b scenario 2 for the schema failure: whole before and after the late 500, message empty. The catalogue failure variant is the same guard (`mine !== formSeq`, one `catch`); the SUMMARY's probe covers it, not re-run by me |
| F7 | 05-25: no truth of 05-21 to 05-24 regresses; 05-23 probe 17/17 and 05-24 probe 11/11 unchanged | VERIFIED | `p23.py` 17/17 on HEAD (my run). `probe_05_24.py` not re-run by me; its WR-09 content is covered by p25c (catalogue window), p25 (schema window) and p25b (Back), and its pin is in the 73 passed |
| F8 | 05-25 pins and IN-08: both pins drop comment lines and count nothing file-wide; RED 2 failed 71 passed at BASE; GREEN 73 passed; mutant check | VERIFIED | Test bodies read; `73 passed` in my run. The RED count and the eleven-line mutant run rest on the SUMMARY (not re-run) |
| F9 | 05-25 UI-SPEC considerations E2, E3, E10, E11, E15, E17 as lifted; `Applicable:` count stays 82 | VERIFIED | `git diff 9f68e69 HEAD -- 01-UI-SPEC.md` carries the E2/E3/E10/E11/E15/E17 rows, matching the built behaviour (spot-read E15: hidden "again after ... the start of a kind switch"; E11: "unless a newer navigation has overtaken"). I did not count the `Applicable:` line |
| F10 | 05-25: the contract lands with the code (Copywriting rows, rules 14, 30, 34, 36, the dated note, Verification-status bullet, Extension rule 3); L15 not edited; WR-10 and IN-08 read `fixed` with the fix sha | VERIFIED | The same diff carries the dated 05-25 note, the three Copywriting rows, rules 14/30/34/36, the Verification-status bullet and the Extension rule 3 clause; `decision_log.md` diff empty; `05-REVIEW-DISPOSITION.md`: `WR-10 \| fixed \| b857016 fix(05-25)...`, `IN-08 \| fixed \| b857016...`, `open: 1` (IN-07) |

**Score:** 47/47 truths verified (0 present, behavior-unverified). Counting: 37 carried forward + F1 to F10.

### Regression check (carried-forward truths)

The carried truths are about the working path and about files that are unchanged. For the page, the only change
since the last report is the navigate block, so I re-ran the probe that exercises the page truths (05-23's, 17/17) and
the 05-25 scenarios above, and `make verify` for everything else. Not regressed.

### Prohibitions (05-25 and carried)

| Prohibition | Tier | Status | Evidence |
|-------------|------|--------|----------|
| No number, link, download or status claim of one part beside another kind's form during a switch or after a failed one; the failure of an overtaken navigation refuses nothing (05-25) | test | HELD | F1, F4, F5, F6; pins in the 73 passed. The enforcement is a page-source pin plus my browser runs, not a browser test in the gate (IN-05 idea) |
| app.js changed only by the grounded patch; no new message string, fetch, retry button or timer | test | HELD | `git diff 9f68e69 HEAD -- src` is the navigate hunk only; md5 `b77c651e...` equals the plan's pinned result |
| No change to calc, app.py, cli.py, index.html, style.css, decision_log.md; app.js names no field or kind; nothing persisted | test | HELD | the same diff; `decision_log.md` diff empty; naming tests in the 73 passed |
| No `--no-verify`; `.planning/HANDOFF.json`, `.continue-here.md`, `.planning/ui-reviews/` not staged; no scratch probe committed | judgment | HELD, NON-AUTHORITATIVE | `git status` still shows the three paths untracked, and no probe or patch file is in the 05-25 commits' file list (`git diff --stat`). Commit hooks cannot be seen from the tree: flagged for a human glance, not green |
| Carried: no writer of `lastTyped` but `rememberTyped`; no field or kind named in app.js | test | HELD | pins pass |

### Deferred Items

None. PAIR-02 (the default clearance) is Phase 6 and is not claimed here. IN-07 stays open (below).

### Advisory (New Scope, Unevidenced)

None.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/static/app.js` | `mine`, seven clears, one try, guarded catch; contains `plan 05-25` | VERIFIED | lines 295-355; wired (runs on every navigation, startup included) |
| `tests/test_parity.py` | re-bodied WR-09 pin, the WR-10 pin, `_rebuild_block` | VERIFIED | lines 998-1040; 73 passed |
| `01-UI-SPEC.md` | rows, rules, dated note | VERIFIED | in the 05-25 diff |
| `05-REVIEW-DISPOSITION.md` | WR-10 and IN-08 `fixed` with sha | VERIFIED | `b857016`; 1 of 18 open |
| Phase 5 kernel, calc, tables, API, CLI | as in the prior reports | VERIFIED | unchanged; in the green gate |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `navigate` | panel, link, downloads, status | `clearPicker(); $('#dims').replaceChildren(); showCounterpart(null); setDownloads(null); setStatus(''); try {` | WIRED | app.js:337-341; pinned; observed in all three windows |
| `navigate` catch | `refuseLink` | `if (mine !== formSeq) return; return refuseLink(...)` | WIRED | observed: refused when newest, silent when overtaken |
| `navigate` | `formSeq` | `const mine = ++formSeq;` | WIRED | app.js:299 |
| `renderInfo` / `update` | panel, link, downloads | unchanged code writes them after the switch | WIRED | nut at 0.1: 11 rows, link, nut downloads (p25c) |
| `refuseLink` | selector | `kindSelect.selectedIndex = -1` | WIRED | retry by re-pick observed |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| Info panel, link, downloads after a switch | info document | `nut/info` after the nut's first successful update | yes; empty in the windows instead of stale | FLOWING |
| Picker selects | `catalogue`, `rowOfFields()` | `GET /api/presets?kind=` and the form | yes | FLOWING |
| Nut info panel, `PairReport` | as the prior reports | unchanged | yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full gate | `make verify` (my run, HEAD ddd07df) | `3467 passed in 166.93s`, EXIT 0 | PASS |
| Page source assertions | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` | 73 passed | PASS |
| WR-10 schema 500, retry | `p25.py` | see table above | PASS |
| WR-10 link refusal, Back, late 500 for an overtaken switch | `p25b.py` | see table above | PASS |
| Catalogue window, nut at 0.1 | `p25c.py` | see table above | PASS |
| 05-23 regression probe | `p23.py http://127.0.0.1:8081/` | 17 PASS, `RESULT PASS []` | PASS |

Stated for the record: code re-review at cee263d (0 critical, 0 warning, 1 info IN-07 open), disposition at ddd07df
(1 of 18 open), security register 87/87 closed (d482100), validation strategy 1f2c24c and UI review 24/24 (343c6c5)
are cited from the orchestrator's evidence and the files' commit subjects; I did not re-run the audits.

### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared by the phase. SKIPPED.

### Requirements Coverage

Every ID in the phase list is claimed by at least one PLAN's `requirements:` frontmatter (grep of `05-*-PLAN.md`) and
each maps to Phase 5 in REQUIREMENTS.md. PAIR-02 maps to Phase 6 and no Phase 5 plan claims it. No orphans.

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| TYPE-03 | 02, 04, 05, 06, 07, 13, 18, 19, 20, 21 | SATISFIED | tables and nut solid unchanged and green; the page pick holds with an empty clearance |
| TYPE-04 | 10, 18, 22, 23, 24, 25 | SATISFIED | API and CLI counterpart tests pass; the page round trip (`p23.py`) and the 05-25 switch behaviour (F1 to F6) hold. The `[x]` / Complete in REQUIREMENTS.md (lines 34, 134) is confirmed |
| THRD-05 | 02, 11, 12, 13, 18, 20 | SATISFIED | unchanged |
| PAIR-01 | 04, 05, 09, 10, 18 | SATISFIED | unchanged |
| PAIR-03 | 01, 03, 05, 09, 14, 15, 16, 18, 20 | SATISFIED | unchanged; kernel evidence stands |
| PAIR-04 | 01, 03, 14, 15, 16, 18, 20 | SATISFIED | unchanged; first ubuntu grid run is filed debt |
| INFO-01 | 02, 06, 07, 08, 09, 18 | SATISFIED | unchanged |
| INFO-02 | 02, 08, 09, 18 | SATISFIED | unchanged |
| FRNT-06 | 02, 17, 18 | SATISFIED | unchanged |

REQUIREMENTS.md still reads `Gaps Found` for the eight rows other than TYPE-04 (lines 124-152) and the checkboxes
for THRD-05, PAIR-01, PAIR-03, PAIR-04, TYPE-03, INFO-01, INFO-02, FRNT-06 are unticked. All nine are SATISFIED on the
evidence, so the table is inconsistent until the orchestrator moves them to Complete after the owner confirms the
human items. I did not edit REQUIREMENTS.md.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_parity.py` | 998-1040 | the page pins assert source order, not behaviour | Info (IN-05 idea, owner's call) | a regression of the windows is seen by the probes, not by the gate |

No TBD, FIXME, XXX, TODO or HACK in `app.js`. WR-10 no longer applies; the prior report's warning row is gone.

### Known debt that bears on the goal (unchanged)

Filed under `docs/tech_debt/active/`; none breaks a success criterion on the sizes the goal names: first ubuntu
dispatch of `pair.yml` (must), `screw pair` exit codes 1 and 2 collide with failure exits (must), fillet ring can
overhang the head flats (must), the countersink-cutter and lead-in-gate items (must), interim nut bounds, the
unpurchased ISO standards. IN-07 (the nut narrow-s test band) is open in the review disposition: a test gap with no
defect found, outside the page.

### Human Verification Required

The owner's end-of-phase items (also in the frontmatter). The code and my headless runs agree with the expected
results; no human has looked at the final build.

1. **UAT test 1 on the final build.** `make serve`, kind nut, clearance empty, pick ISO 4032 then M6. Expected:
   selects hold, fields M6 (d 6, pitch 1, s 10, m 5.2), nothing builds, the one error is the missing clearance.
   Why human: the owner reported this as failed (G-05-1) and the browser is not in the gate (L01).
2. **UAT test 3 on the final build.** Type 0.1 on the nut, Matching bolt, Matching nut. Expected: the nut opens at
   0.1 and builds. Also type 0.1, Reset, switch to the bolt and confirm its Matching nut link carries no clearance.
   Why human: the owner reported this as failed (G-05-3).
3. **WR-09 / WR-10 in a real browser (updated for 05-25).** Block `api/schema?kind=nut` in devtools and switch Kind
   to nut; then throttle and switch; then follow Matching nut and press Back during the load. Expected: blocked, the
   page shows nothing of the bolt (no controls, panel rows, Matching link, download hrefs, picker, badge, status),
   one message `Could not load the part: ...`, Kind deselected, and picking nut again opens the nut; throttled, no
   old control, panel or link on screen while the nut loads and no console error; Back reopens the bolt whole and it
   builds. Why human: the windows are one localhost request long, and a real browser's network error text and the
   real select's change behaviour are only visible there.

### Gaps Summary

No gaps. The prior report's one recorded warning (WR-10) and info (IN-08) are closed in code, in the page pins and in
a headless browser, and nothing regressed. The phase waits only on the owner's browser confirmation (three items
above) and on moving the eight `Gaps Found` rows of REQUIREMENTS.md to Complete afterwards.

---

_Verified: 2026-10-22T10:00:00Z_
_Verifier: Claude (gsd-verifier)_
