---
phase: 05-hex-nut-and-kernel-pair-proof
verified: 2026-10-21T08:15:00Z
status: human_needed
score: 6/7 must-haves verified
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
  - Makefile
  - bench/RESULTS.md
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
covered_digest: "v3:sha256:6ad99eb6dcff5f8789037c7db20844785a3a14c95bac643569228a692fa67b47"
overrides_applied: 0
behavior_unverified: 1
behavior_unverified_items:
  - truth: "The page (UI) lets a user pick an ISO 4032 nut preset, leaves the nut's clearance empty with no default, shows the matching-part link, drops the mesh on a kind switch, and shows the pair rows and the M18 note"
    test: "Serve the app (`make serve`), open the page, choose kind nut, pick a preset (e.g. ISO 4032 M6), leave clearance empty, then type 0.1; follow the 'Matching bolt' link, then the 'Matching nut' link on the bolt; switch kinds with a mesh on screen; pick (M18) and read the panel"
    expected: "Empty clearance field blocks a build and shows no stale part; typing 0.1 renders the nut and a Pair group with radial 0.1 mm and diametral 0.2 mm, nut major/pitch/minor diameters and 5.2 turns; the 6g/6H limits group carries the label 'limits for a bought part; this model is nominal and not toleranced'; the counterpart link round-trips d, pitch and hand; a kind switch drops the previous mesh; M18 shows 'kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)' and no kernel call is made"
    why_human: "No browser exists in the gate (L01); 05-UI-REVIEW.md is code-only with no screenshots and 05-VALIDATION.md lists this check as manual-only for TYPE-04 and PAIR-01. Source assertions and the API/CLI info documents (which I ran) show the data is right; they cannot show the page renders and switches state correctly"
human_verification:
  - test: "Page walk-through of the nut UI (see behavior_unverified_items): preset pick, empty clearance, matching-part link both ways, kind switch, pair rows, 6H/6g limits label, M18 note, live 3D preview of a nut and its STL/STEP buttons"
    expected: "As stated above; the 3D preview shows a hex nut with a lead-in countersink and chamfered faces, and the download buttons name the quality ('preview' in the preview STL's filename)"
    why_human: "Rendered browser behaviour, not exercised by any test or by the UI audit"
---

# Phase 5: Hex Nut and Kernel Pair Proof Verification Report

**Phase Goal:** For any bolt a user can get the matching ISO 4032 nut at a chosen radial clearance, see the pair's numbers on the info panel, and get a kernel verdict on whether the pair mates, one that cannot report `proven` when its own control did not fire.
**Verified:** 2026-10-21T08:15:00Z
**Status:** human_needed
**Re-verification:** No, initial verification (HEAD e7ac42e; code and tests unchanged since eeb49b5, only 05-SECURITY.md differs)

## Verdict in one paragraph

The goal is achieved in the codebase on every path that can be exercised without a browser. I ran the real
CLI proof on M6 (`proven`, exit 0, controls at 12.2130 mm3 against a closed form of 12.2130) and on M18
(`inconclusive`, exit 2, "control at theta -2.0944 reads empty (closed form 336.632 mm3)"), served the nut
through the API (info, preview STL, fine STL, STEP, hand, missing-clearance 422), fed the verdict rule five
planted control readings (it refused `proven` for an empty, NaN, off-band and all-empty control), and ran
the pair, CLI-pair and import-boundary tests (150 passed) plus end-oracle, mesh, parity, presets and calc
tests (677 passed). The one open item is the rendered page, which no test or audit has looked at; it is the
single reason the status is `human_needed` and not `passed`. No truth FAILED.

## Goal Achievement

