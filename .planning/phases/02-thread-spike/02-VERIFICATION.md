---
phase: 02-thread-spike
verified: 2026-10-09T03:30:00Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - ".planning/phases/02-thread-spike/02-01-PLAN.md"
  - ".planning/phases/02-thread-spike/02-01-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-02-PLAN.md"
  - ".planning/phases/02-thread-spike/02-02-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-03-PLAN.md"
  - ".planning/phases/02-thread-spike/02-03-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-04-PLAN.md"
  - ".planning/phases/02-thread-spike/02-04-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-05-PLAN.md"
  - ".planning/phases/02-thread-spike/02-05-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-06-PLAN.md"
  - ".planning/phases/02-thread-spike/02-06-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-07-PLAN.md"
  - ".planning/phases/02-thread-spike/02-07-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-08-PLAN.md"
  - ".planning/phases/02-thread-spike/02-08-SUMMARY.md"
  - ".planning/phases/02-thread-spike/02-SPIKE.md"
  - "bench/RESULTS.md"
  - "bench/results/thread-spike/2026-10-08-a-campaign.md"
  - "bench/results/thread-spike/2026-10-08-a-container.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-controls.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-frontier.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-grid.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-ksweep.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-ladder.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-pair.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-rss.jsonl"
  - "bench/results/thread-spike/2026-10-08-a-trim.jsonl"
  - "docs/architecture/decision_log.md"
covered_digest: "v3:sha256:0ad62dbb56ddad5e6a62a86db93c8f658a839a87c7d2bdcf8311a33be745d699"
behavior_unverified: 0
overrides_applied: 0
deferred:
  - truth: "Seconds caps per size (the seconds clause of the mesh budget over the whole grid)"
    addressed_in: "Phase 7"
    evidence: "Phase 7 SC1: 'The per-build timeout is measured over the whole allowed grid on linux/amd64 ... and recorded as a constant whose decision entry cites the run.' L11 also states Phase 7 re-measures the unestablished seconds caps."
human_verification:
  - test: "Accept or reject the indirect evidence that PR 5 (the harness and pre-registered protocol) had a cross-CLI review (02-06 D5)"
    expected: "The owner confirms the review the repo cannot show (no GitHub review object; findings F4 and G6 cited in the protocol; 23 fix commits; owner merged the PR) satisfies the D-19 / AGENTS.md rule that whoever wrote the diff does not review it. If rejected, the remedy is a review on the existing record, not a protocol edit."
    why_human: "gh pr view 5 returns empty reviews and comments. Which CLI reviewed, and what it said, cannot be established from any artifact."
  - test: "Judgment-tier prohibition P1 (02-08): the escape-clause outcome, the non-falsifiable size and the non-pass verdict (pass bar held, escape clause fired) are not softened or reworded away"
    expected: "Owner reads 02-SPIKE.md '## Verdict' and L11 'Escape clause' beside the verdict output and agrees the wording is the rules' output. Verifier LLM-judge: no softening found. NON-AUTHORITATIVE. unverified-prohibition, human review recommended."
    why_human: "Judgment-tier prohibition (ADR-550 D4); an LLM verdict is never authoritative for it."
  - test: "Judgment-tier prohibition P2 (02-08): no thread-building field or builder exists in src/ before or with the decision entry"
    expected: "Owner agrees the SC4 check is sufficient. Verifier ran it (git diff --quiet origin/main -- src/ exit 0; git grep for helix/Helix/PipeShell/left_hand/thread_length/Sewing in src/screw exit 1). NON-AUTHORITATIVE LLM-judge verdict: holds. unverified-prohibition, human review recommended."
    why_human: "Judgment-tier prohibition (ADR-550 D4)."
  - test: "Judgment-tier prohibition P3 (02-08): no number in L11 that the records do not contain or no pre-registered rule produced; unestablished values written 'not established'"
    expected: "Owner spot-checks L11 against the verdict. Verifier cross-checked K table, T_gate, estimator error, turn-cap table, excluded clearances, known-bad inputs, container count, unchecked-mesh count against a fresh verdict run: all match. NON-AUTHORITATIVE. unverified-prohibition, human review recommended."
    why_human: "Judgment-tier prohibition (ADR-550 D4)."
---

# Phase 2: Thread Spike Verification Report

