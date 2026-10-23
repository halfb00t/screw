---
phase: 06-printed-pair-acceptance
verified: 2026-10-23T23:30:00Z
status: human_needed
score: 6/6 must-haves verified
covered_files:
  - ".planning/phases/06-printed-pair-acceptance/06-01-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-01-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-02-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-02-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-03-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-03-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-04-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-04-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-05-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-05-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-06-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-06-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-07-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-07-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-08-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-08-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-09-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-09-SUMMARY.md"
  - ".planning/phases/06-printed-pair-acceptance/06-10-PLAN.md"
  - ".planning/phases/06-printed-pair-acceptance/06-10-SUMMARY.md"
  - "bench/RESULTS.md"
  - "bench/print_rules.py"
  - "bench/results/phase-06/manifest-acceptance.tsv"
  - "bench/results/phase-06/print-run-1.tsv"
  - "bench/results/phase-06/print-run-2.tsv"
  - "docs/architecture/decision_log.md"
  - "src/screw/calc/__init__.py"
  - "src/screw/calc/printability.py"
  - "src/screw/params.py"
  - "tests/test_print_rules.py"
covered_digest: "v3:sha256:5001ef62d17946698fc6ba39c58cab71e8553f6f271f6607d79f7e7758d94164"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Run the page (dev server http://127.0.0.1:8000). Pick bolt preset ISO 4017 M3 x 6 (or any d < 4 or pitch < 0.7): the printability sentence shows under the info panel. Switch to the nut and pick a size outside M6 to M12: the D-09 sentence shows too. Pick ISO 4017 M8 x 16: neither sentence shows."
    expected: "Printability warning for M3 (naming d_min, P_min, run 06-print-run-2, L18); D-09 warning for a nut outside M6 to M12 (L17, run 06-print-run-1); no printability or D-09 warning for M8 x 16 (and for its matching nut at the default clearance)."
    why_human: "Visual rendering of the warning list on the page (plan 06-09 Task 2 human-check). The API documents the page renders were checked by curl and carry the right sentences; app.js showMessages/pendingWarnings route info.warnings to the page, but what the owner sees was not looked at."
---

# Phase 6: Printed Pair Acceptance Verification Report

**Phase Goal:** The owner holds a bolt and a nut printed from this tool at the default clearance that thread together by hand, and that default and the printability threshold come from a recorded printed test, not from a forum or vendor figure.
**Verified:** 2026-10-23
**Status:** human_needed (one pending visual check, below; no gaps)
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: the printed test's method, predictions and escape clause were committed before the first print, and every sample's pass or bind is recorded in the repo | VERIFIED | Protocol, strict reader and rules landed on main as PR A (#19, squash `16f7041`) before `646b07d` (run-1 manifest) and `3273e51` (run-1 record). `bench/results/phase-06/print-run-1.tsv` holds 60 rows, sha256 `f76753de...d725` (recomputed here, equals `RUN_1_SHA256`). Provenance caveat below: the owner reported in prose, Claude transcribed, owner confirmed. Stated in RESULTS and L17. |
| 2 | SC2: the default `clearance` is set once from the recorded result, one absolute-mm value, cited in a decision entry | VERIFIED | `src/screw/params.py` `NutParams.clearance = _free(0.15, ...)` with the L17 comment. `default_from` over the pinned run-1 record returns 0.15 (every size 3/3 from 0.15; M10 and M12 bind at 0.1 in 3/3; owner's 0.10 prediction was not borne out and was not an input). L17 cites run, digests, profile, owner's `permanent: accepted`. `test_the_shipped_clearance_default_is_the_one_run_1_reads` and `test_the_clearance_default_is_the_frozen_value_l17_records` pass. `/api/nut/info` returns clearance 0.15 / diametral 0.3 with none typed. |
| 3 | SC3: the owner printed a bolt and its matching nut at the default clearance and they thread by hand; kernel verdict `proven` | VERIFIED (owner testimony) | RESULTS "Acceptance pair (Phase 6, D-16)": `screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8` exit 0, `proven`, JSON recorded verbatim. `manifest-acceptance.tsv` names/bytes/sha256 equal the two STL files in `~/Downloads/3dprint`: I recomputed `30f2fca0...5814` (bolt) and `4c09af10...6324` (nut), both match. Owner's reply recorded verbatim, "Result: pass", print 21:53 2026-10-23. The pass itself is the owner's hand judgement (D-05); nothing mechanical sits behind it, which is what PAIR-05's "owner's manual acceptance" means. |
| 4 | SC4 (bought nut / PAIR-06) is struck and the deferral is recorded, not silently dropped | VERIFIED | ROADMAP SC4 struck with R9 note; REQUIREMENTS lists PAIR-06 and PAIR-07 under v2 and a traceability row `v2 (deferred)`; R9 in `06-OWNER-RULINGS.md` with the owner's quote; no "bought" in `bench/print_rules.py` or `bench/print_matrix.py`; no `undersize` anywhere in `src`. |
| 5 | SC5 / INFO-04: the printability threshold is a constant set from a recorded printed test, and parts below it get a warning citing the source on UI, API and CLI | VERIFIED, weaker evidence (see below) | `D_MIN_MM = 4.0`, `P_MIN_MM = 0.7`, `THRESHOLD_*` in `src/screw/calc/printability.py`; `test_the_printability_threshold_is_the_one_run_2_reads` re-derives both from the pinned run-2 record (sha256 `6c2d9240...923e`, recomputed, equals `RUN_2_SHA256`). `printability_warning` is appended by `_bolt` and `_nut` in `derive()` (key link present at `calc/__init__.py` lines 305, 416). Live API: bolt d3 p0.5 and nut d3 p0.5 carry the sentence naming d_min, P_min, run 06-print-run-2, L18; `screw info nut --d 3 --pitch 0.5` prints the same; bolt M8 x 16 and nut M8 x 16 pair carry none; nut d4 p0.7 (exactly at threshold) carries none of the printability sentence. It warns only, no cap, no 422 (D-13, L02; documented). 38 calc/parity printability tests pass. |
| 6 | L02: a parameter the user did not set never silently changes the part; a link omitting clearance and one typing 0.15 are the same part | VERIFIED | Default is a frozen literal with no lower bound; the two refusals unchanged; tests in `test_params.py` pass (2 clearance tests) and 06-06 SUMMARY coverage cites the equal-document test. The below-threshold path never trims `d` or `pitch`: curl of d3 p0.5 returns the warning and 200, not a refusal. |

**Score:** 6/6 truths verified (0 present-but-behavior-unverified)

### Judgement on INFO-04's evidence (R10), stated plainly

The requirement text is "the threshold is a constant set from the owner's printed test, not from vendor guides". That holds literally: the constants are M4's d and ISO 262 coarse pitch, read by `threshold_from` (a rule committed before the run in PR A) from a pinned record of the owner's real prints, and a test re-derives them on every `make verify`. No vendor or forum figure enters.

But it is weaker than what the phase pre-registered, and I will not call it equivalent:

- Run 2 is the owner's earlier informal prints accepted under R10 (over Claude's recommendation to re-run). The parts did not come from `export run-2`; `manifest-run-2.tsv` does not exist; nothing in the repo ties the printed M3 to M5 nuts to the shipped 0.15 mm STL bytes. The link is the owner's word that the 0.15 mm result is the one recorded.
- Only 9 rows (3 sizes x 3 samples), transcribed by Claude from prose and confirmed by the owner; the owner gave no dates. M3 rows are `bind` at 0 turns with note `thread did not print`, an encoding of "no thread printed" into a pass/bind schema.
- The pre-registered mitigation (every nut name carries the shipped default, every file its digest) had nothing to check.
- The threshold rests on 3 samples per size at one profile (Prusa MK4, 0.4 mm nozzle, PETG, 0.2 mm layers).

L18, `bench/RESULTS.md` (run-2 entry with four numbered departures) and REQUIREMENTS INFO-04 all state this, so the weakness is disclosed rather than smoothed over. I treat INFO-04 as satisfied with that caveat. It is a standing note for the release, not a gap. If the owner later wants the stronger evidence, a re-run as pre-registered plus a superseding L-entry is the route (L18 says so).

PAIR-02 (run 1) does not share this weakness: pre-registered, manifest committed before printing, record pinned. Its provenance caveat is only that the cells were transcribed from the owner's report and confirmed.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `bench/print_rules.py` | strict readers, `default_from`, `threshold_from`, pinned digests | VERIFIED | imports clean; 51 tests in `tests/test_print_rules.py` pass |
| `bench/results/phase-06/print-run-1.tsv` | 60 rows | VERIFIED | digest equals pin |
| `bench/results/phase-06/print-run-2.tsv` | 9 rows | VERIFIED | digest equals pin |
| `bench/results/phase-06/manifest-run-1.tsv`, `manifest-acceptance.tsv` | pre-print file manifests | VERIFIED | acceptance manifest equals files on disk; `manifest-run-2.tsv` intentionally absent (R10) |
| `src/screw/calc/printability.py` | constants and both warning builders, stdlib only | VERIFIED | substantive, wired |
| `src/screw/params.py` | frozen clearance default 0.15 | VERIFIED | |
| `docs/architecture/decision_log.md` | L17, L18 | VERIFIED | both cite run, digests, profile; L18 states weaker evidence |
| `bench/RESULTS.md` | run-1, run-2, acceptance entries | VERIFIED | |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `calc/__init__.py` `_bolt`, `_nut` | `printability_warning(p.d, p.pitch)` | append before counterpart block | WIRED |
| `_nut` | `measured_range_warning` (D-09) | before the printability sentence | WIRED |
| `tests/test_print_rules.py` | `params.py` default and `printability.py` constants | re-derivation from pinned records | WIRED (tests pass) |
| `app.js` | `info.warnings` | `pendingWarnings` to `showMessages` | WIRED (rendering unlooked, human item) |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| warnings in `/api/<kind>/info` | `printability_warning` string | `derive()` from request d, pitch against constants pinned to the record | yes (live curl) | FLOWING |
| nut clearance rows | 0.15 / 0.3 | `NutParams.clearance` default | yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Record readers and rules | `pytest tests/test_print_rules.py` | 51 passed | PASS |
| Default frozen | `pytest tests/test_params.py -k clearance` | 2 passed | PASS |
| Printability and range edges | `pytest tests/test_calc.py tests/test_parity.py -k "printab or measured_range"` | 38 passed | PASS |
| API warnings | curl `/api/{bolt,nut}/info` at M3, M4 exact, M8 | as expected above | PASS |
| CLI parity | `screw info nut --d 3 --pitch 0.5` | same two sentences; M8 nut exit 0 | PASS |
| Acceptance files | `shasum -a 256 ~/Downloads/3dprint/*.stl` | equal manifest | PASS |

Full gate not re-run by me: the orchestrator reports `make verify` on HEAD `788c9b9` as `3556 passed in 151.79s`; I ran only the targeted tests above. Debt-marker scan (`TBD|FIXME|XXX`) over the phase's changed code and tests: none.

### Probe Execution

SKIPPED: no probe scripts declared by the phase.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| PAIR-02 | 01-07 | SATISFIED | truths 1, 2, 6; L17 |
| PAIR-05 | 03, 10 | SATISFIED | truth 3 |
| INFO-04 | 01-04, 08, 09 | SATISFIED with weaker evidence | truth 5; L18 |
| PAIR-06 | 01, 02, 03 (frontmatter, struck by R9) | DEFERRED to v2, recorded | truth 4; REQUIREMENTS traceability row |

REQUIREMENTS.md maps only PAIR-02, PAIR-05, INFO-04 to Phase 6; all three appear in plan frontmatter. No orphaned requirements. PAIR-07 deferred with PAIR-06, not built.

### Anti-Patterns Found

None blocking. Code-review findings (Codex, cross-CLI) WR-01, WR-02, WR-03, IN-01 all marked fixed in `06-REVIEW-DISPOSITION.md` with commits `e1d85c7`, `42b9665`, `7cf8a06`, `40fd8a1` (all present in git log), plus `788c9b9`.

| File | Issue | Severity | Impact |
|------|-------|----------|--------|
| `bench/RESULTS.md` ~L7274-7277 (run-1 entry, "Off-protocol, as reported") | Stale: says the M3 to M5 prints "are not run 2", "no number or threshold is read from them" and "Run 2 remains to be decided". R10 later made them run 2 and L18 reads M4 from them. Also says M4/M5 "pass at 0.1 and bind below" while the run-2 entry says bound "after half a turn" below 0.1. | Warning | Contradicts the run-2 entry and L18 for a reader of RESULTS top to bottom. Not a gap: the later entry and L18 are correct and explicit. Suggest a one-line pointer to R10 under the paragraph. |
| `docs/architecture/decision_log.md` L17 "Outside the measured range" | Future tense ("will carry ... plan 06-07 wires it"), now wired | Info | Cosmetic |

### Human Verification Required

#### 1. Page shows the three warning states

**Test:** Open http://127.0.0.1:8000. Pick bolt ISO 4017 M3 x 6; then the nut with a size outside M6 to M12; then ISO 4017 M8 x 16.
**Expected:** M3: printability sentence (naming d_min 4, P_min 0.7, run 06-print-run-2, L18). Nut outside M6 to M12: the D-09 sentence (and the printability one if below 4 mm). M8 x 16: neither.
**Why human:** Visual page rendering (06-09 Task 2). The API payloads that feed the page were verified.

### Gaps Summary

No gaps. Every truth has code or record evidence, the pinned records match their digests, the shipped default and threshold constants are re-derived from the records by tests, and the live API and CLI carry the right sentences. Status is `human_needed` only because the page-level visual check deferred from 06-09 Task 2 is still outstanding. Two standing notes for the owner and the release: INFO-04's threshold rests on weaker, R10-accepted evidence (disclosed in L18); and PAIR-05 is one M8 pair, the owner's word, printed on one profile.

Not committed. Do not stage `.planning/HANDOFF.json`, `.planning/phases/05-hex-nut-and-kernel-pair-proof/.continue-here.md` or `.planning/ui-reviews/`.

---

_Verified: 2026-10-23_
_Verifier: Claude (gsd-verifier)_