### Observable Truths (ROADMAP success criteria, none dropped; plan must-haves add detail)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: an ISO 4032 nut M2-M20 from a preset or mm fields on the API and CLI; matching part both ways from the same d, pitch, hand; lead-ins; parity green | VERIFIED | `screw presets nut` returns 14 rows (M2..M20, no M7), each citing its GOST ISO 4032-2014 table; the M6/M8/M10/M12/M16/M20 s and m equal the ISO 4032 values I know. `/api/nut/info`, `/api/nut/model.{stl,step}` return 200 (preview 335 KB, fine 2.3 MB, STEP 626 KB, left-hand 200). `counterpart` is on the nut and the bolt info (`{'kind': 'nut', 'fields': {'d': 8.0, 'pitch': 1.25, 'left_hand': False, 's': 13.0, 'm': 6.8}}` from an M8 bolt). Lead-ins: `solid/nut.py` `countersink`/`face_chamfer` on both faces, `solid/__init__.py` tip cone and fillet gates. `tests/test_parity.py` and `tests/test_presets.py` pass. The M2-M4 "informative" label is amended away (L14, owner ruling 2026-10-20, ROADMAP SC1 text records it) |
| 2 | SC2: `clearance` is radial mm, positive enlarges the nut thread, no default; panel shows the INFO-01 set and the 6g/6H limits under the required label | VERIFIED | `/api/nut/info` without `clearance` is a 422 `Field required`; the CLI help reads `[required]`. Info rows at c = 0.1, M6: radial 0.1, diametral 0.2, nut major 6.2, pitch diameter 5.5505, minor 5.1175, engagement 5.2 turns, flank gap 0.05 (= c sin 30), axial play 0.1155 (= 2c tan 30). 6H limits D1 4.917-5.153, D2 5.350-5.500 equal the ISO 965-2 6H M6 figures; group name is exactly "limits for a bought part; this model is nominal and not toleranced"; each label says derived and names both GOST sources. `tests/test_nut.py::test_a_positive_clearance_moves_the_nut_thread_away_from_the_axis_on_both_hands` exists and passes under `make verify` |
| 3 | SC3: `screw pair` and the solid function return `proven \| violated \| inconclusive` with the control; an empty control is `inconclusive` naming pose and clearance, never `proven`; c <= 0 inconclusive; both hands; one size in `make verify`; full grid in CI against pre-registered verdicts | VERIFIED | Behavioural, not presence. Real kernel: `screw pair nut --d 6 --pitch 1 --s 10 --m 5.2 --clearance 0.1` gave `proven`, exit 0, three matched poses 0 solids, three controls 12.21304/12.21304/12.21299 mm3 against closed form 12.21303. `screw pair nut --d 18 --pitch 2.5 --s 27 --m 15.8 --clearance 0.1` gave `inconclusive`, exit 2, reason "control at theta -2.0944 reads empty (closed form 336.632 mm3)", the other two controls 336.630 and 336.630. Rule fed planted readings (`calc/pair.py` `cell_judgement`): all fire gives proven; one empty, one NaN, one 1 % off band, all empty each give inconclusive. Source: `proven` requires every matched pose empty AND every control non-empty within `PAIR_BAND`, with NaN refused (negated comparisons) and the nut body checked against its closed form. `prove()` reads nothing at c <= 0 and at c >= d/2. Tests `test_an_empty_control_at_any_pose_is_inconclusive_and_names_that_pose` (both hands, three poses), `test_the_verify_cell_is_proven_as_pre_registered` (in `make verify`; ubuntu reading `proven`, 167.5 s, CI run 39431329111 per 05-15) pass. The expected table `tests/data/pair_expected.tsv` was added in 5d90f3e (PR #17, 2026-10-14), six days before the 2026-10-20 grid run; `bench/RESULTS.md` "Pair tier (Phase 5, D-07)": 240 of 240 equal, 88 proven / 60 violated / 92 inconclusive, M18 has 0 proven |
| 4 | SC4: the pair proof is not an API endpoint; API/UI show closed-form flank gaps; import-linter forbids `app` and `pool` importing the pair module | VERIFIED | `app.routes` has no `pair` path and `GET /api/pair/nut` is 404; `flank_gap` and `axial_play` rows are on the info document. `make lint-imports`: 10 contracts kept, 0 broken, including "The serving process and its workers never import the pair proof" (`source_modules = [screw.app, screw.pool]`, `allow_indirect_imports = false`), with a runtime half in `tests/test_import_boundaries.py` (passes) |
| 5 | SC5: STL and STEP from the same modelled-thread solid; STL chord deviation explicit, measured against the clearances, cited in a decision entry; `ControlSurfaceDeflection` on for downloads | VERIFIED | `solid/__init__.py` `_write_export` meshes a copy of the one built solid for STL and writes STEP from the same shape; `TESSELLATION["fine"] = (0.01, 0.1)`; `bench/RESULTS.md` "Mesh deviation (Phase 5, D-21)": rule committed in c87aadf before the rows, worst 0.0161 mm against a 0.025 mm bound (R6: 0.5 of the 0.05 mm proof clearance); `tests/test_mesh.py` pins `ControlSurfaceDeflection is True` and the preset (pass); decision log L15. Caveat: the pin asserts the OCP default holds, it does not set the flag |
| 6 | SC6: the M18 empty control is diagnosed in one bounded task whose method was committed first; finding recorded; no verdict rule changed; M18 ships, reads `inconclusive`, panel labels M18 from the cited record | VERIFIED | `05-M18-DIAGNOSIS.md` landed on main in PR #17 before the probe; `bench/RESULTS.md` "M18 control diagnosis": 36 of 36 readings built, the empty reproduced in 10 of 10 fresh processes on both hands, H1/H3/H4/H harness controls held, H2 not held (recorded as such, nothing re-run). `calc/pair.py` constants unchanged from the spike (`tests/test_pair.py::test_the_moved_constants_have_the_values_the_spike_registered`). `screw info nut --d 18 --pitch 2.5 --s 27 --m 15.8 --clearance 0.1` carries the note "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)" without calling the kernel; the live proof above is `inconclusive` |
| 7 | The page (UI): preset pick, empty clearance with no stale part, matching-part link, kind switch, pair rows and M18 note render and behave | PRESENT_BEHAVIOR_UNVERIFIED | `static/app.js` has `showCounterpart` (builds `#kind=...&fields` link, text "Matching <kind>"), an empty-clearance guard (line ~280, "never shown as the last valid part"), `showCounterpart(null)` on kind change; `index.html` has `#counterpart`. 05-UI-REVIEW.md scored 24/24 from code only, no screenshots. 05-VALIDATION.md lists this as manual-only. No test drives a browser. Routed to human verification |

**Score:** 6/7 truths verified (1 present, behavior-unverified)

The behavior-dependent truth (3, cancellation of `proven` when a control is empty) was upgraded to VERIFIED by
named tests and by two real-kernel runs, not by symbol presence.

### Deferred Items

None. PAIR-02 (the default clearance) is Phase 6 by REQUIREMENTS.md and ROADMAP and is correctly not claimed here.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/screw/calc/pair.py` | kernel-free pair rule | VERIFIED | 244 lines, no kernel import (`test_the_pair_rule_module_loads_no_kernel`), used by `solid/pair.py` and the spike |
| `src/screw/solid/pair.py` | bodies, `prove()`, report | VERIFIED | 352 lines, wired from `cli.cmd_pair`; `_KEEP`/`os._exit` teardown handled |
| `src/screw/solid/nut.py` | hex prism less L11 void, countersinks, face chamfers | VERIFIED | built and meshed through the API in both hands |
| `src/screw/solid/bolt.py` + `solid/__init__.py` | tip cone, under-head fillet, gates | VERIFIED | gates `piece_refusal` on tip cone and fillet ring; `test_end_oracles.py` passes |
| `src/screw/tables/iso4032.py`, `gost16093.py`, `iso724.py` | cited rows, derived limits | VERIFIED | 14 rows; derived 6H M6 limits match ISO 965-2 |
| `src/screw/cli.py` `pair` | subcommand, exit codes 0/1/2 | VERIFIED | run live; collision of codes 1/2 with failure exits is filed debt |
| `tests/data/pair_expected.tsv` | 240 pre-registered verdicts | VERIFIED | added before the run (5d90f3e vs 22bcd50) |
| `.github/workflows/pair.yml`, `make pair` | slow tier | VERIFIED (not yet run on ubuntu) | `workflow_dispatch` + weekly, no PR trigger; first ubuntu grid run is filed debt |
| `bench/RESULTS.md` entries | recorded runs | VERIFIED | M18 diagnosis, pair tier, product cells, mesh deviation, nut fine caps |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli.cmd_pair` | `solid.pair.prove` | lazy import, `os._exit(PAIR_EXIT[verdict])` | WIRED | ran live |
| `solid.pair.prove` | `calc.pair.cell_judgement` | `_record` then judge | WIRED | verdict and `closed_control` come from the rule, not recomputed |
| `solid.pair.prove` | shipped bolt/nut | `_shipped`, `counterpart_for` | WIRED | evidence only, shown zero solids at all three poses for M6 |
| `app` / `pool` | `solid.pair` | forbidden | NOT IMPORTED (intended) | import-linter + runtime probe |
| nut info document | `calc` pair rows, limits, counterpart | `derive()` | WIRED | rows printed above |
| `static/app.js` | `info.counterpart` | `showCounterpart` | WIRED in source; rendering unverified | human item |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| Nut info panel | pair rows, nut diameters, limits | `calc` closed forms and `tables` rows | yes (values checked against hand arithmetic and ISO figures) | FLOWING |
| `PairReport.readings` | volumes, solids | `BRepAlgoAPI_Common` on the built rod and blank | yes (non-zero controls, zero matched) | FLOWING |
| Page counterpart link | `info.counterpart` | API info JSON | yes in the API; page not rendered | see human item |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| M6 pair proof | `screw pair nut --d 6 --pitch 1 --s 10 --m 5.2 --clearance 0.1` | proven, exit 0, 57 s | PASS |
| M18 pair proof | `screw pair nut --d 18 --pitch 2.5 --s 27 --m 15.8 --clearance 0.1` | inconclusive, exit 2, empty control named | PASS |
| Rule refuses `proven` on bad controls | scratch script over `cell_verdict` | empty, NaN, off-band, all-empty all inconclusive | PASS |
| Nut over the API | TestClient with lifespan | info 200, 422 without clearance, STL preview/fine, STEP, left-hand 200, `/api/pair/*` 404 | PASS |
| Pair, CLI-pair, import boundaries | `pytest tests/test_pair.py tests/test_cli_pair.py tests/test_import_boundaries.py --no-cov` | 150 passed, 240 grid cells deselected, 127 s | PASS |
| Ends, mesh, parity, presets, calc | `pytest tests/test_end_oracles.py tests/test_mesh.py tests/test_parity.py tests/test_presets.py tests/test_calc.py --no-cov` | 677 passed, 21 s | PASS |
| Import contracts, unfinished-work scan | `make lint-imports no-fake-done` | 10 kept, 0 broken; scan rc 0 | PASS |
| Full gate | not re-run; orchestrator `make verify` at eeb49b5: 3460 passed, exit 0; HEAD differs only by 05-SECURITY.md | accepted | PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared by the phase. The phase's own probes (`bench/m18_probe.py`,
`bench/end_cuts.py`) are recorded runs, read in `bench/RESULTS.md`; I did not re-run them. SKIPPED.

