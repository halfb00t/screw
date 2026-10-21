---
phase: 05-hex-nut-and-kernel-pair-proof
verified: 2026-10-21T12:10:00Z
status: gaps_found
score: 19/20 must-haves verified
covered_files:
  - .github/workflows/pair.yml
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
covered_digest: "v3:sha256:9429d998c1c37ccccc050694ec8c2dfcbc98cbdab2dfb571ad66c84c2f5140a5"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 6/7
  gaps_closed:
    - "G-05-1: with an empty clearance the nut preset picks hold (plan 05-21), re-run in a real browser"
    - "G-05-3: the bolt's Matching nut link carries the clearance last typed (plan 05-22), re-run in a real browser"
  gaps_remaining:
    - "WR-07: the typed-clearance memory is keyed by the wrong kind during a kind switch"
  regressions:
    - "05-22 truth 3 and the L15 amendment: 'the value never enters the bolt's hash' is false on the WR-07 path"
gaps:
  - truth: "05-22 must-have 3 and the L15 amendment of 2026-10-21: the remembered clearance never reaches the bolt (not its hash, a bolt request or a download link); with it, must-have 1 (type 0.1 on a nut, follow Matching bolt, then Matching nut: the nut opens at 0.1 and builds)"
    status: failed
    reason: "rememberTyped keys the memory by currentKind, which is assigned only after await loadPresets() in navigate(), while buildForm() has already put the new kind's form on screen. A clearance typed in that window is stored under the old kind ('bolt'). The nut's memory misses it, and the nut page's Matching bolt link is built from lastTyped.get('bolt'), so it reads #kind=bolt&clearance=0.1&... . Following it puts the clearance in the bolt's hash and navigate() refuses the link: 'Unknown field \"clearance\" for kind \"bolt\"'. Nothing clears the entry, because every bolt field has a default and so never writes the memory: the nut's Matching bolt link stays broken for the rest of the page session. Reproduced in a headless browser (see Behavioral Spot-Checks). The window is one request on localhost, so it is narrow, but it breaks the stated invariant and the failure is persistent once hit. It fails closed: no wrong part is built, no bolt API request carries the value, and the refusal names the field."
    artifacts:
      - path: "src/screw/static/app.js"
        issue: "rememberTyped (lines 678-686) uses currentKind (assigned at line 315); buildForm (line 87) replaces the form and defaults earlier, so the key and the form disagree for the length of loadPresets"
    missing:
      - "Key the memory by the kind the form was built for: set a formKind in buildForm in the same synchronous block as defaults, clear it in clearForm, and use it in rememberTyped (05-REVIEW.md WR-07 gives the patch)"
      - "A source pin that lastTyped.set( is keyed by formKind, not currentKind (05-REVIEW.md IN-05 asks for the pin); and a guard in rowOfFields for a control the form lacks (IN-06, same window, same cause)"
      - "Owner re-run of UAT test 3 after the fix"
  - truth: "05-22 plan prose, UI-SPEC rule 37 and the code comment at app.js:675-677: 'a link never carries an empty or stale number'"
    status: partial
    reason: "Only an input event touches the memory. Reset empties the clearance field without an event, and a link or Back writes the hash value into it without one. Reproduced in a headless browser: type 0.1 on a nut, press Reset (field empty, nut does not build), switch to the bolt; its Matching nut link is #kind=nut&clearance=0.1&... and opens a nut at a clearance the user cleared. This follows the owner's literal ruling (0.1 is the clearance last typed on a nut, the value is the user's own, the nut shows it when it opens, nothing is invented), so it is not an L02 silent change and no listed truth fails on it. It does contradict the word 'stale' in the plan, rule 37 and the code comment, and rule 37 names Reset as a non-writer, not as a non-clearer. Partial, not a blocker. The owner should pick: make Reset (and a link that overwrites with a different value) forget the entry, or amend the wording to 'the clearance last typed'."
    artifacts:
      - path: "src/screw/static/app.js"
        issue: "Reset handler (lines 698-701) and navigate's write loop (line 325) change a field with no default without updating lastTyped; showCounterpart (line 428) reads it"
    missing:
      - "Either forget the entry when Reset or a link overwrites it (05-REVIEW.md WR-08 gives forgetUntyped), or amend rule 37, the code comment and the L15 amendment to say the link carries the clearance last typed even after Reset or a link replaced it"
---

# Phase 5: Hex Nut and Kernel Pair Proof Verification Report