**Phase Goal:** The owner knows, from a pre-registered and recorded measurement rather than a guess, which helical construction to build, which volume estimator to trust, what turn cap each size needs, and whether a kernel pair proof can be made falsifiable, all before any field that builds a thread exists.
**Verified:** 2026-10-09T03:30:00Z
**Status:** human_needed
**Re-verification:** No, initial verification

The goal is achieved, with the qualification the record itself states: the spike's own verdict is "not a pass" (escape clause FIRED for the M18 pair proof; seconds caps not established). That is the honest, pre-registered outcome and the roadmap's SC5 describes it as an acceptable one. I found no gap against the roadmap contract. The status is `human_needed` only because four items cannot be settled from artifacts (one process-evidence item, three judgment-tier prohibitions).

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Method, predictions and escape clause committed before the first run; git history shows the order | VERIFIED | `fd40abc` (PR 5, 2026-10-08 15:28 +0600 = 09:28Z) carries `02-SPIKE.md` with Method, Predictions and Escape clause; first run reading is `2026-10-08-a-ksweep` at 11:01:06Z. Every one of the 9 run headers records protocol blob `4e1959e` = origin/main's blob. `fd40abc` is an ancestor of the campaign HEAD `32cdeac`. `check-protocol` prints "protocol guard: held" (exit 0). Harness diff `origin/main..HEAD` over `bench/` (excluding results), `tests/`, `Makefile`, `pyproject.toml`, `requirements.txt` is empty: nothing moved after landing. |
| 2 | Every run behind a quiet-host gate; every load reading labelled with when it was taken | VERIFIED | I parsed all 9 JSONL headers: every `readings` entry is `[ISO-8601 UTC time, load]` (all labelled), and every header carries a `decisive` flag. Decisive: ladder, trim, controls, rss, pair. Non-decisive: ksweep, grid, frontier (released non-decisive at the 900 s cap), container (non-decisive by construction). The two departures (host M5 Max vs registered M2 Max; owner ruling R4 overridden) are stated verbatim at the head of the `## Thread spike (Phase 2)` section of `bench/RESULTS.md`, in 02-SPIKE.md Results and in L11, and both are owner decisions quoted in 02-07-SUMMARY. Caveat, not a gap: code-review WR-03 notes `decisive` is decided once at block start; no decisive-only claim in the verdict rests on it (see Anti-Patterns). |
| 3 | Results answer four questions with run ids, over the whole grid (M2 to M20, every standard length), not a sample | VERIFIED (seconds clause deferred) | The verdict reads a block only when its record is complete against the pre-registered row set; it read grid 7160/7160, container 7160/7160, ksweep 192, frontier 2236 (all 15 sizes, both hands, to 250 turns), ladder 16, pair 272 cells. Construction and frontier: `-ksweep`, `-grid`, `-frontier`, `-container`, `-controls`. Mesh budget: triangles and bytes over the whole grid, peak RSS and gzip table from the decisive `-rss`; seconds: the grid is non-decisive so the seconds cap is "not established" for all 15 sizes (pre-registered rule R4, never re-run toward a value); decisive timing exists only as evidence in `-ladder`, `-trim`, `-rss`. Pair: `-pair` (decisive) with half-pitch controls, 14 of 15 sizes falsifiable both hands, M18 not. Estimator: `precise`, max abs error 8.147e-06, T_gate 9e-05. Re-ran `verdict --campaign 2026-10-08-a` myself (exit 1): stdout is contained verbatim in both `2026-10-08-a-campaign.md` and the `### 2026-10-08-a-verdict` entry of `RESULTS.md`. 02-SPIKE.md Results spot checks (one-pipe inverts at the 160-turn step on 8 of 8 sizes and reads ok at 200 and 250; container 7160 ok) match the verdict. The seconds clause is listed under Deferred Items (Phase 7 SC1 measures the per-build timeout over the whole grid on linux/amd64). |
| 4 | A new decision entry records construction, estimator, turn cap per size and the ISO 68-1:2023 profile pinned; no thread-building field in `src/` when committed | VERIFIED | `docs/architecture/decision_log.md:284` `## L11`: Profile (basic, pinned 2026-10-06 at the D-01 checkpoint, coefficients in 02-SPIKE.md), Construction (sewn twist-section, K = 3), Volume estimator (`BRepGProp` eps 1e-6, never `Volume()`, T_gate 9e-05), Turn cap table for all 15 sizes (construction 250 for all; bytes caps M8 to M20; seconds "not established"), Pair check per size with excluded clearances, THRD-04 known-bad inputs (15 tuples, identical to the verdict's list), Container, Escape clause, UNVERIFIED and INTERIM inputs, Reason, Reversibility. SC4 check: `git diff --quiet origin/main -- src/` exit 0; `git grep -n -e helix -e Helix -e PipeShell -e left_hand -e thread_length -e Sewing -- src/screw` exit 1 (no match). `git diff --name-only origin/main..HEAD` touches no file under `src/`, `tests/` or `bench/` code. |
| 5 | If the pair check cannot be made falsifiable or the worst case trips the escape clause, the spike says so and the roadmap is revised before Phase 5 is planned; no constant tuned toward a pass | VERIFIED | Verdict: "escape clause: FIRED - pair: not falsifiable for size M18 (right, left hand)". Stated unsoftened in 02-SPIKE.md `## Verdict`, L11 `Escape clause`, STATE.md Blockers (lines 124 to 125) and ROADMAP.md line 161 `**Precondition (L11 escape clause)**` under Phase 5. The owner chose "revise: Phase 5" at the 02-08 Task 2 checkpoint (quoted in 02-08-SUMMARY line 126). Phase 5 is gated, not planned. The revision itself is the future precondition this SC defers to ("before Phase 5 is planned"). No constant moved: the harness diff is empty and the protocol guard holds. |

**Score:** 5/5 truths verified (0 behavior-unverified; 1 sub-clause deferred to Phase 7)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Seconds caps per size (non-decisive grid, "not established") | Phase 7 | Phase 7 SC1: per-build timeout measured over the whole allowed grid on linux/amd64 and recorded with a decision entry. L11 Reversibility: "unestablished seconds caps and the INTERIM budgets are reversible by design: Phase 7 re-measures them." |

### Required Artifacts

No plan declares frontmatter `must_haves.artifacts` beyond plan 02-08; checked directly.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/architecture/decision_log.md` (`## L11`) | Decision entry | VERIFIED | Present at line 284, full structure, numbers cross-checked to the verdict |
| `.planning/phases/02-thread-spike/02-SPIKE.md` (`## Results`, `## Verdict`) | Results and Verdict by citation | VERIFIED | Present; four question subsections plus Verdict; text above `## Results` byte-equal to origin/main |
| `bench/RESULTS.md` `### 2026-10-08-a-verdict` and 9 run entries | Verbatim record | VERIFIED | Entries and sha256 present for all 9 JSONLs; recomputed sha256 of each file appears in the document |
| `bench/results/thread-spike/*` (9 JSONL + md + campaign log) | Raw records | VERIFIED | Present; row counts 7160/7160/192/2236/16/30/85/90/272 |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | Escape consequence | VERIFIED | Blocker line 125, precondition line 161 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| L11 | `bench/RESULTS.md` | every value cites a `2026-10-08-a-*` run id | WIRED | All L11 sections name the run ids; each id has an entry |
| Verdict output | JSONL records | `verdict --campaign` recomputes classes from raw rows | WIRED | Re-run reproduces committed output |
| Protocol | Guard | `check-protocol` against origin/main blob | WIRED | "protocol guard: held" |

### Data-Flow Trace (Level 4)

Not applicable in the UI sense (no rendered dynamic data in `src/`). The analogue was traced: JSONL rows to verdict tables to L11 numbers (K table, T_gate, turn caps, excluded clearances, known-bad inputs, container 7160/7160, 1025 of 7160 unchecked meshes). All match; none is a literal or placeholder.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Protocol guard holds | `.venv/bin/python -m bench.thread_spike check-protocol` | "protocol guard: held", exit 0 | PASS |
| Verdict reproducible | `.venv/bin/python -m bench.thread_spike verdict --campaign 2026-10-08-a` | exit 1 (designed "not a pass"); output contained in campaign log and RESULTS.md | PASS |
| Full gate | `make verify` | 695 passed, coverage 95.56 % (floor 94.0 %), exit 0 | PASS |
| SC4 no thread field | `git diff --quiet origin/main -- src/`; `git grep ... -- src/screw` | exit 0; exit 1 | PASS |

I did not run `campaign`, `run` or `smoke` (they write records).

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and no plan declares a probe. SKIPPED.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| INFR-03 | 02-01 to 02-08 (all eight declare `requirements: [INFR-03]`) | Spike pre-registered, run behind a quiet-host gate with time-labelled load readings, result is a decision entry (construction, estimator, turn cap per size) before any thread field exists | SATISFIED | SC1 to SC4 above; L11 records seconds caps as "not established" rather than inventing them. |

REQUIREMENTS.md maps only INFR-03 to Phase 2 (line 158): no orphaned requirements. Note: it already reads "Complete" while the ROADMAP progress row for Phase 2 still reads "In Progress" (bookkeeping for the close-out, not a goal gap).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `bench/thread_spike/__main__.py` | 1375 | WR-01 prefix glob can read a longer-prefix campaign | Warning | Does not affect this campaign (one prefix, 9 runs, verdict reproduced). Filed as tech debt. |
| `bench/thread_spike/__main__.py` | 1142 | WR-02 `--k-from`/`--frontier-from` accept incomplete records | Warning | Campaign path is guarded by `_NEEDS`; verdict refuses incomplete ksweep. No effect on recorded result. |
| `bench/quiet.py` | 52 | WR-03 `decisive` fixed at block start | Warning | Could over-label a block decisive. The decisive blocks (ladder, trim, controls, rss, pair) feed no timing claim in the verdict; pair outcomes count on any gate; the pair block had no timeout cell. No effect on any verdict claim. |
| `bench/thread_spike/verdict.py` | 1589 | WR-04 mixed-hand cell does not check nut body | Warning | Could read a garbage cell as violated. The mixed-hand criterion did not drive the escape (M18 fired on same-hand cells); the identical left-hand nut is checked in the guarded left/left cells. No effect on the outcome. |
| `bench/thread_spike/__main__.py` | 183 | WR-05 dirty working tree not detected | Warning | Header HEAD could mask uncommitted edits. The committed harness equals the protocol commit's (diff empty) and the guard checked the on-disk protocol file against `origin/main` at each run; whether `bench/thread_spike/` on disk matched HEAD while the campaign ran is not recorded (that is WR-05) and is unverified. |
| harness (IN-01 to IN-07) | various | Info items | Info | Open, filed in `docs/tech_debt/active/2026-10-09-thread-spike-harness-review-findings.md`. D-19 freezes the harness on this branch. |

No `TBD`/`FIXME`/`XXX` marker was introduced by the phase (`make verify` runs the unfinished-work scan and exits 0). No code in `src/` changed.

### Human Verification Required

#### 1. Cross-CLI review of PR 5 (02-06 D5)

**Test:** Decide whether the indirect evidence satisfies the D-19 review rule.
**Expected:** Owner accepts, or requests a review on the existing record.
**Why human:** No GitHub review object exists; the reviewer and findings are unverifiable from the repo.

#### 2. Unverified prohibitions, judgment tier (02-08 P1, P2, P3)

**Test:** Skim 02-SPIKE.md `## Verdict`, L11 and `git diff origin/main -- src/`.
**Expected:** Agreement that nothing is softened, nothing in `src/`, and no invented number. Verifier's LLM-judge reading is "holds" for all three, flagged `unverified-prohibition - human review recommended`, non-authoritative.
**Why human:** Judgment-tier prohibitions never pass silently.

### Gaps Summary

No gaps against the roadmap contract. Things the owner should keep in view, all already recorded in the artifacts:

- The verdict is "not a pass": escape clause FIRED at M18 (both hands), so Phase 5 stays gated until the roadmap is revised (no direction named yet). Phase 3 is plannable on L11.
- Seconds caps are unestablished for all 15 sizes because the grid ran non-decisive after the owner overrode R4; Phase 3's cap-and-warn input is therefore the construction and bytes columns only until Phase 7.
- The campaign ran on an Apple M5 Max, not the registered M2 Max (owner option A; kernel pair identical).
- 12 code-review findings are open by design (D-19 freeze) and filed as tech debt.

---

_Verified: 2026-10-09T03:30:00Z_
_Verifier: Claude (gsd-verifier)_