### Requirements Coverage

All nine IDs in the task are claimed by at least one PLAN's `requirements:` frontmatter, and REQUIREMENTS.md
maps each to Phase 5, marked Complete. PAIR-02 maps to Phase 6 (Pending) and is not claimed by any Phase 5
plan. No orphans.

| Requirement | Source plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| TYPE-03 | 05-02, 04, 05, 06, 07, 13, 18, 19, 20 | ISO 4032 hex nut with chamfers | SATISFIED | 14 cited rows, nut builds on API/CLI, tests in `test_tables.py`, `test_nut.py`; M2-M4 informative label amended by L14 and the owner |
| TYPE-04 | 05-10, 05-18 | matching part from the same d, pitch, hand (and clearance) | SATISFIED (page unverified) | `counterpart` on both kinds, `test_parity` same-counterpart test. Bolt-to-nut link carries no clearance because a bolt has none; the nut opens with the field empty (D-01/D-02) |
| THRD-05 | 05-02, 11, 12, 13, 18, 20 | lead-in chamfers, tip, fillet | SATISFIED | tip cone (GOST 12414-94), fillet ring, nut countersinks, gated by piece, watertight sweeps |
| PAIR-01 | 05-04, 05, 09, 10, 18 | one radial `clearance` on the nut | SATISFIED | required, no default, radial and diametral on the panel |
| PAIR-03 | 05-01, 03, 05, 09, 14, 15, 16, 18, 20 | kernel check with control, never proven on an empty control | SATISFIED | live runs, planted-reading checks, 240/240 grid |
| PAIR-04 | 05-01, 03, 14, 15, 16, 18, 20 | solid function, `screw pair`, slow tier, not an endpoint | SATISFIED | CLI, `make pair`, `pair.yml`, import contract. First ubuntu grid run unrecorded (debt) |
| INFO-01 | 05-02, 06, 07, 08, 09, 18 | numbers from pure maths, no kernel | SATISFIED | `screw info nut` prints them; "serving process never imports the kernel" contract kept |
| INFO-02 | 05-02, 08, 09, 18 | 6g/6H limits with the label | SATISFIED | derived values and exact label confirmed (amended source per L14) |
| FRNT-06 | 05-02, 17, 18 | same solid for STL/STEP, explicit recorded chord deviation | SATISFIED | RESULTS entry, `test_mesh.py`, L15 |