**Phase Goal:** For any bolt a user can get the matching ISO 4032 nut at a chosen radial clearance, see the pair's numbers on the info panel, and get a kernel verdict on whether the pair mates, one that cannot report `proven` when its own control did not fire.
**Verified:** 2026-10-21T12:10:00Z
**Status:** gaps_found
**Re-verification:** Yes, after gap closure plans 05-21 (G-05-1) and 05-22 (G-05-3). HEAD 53988f4. Since the prior report (e7ac42e) only `src/screw/static/app.js` and `tests/test_parity.py` changed under `src/`, `tests/`, `Makefile`, `pyproject.toml`, `bench/` and `.github/`. The kernel, calc, tables and API are untouched, so the prior kernel evidence (M6 `proven`, M18 `inconclusive`, planted-reading checks, 240 of 240 grid cells) stands, and I ran a regression sample on top of it.

## Verdict in one paragraph

The phase goal is achieved: the nut, the pair numbers and the kernel verdict all work, and the verdict still cannot
be `proven` when a control did not fire. Both UAT gaps are closed and I re-ran their two tests in a real headless
browser: with an empty clearance, ISO 4032 then M6 stays picked and nothing builds (G-05-1); a clearance typed on a
nut rides the bolt's Matching nut link and the nut opens at 0.1 and builds (G-05-3). The status moves from
`human_needed` to `gaps_found` for one reason. The 05-22 change breaks one of its own stated invariants on a narrow
path (WR-07, below): the remembered clearance can reach the bolt's hash, and the nut's Matching bolt link is then
refused for the rest of the page session. It fails closed and the trigger is a keystroke inside the one-request
window after a kind switch, so no success criterion fails on the ordinary path. A contradicted must-have is a gap
all the same, and the fix is a few lines of page code. WR-08 is a second, softer divergence and is recorded as partial.

## Decision on WR-07 and WR-08

- **WR-07 defeats a 05-22 must-have truth** (truth 3, "never reaches the bolt: not its hash", and the L15 amendment that repeats it), and with it truth 1 on that path. I reproduced it, so this is not read from the review alone. It does not defeat a roadmap success criterion: SC1's "matching part both ways from the same d, pitch, hand" holds on every path except a clearance typed before the kind switch has finished loading, and the broken link refuses whole with a message naming the field (L02-safe). So: gap, but not a phase-goal failure. 05-UI-REVIEW.md rates it BLOCKER and 05-SECURITY.md judges it fail-closed; both are right about different things. Fail-closed means no wrong part. It does not mean the invariant holds.
- **WR-08 does not defeat a listed must-have.** It follows the owner's ruling read literally, and rule 37 says Reset does not write the memory. It contradicts the "no stale number" wording, so it is a partial gap and an owner choice (fix the code or amend the words).

## Goal Achievement

### Observable Truths