### Anti-Patterns Found

None blocking. TBD/FIXME/XXX scan over `src tests bench Makefile .github` finds nothing unreferenced;
`make no-fake-done` exits 0.

### Known debt that bears on the goal (reported as such, not hidden gaps)

All filed under `docs/tech_debt/active/`, none breaks a success criterion on the sizes the goal names:

| Item | Bearing |
|------|---------|
| `2026-10-14-first-pair-yml-dispatch.md` (must) | The full 240-cell grid has run on macOS arm64 only; the ubuntu per-size times and verdicts are unrecorded because `pair.yml` can be dispatched only from `main`. SC3 asks for the CI job to exist and to assert against the pre-registered table, which it does; the run on ubuntu is the next step after merge |
| `2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md` (must) | `violated` = 1 and `inconclusive` = 2 are also a crash and a refused parameter. The JSON on stdout is the discriminator today. Does not make a `proven` untrue (only exit 0 is `proven`) but a script that trusts the code alone could misread; owner decision before Phase 6 |
| `2026-10-21-fillet-ring-can-overhang-the-head-flats.md` (must) | A bolt with s barely above d can carry a fillet wider than its head with no warning. An L02 near-miss (silent geometry), off the ISO rows |
| `2026-10-21-nut-countersink-cutter-crosses-the-axis-at-a-coarse-pitch.md` (must), `2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md` (must) | The model accepts a nut the kernel then refuses with an error naming no field. Tool refuses rather than serves a wrong part (L02-safe); no ISO 262 coarse size is affected |
| `2026-10-14-nut-interim-bounds.md`, `2026-10-20-iso-standards-not-purchased.md` | Bounds are interim until Phase 7; table sources are GOST texts by owner decision L14, the ISO purchase is debt |
| 05-REVIEW.md | 7 findings fixed (WR-01 to WR-06, IN-01), 3 deferred to debt (IN-02 to IN-04), open 0 |

### Housekeeping note

`.planning/ROADMAP.md` line 30 still shows Phase 5 unticked (`- [ ]`) although the phase section reads
20/20 plans executed. It is for the orchestrator to flip at completion; it does not bear on the goal.

### Human Verification Required

#### 1. The nut page in a browser

**Test:** `make serve`, open the page; choose kind nut; pick ISO 4032 M6; leave clearance empty, then enter 0.1; follow "Matching bolt", then "Matching nut" on the bolt; switch kinds with a mesh on screen; pick (M18) and read the panel; toggle the left-hand box.
**Expected:** An empty clearance builds nothing and shows no stale part. At 0.1 the nut renders with its lead-in countersink and chamfered faces, and the panel shows a Pair group (0.1 radial, 0.2 diametral, 6.2 / 5.5505 / 5.1175 mm, 5.2 turns, flank gap 0.05), plus the 6H limits group under its exact label. Links round-trip d, pitch and hand. A kind switch drops the previous mesh. M18 shows the "kernel pair proof inconclusive at K = 3" note. Preview and fine STL buttons name their quality.
**Why human:** no browser in the gate; the UI audit was code-only and the validation plan marks this check manual-only.

### Gaps Summary

No gaps. Every roadmap success criterion is met on the API and CLI, and the headline guarantee (the verdict
cannot be `proven` when a control read empty) holds against the real kernel and against planted readings.
Phase 5 is ready to proceed once the owner has looked at the page, and the first ubuntu dispatch of
`pair.yml` after merge is the filed follow-up for platform confidence.

---

_Verified: 2026-10-21T08:15:00Z_
_Verifier: Claude (gsd-verifier)_