Roadmap success criteria SC1 to SC6, none dropped; the page truth from the first report; then the must-haves of 05-21 (A) and 05-22 (B).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: ISO 4032 nut M2-M20 from a preset or mm fields on API and CLI; matching part both ways from the same d, pitch, hand; lead-ins; parity green | VERIFIED | Unchanged since the prior report. `tests/test_presets.py`, `tests/test_nut.py`, `tests/test_mesh.py`, `tests/test_import_boundaries.py` re-run: 480 passed. The page half of "both ways" is covered by truths B1 and B3 |
| 2 | SC2: `clearance` is radial mm, positive enlarges the nut thread, no default; panel shows the INFO-01 set and the 6g/6H limits under the required label | VERIFIED | Unchanged (calc and API untouched). In the browser the nut with clearance empty makes zero `model.stl` requests (A1) |
| 3 | SC3: `proven \| violated \| inconclusive` with the control; an empty control is `inconclusive`, never `proven`; c <= 0 inconclusive; both hands; full grid pre-registered | VERIFIED | Unchanged (no change under `calc/pair.py`, `solid/pair.py`, `cli.py` since the prior report, which ran the real kernel and planted readings). `tests/data/pair_expected.tsv` and `bench/RESULTS.md` unchanged |
| 4 | SC4: the pair proof is not an API endpoint; import-linter forbids `app` and `pool` importing it | VERIFIED | `make lint-imports`: 10 contracts kept, 0 broken |
| 5 | SC5: STL and STEP from the same solid; chord deviation explicit and recorded; `ControlSurfaceDeflection` on | VERIFIED | Unchanged; `tests/test_mesh.py` passes |
| 6 | SC6: the M18 empty control diagnosed in one bounded task; no verdict rule changed; M18 ships `inconclusive` | VERIFIED | Unchanged; UAT test 5 (owner, browser) passed the M18 note |
| 7 | The page: preset pick, empty clearance with no stale part, matching-part link, kind switch, pair rows, M18 note render and behave | VERIFIED | Owner UAT 2026-10-21: tests 2, 4, 5, 6 passed in a browser; tests 1 and 3 failed and are the two gaps, now re-run below. Previously PRESENT_BEHAVIOR_UNVERIFIED; the owner's UAT plus my probe now exercise it. The owner's own re-run of tests 1 and 3 on the fixed build is still the end-of-phase confirmation |
| A1 | 05-21: kind nut, clearance empty, ISO 4032 then M6 leaves the selects on ISO 4032 / M6, fields at d 6 pitch 1 s 10 m 5.2, 422 missing clearance, nothing builds | VERIFIED | My headless probe: opening `#kind=nut` showed selects `["ISO 4032","M6"]`; picking ISO 4032 then M6 gave `["ISO 4032","M6"]`, fields `d 6, pitch 1, s 10, m 5.2, clearance ""`, 0 `model.stl` requests, empty status. Before the fix the SUMMARY records the same probe failing at exactly the three predicted steps |
| A2 | 05-21: after a failed update the selects show the first catalogue row whose every field the form holds exactly, else blank; the server's rule and order | VERIFIED | `rowOfFields()` (app.js:199-204) uses `Number(held) === value`, `held !== ''`, first row in catalogue order, no tolerance. Pinned by `test_after_a_failed_update_the_selects_show_the_row_the_fields_hold_exactly` (passes). Caveat IN-06: `fields.get(name).input` is unguarded while the catalogue can belong to the previous kind (same window as WR-07); a console error, not a wrong part |
| A3 | 05-21: the badge reads only an info document; `presetBasis` set only by a pick or an exact info document | VERIFIED | `showMatch`: `if (preset === null) badge.textContent = ''`; `presetBasis` assigned only in `pick` and the `exact` branch |
| A4 | 05-21: a successful info document drives selects and badge from `info.preset` exactly as before | VERIFIED | The `exact` branch still finds the row by `preset.id`; the `rowOfFields` path is taken only for `preset === null` |
| A5 | 05-21: the diagnosis was reproduced before the fix; RED and GREEN outputs in the SUMMARY | VERIFIED | 05-21-SUMMARY.md lines 105 (`RESULT FAIL` with three steps) and 131 (`RESULT PASS []`); the missing RED exit code is disclosed |
| A6 | 05-21: 01-UI-SPEC.md amended; the browser test in the gate is filed as an idea | VERIFIED | UI-SPEC amendment note dated 2026-10-21 (plan 05-21) present; `docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md` exists and has its INDEX row |
| B1 | 05-22: type 0.1 on a nut, follow Matching bolt, then Matching nut: the nut opens at 0.1 and builds; the link reads `#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2` | VERIFIED (normal path; fails on the WR-07 path, see B3) | My probe: typed 0.1 on the M6 nut (one `model.stl` request); bolt link `#kind=bolt&d=6&pitch=1&left_hand=false&s=10&k=4`; after Matching bolt, the nut link read exactly `#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2`; following it left clearance `0.1` and a second nut `model.stl` request |
| B2 | 05-22: with nothing typed the link is as before and the nut opens empty and builds nothing; typing the field empty forgets the value; nothing invented | VERIFIED | With nothing typed the link read `#kind=nut&d=6&pitch=1&left_hand=false&s=10&m=5.2`. `rememberTyped` deletes the entry on `value === ''`. No default is introduced |
| B3 | 05-22: the remembered value never reaches the bolt: not its hash, a bolt request, a download link, never the bolt API; page memory only | FAILED | Bolt API, requests and downloads: never carry it (the auditor's probe and the source: `lastTyped` is read only at app.js:428). The bolt's hash: reached on the WR-07 path. Reproduced: kind switched to nut with the nut catalogue request held back, 0.1 typed inside the window, 0.2 retyped after load. The nut's Matching bolt link read `#kind=bolt&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&k=4`; clicking it put that in the URL and the page answered `Unknown field "clearance" for kind "bolt"`. See Gaps |
| B4 | 05-22: `PartInfo.counterpart` never carries `clearance`; calc, app.py, cli.py unchanged | VERIFIED | `git diff e7ac42e HEAD` over `src/` and `tests/` touches only `app.js` and `test_parity.py`; the contract test `test_a_bolts_matching_nut_link_with_a_typed_clearance_opens_a_nut_that_builds` passes with `tests/test_parity.py` (69 passed) |
| B5 | 05-22: app.js names no field or kind; the memory is generic; the server's fields win | VERIFIED | `{ kind, ...lastTyped.get(counterpart.kind), ...counterpart.fields }` at app.js:428; the naming test in `test_parity.py` passes |
| B6 | 05-22: L15 amendment in the same change; UI-SPEC rule 37 and the amended rule 34 | VERIFIED (text of the amendment is contradicted by B3 on the WR-07 path) | `docs/architecture/decision_log.md` carries the 2026-10-21 amendment naming G-05-3; UI-SPEC rule 37 and the dated note are present |
| B7 | 05-22: reproduced before the change, RED and GREEN outputs in the SUMMARY | VERIFIED | 05-22-SUMMARY.md line 118 (`RESULT FAIL`, two predicted steps) and 143 (`RESULT PASS []`) |

**Score:** 19/20 truths verified (0 present, behavior-unverified). The one failure is B3.

### Deferred Items

None. WR-07 and WR-08 are not addressed by Phase 6 or later. PAIR-02 (the default clearance) is Phase 6 by REQUIREMENTS.md and is correctly not claimed here.

### Advisory (New Scope, Unevidenced)

None. The two findings above are carried forward from 05-REVIEW.md and are evidenced by a reproduction.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/static/app.js` | `rowOfFields`, `lastTyped`, `rememberTyped`, composed counterpart link | VERIFIED for 05-21; WIRED WITH DEFECT for 05-22 | `rowOfFields` and the failed-update branch present and working in a browser. `lastTyped`/`rememberTyped` present, wired to the form `input` listener and `showCounterpart`, with the key defect of WR-07 |
| `tests/test_parity.py` | source pins and the link contract test | VERIFIED | 69 passed. They pin source text and cannot see WR-07 or WR-08 (IN-05) |
| `docs/architecture/decision_log.md` | L15 amendment | VERIFIED | present, dated, names G-05-3 |
| `01-UI-SPEC.md` | rules 32, 34, 35, 37 | VERIFIED | amendment notes present |
| `docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md` | owner decision filed | VERIFIED | file and INDEX row present |
| Phase 5 kernel, calc, tables, API, CLI artifacts | as in the prior report | VERIFIED | unchanged; regression sample passed |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `update()` `fail()` | `showMatch` | `showMatch(null)` | WIRED | still called on every failure |
| `showMatch` | `rowOfFields` | `preset === null ? rowOfFields() : undefined` | WIRED | line 185 |
| `rowOfFields` | `/api/presets` rows | `catalogue.rows`, `read()` | WIRED | live in the browser |
| form `input` | `rememberTyped` | `rememberTyped(e.target)` | WIRED, wrong key during a kind switch | WR-07 |
| `showCounterpart` | `lastTyped` | `lastTyped.get(counterpart.kind)` | WIRED | composed link observed |
| composed nut link | `/api/nut/info`, `model.stl` | navigate writes the hash, `partQuery` sends it | WIRED | nut built from the link in the browser |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| Picker selects after a failed update | `rowOfFields()` | `catalogue.rows` from `GET /api/presets?kind=` and the live form values | yes | FLOWING |
| Matching-part link | `lastTyped` + `info.counterpart` | the user's `input` events and the info document | yes, keyed wrongly on the WR-07 path | FLOWING (defect noted) |
| Nut info panel, `PairReport` | as the prior report | unchanged | yes | FLOWING |

### Behavioral Spot-Checks

Scratch Playwright probes against `screw serve` on port 8019 (spur's Playwright, headless shell; not in the repo, L01; the server is stopped). Probe files are in the session scratch directory.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| UAT 1: empty clearance, pick ISO 4032 then M6 | `probe.py` against `#kind=nut` | selects `[ISO 4032, M6]`, fields M6, 0 `model.stl` requests | PASS |
| UAT 3 (owner ruling): type 0.1, Matching bolt, Matching nut | `probe.py` | link `#kind=nut&clearance=0.1&d=6&pitch=1&left_hand=false&s=10&m=5.2`; nut opens at 0.1 and builds | PASS |
| WR-08 case 1: type 0.1, Reset, switch to bolt | `probe.py` | field empty after Reset; bolt's Matching nut link still `#kind=nut&clearance=0.1&...` | CONFIRMED (partial gap) |
| WR-07: type inside the kind-switch window, retype after load | `probe7.py`, nut catalogue request delayed 1.5 s | nut's Matching bolt link `#kind=bolt&clearance=0.1&...`; click gives `Unknown field "clearance" for kind "bolt"` | CONFIRMED (gap). The delay is mine, to make the window a person can hit; on localhost it is one request |
| Page source assertions | `pytest tests/test_parity.py --no-cov` | 69 passed | PASS |
| Nut, presets, import boundaries, mesh | `pytest tests/test_nut.py tests/test_presets.py tests/test_import_boundaries.py tests/test_mesh.py --no-cov` | 480 passed, 103 s | PASS |
| Import contracts | `make lint-imports` | 10 kept, 0 broken | PASS |
| Full gate | not re-run; the 05-22 SUMMARY records `make verify` on the final tree: 3463 passed, exit 0, and no `src/` or `tests/` file has changed since | accepted | PASS |

I did not re-run the real-kernel `screw pair` runs: nothing under `calc/pair.py`, `solid/` or `cli.py` changed since the prior report, which ran them.

### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared by the phase. SKIPPED.

### Requirements Coverage

All nine IDs are claimed by at least one PLAN's `requirements:` frontmatter (05-21 claims TYPE-03, 05-22 claims TYPE-04, the rest as in the first report), and REQUIREMENTS.md maps each to Phase 5, marked Complete. PAIR-02 maps to Phase 6 (Pending) and no Phase 5 plan claims it. No orphans.

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| TYPE-03 | 05-02, 04, 05, 06, 07, 13, 18, 19, 20, 21 | SATISFIED | 14 cited rows; the page picks them with an empty clearance (A1) |
| TYPE-04 | 05-10, 05-18, 05-22 | SATISFIED on every path but one; gap WR-07 | `counterpart` both ways on the API/CLI; on the page the link round-trips d, pitch, hand and the typed clearance (B1). The nut's Matching bolt link breaks on the WR-07 path (fails closed). The requirement itself holds (API and CLI both ways); only the page's nut-to-bolt link is affected, and only on that path |
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
| `src/screw/static/app.js` | 678-686 | memory keyed by `currentKind`, not the kind of the form on screen | Blocker for B3 (gap 1) | persistent broken Matching bolt link after a kind-switch keystroke |
| `src/screw/static/app.js` | 698-701, 325, 428 | Reset and links change the field, not the memory | Warning (gap 2) | the bolt's Matching nut link carries a clearance the nut no longer shows |
| `src/screw/static/app.js` | 199-204 | `fields.get(name).input` unguarded while the catalogue is the previous kind's | Warning (IN-06) | console error inside `fail` in the same window; not a wrong part |
| `tests/test_parity.py` | 687-708, 884-905 | tests pin source text; none runs the page | Info (IN-05) | cannot see WR-07 or WR-08; the browser test is the owner's open idea |

No unreferenced TBD/FIXME/XXX; `make no-fake-done` passed at the 05-22 gate.

### Known debt that bears on the goal (unchanged)

Filed under `docs/tech_debt/active/`; none breaks a success criterion on the sizes the goal names: first ubuntu dispatch of `pair.yml` (must), `screw pair` exit codes 1 and 2 collide with failure exits (must), fillet ring can overhang the head flats (must), the countersink-cutter and lead-in-gate items at coarse pitch or huge s (must), interim nut bounds and the unpurchased ISO standards.

### Human Verification Required (after the fix)

Not frontmatter items, because `gaps_found` takes precedence. The owner's end-of-phase re-run stands.

1. **UAT test 1 on the fixed build.** `make serve`, kind nut, leave clearance empty, pick ISO 4032 then M6. Expected: selects hold, fields M6, nothing builds, panel empty. My headless run agrees; no human has looked.
2. **UAT test 3 on the fixed build.** Type 0.1 on the nut, follow Matching bolt, then Matching nut. Expected: the nut opens at 0.1 and builds. Repeat after WR-07 is fixed with a kind switch and an immediate keystroke, and after Reset (per the WR-08 choice).

### Gaps Summary

Two page-only defects in plan 05-22's memory, both from tying the memory to the wrong lifecycle. WR-07 is a failed
must-have (the value can reach the bolt's hash; the nut's Matching bolt link breaks for the session; fails closed). The fix
is to key `rememberTyped` by a `formKind` set where the form is built; it also removes the cause of IN-06. WR-08 is
partial and needs an owner choice: forget on Reset/link, or reword rule 37, the comment and the L15 amendment. Both
fit one small closure plan that touches `app.js`, `tests/test_parity.py` and the two contract texts. No kernel, calc,
API or CLI work is needed, and no earlier truth regressed.

---

_Verified: 2026-10-21T12:10:00Z_
_Verifier: Claude (gsd-verifier)_
