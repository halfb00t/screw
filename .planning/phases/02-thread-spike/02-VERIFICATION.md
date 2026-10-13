---
phase: 02-thread-spike
verified: 2026-10-13T08:56:00Z
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
  - "bench/thread_spike/__main__.py"
  - "bench/thread_spike/maths.py"
  - "bench/thread_spike/verdict.py"
  - "docs/architecture/decision_log.md"
  - "tests/test_bench.py"
covered_digest: "v3:sha256:3dcaa82ffc65dcead008083dad56738933fb2681493d89974ce02ecf49fa3d61"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Seconds caps per size (the seconds clause of the mesh budget over the whole grid)"
    addressed_in: "Phase 7"
    evidence: "Phase 7 SC1: 'The per-build timeout is measured over the whole allowed grid on linux/amd64 ... and recorded as a constant whose decision entry cites the run.' L11 Reversibility also states Phase 7 re-measures the unestablished seconds caps."
---

# Phase 2: Thread Spike Verification Report

**Phase Goal:** The owner knows, from a pre-registered and recorded measurement rather than a guess, which helical construction to build, which volume estimator to trust, what turn cap each size needs, and whether a kernel pair proof can be made falsifiable, all before any field that builds a thread exists.
**Verified:** 2026-10-13T08:56:00Z
**Status:** passed
**Re-verification:** Yes, regeneration (#5118) against `main` at HEAD `4435df8`. The previous report (2026-10-09, 5/5) read `stale` because covered files changed. This run re-derived every truth from the code and records as they stand now.
**HEAD:** 4435df8 on `main`; the working tree is clean apart from untracked `.planning/ui-reviews/` and `web/.DS_Store`.

## Verdict in one paragraph

The goal holds on `main` today, with the qualification the record itself states: the spike's own verdict is "not a pass" (pass bar held, escape clause FIRED for the M18 pair proof, seconds caps not established). That is the pre-registered, honest outcome and ROADMAP SC5 names it as an acceptable one. Three things changed since the 2026-10-09 report and I re-checked each rather than carry the old claims:

1. **The harness moved after landing, by the protocol's own amendment route.** The old report said "harness diff `origin/main..HEAD` is empty". That was true then and is not true now: PR #9 (`e772716`, 2026-10-10) fixed WR-01, WR-02, WR-04, WR-05 and four info items in `bench/thread_spike/`, with dated amendment notes in `02-SPIKE.md` under owner ruling 2026-10-10; Phase 3 and 4 (`66d9393`, `e8df305`) then moved the closed form into `src/screw/calc/thread.py` and touched `bench/`. Neither touched a campaign record. I re-ran the verdict with today's harness over the committed records: byte-identical to the committed verdict (see truth 3).
2. **The ordering evidence is now the recorded blob, not the guard's current answer.** `check-protocol` compares the on-disk protocol to the current `origin/main` blob, which after the amendments is `c705ee7`, not the `4e1959e` the campaign ran against. So "guard: held" no longer proves ordering by itself; the nine run headers (all `protocol_blob 4e1959e`) against `fd40abc`'s blob (`4e1959e`) do (truth 1).
3. **Phase 3 and 4 landed thread builders in `src/`.** Truth 4's "no thread field in `src/` when the decision entry is committed" is a historical claim about commit `7615de2`; I checked it by git history, not at HEAD.

The seven human checkpoints are taken from `02-UAT.md` (2026-10-13, 48 passed, 0 issues; 41 by recorded coverage tests, 7 by the owner) and are not re-issued. The earlier report's `human_needed` body text was settled by the owner's 2026-10-09 UAT (4 passed) and again today; no human item is open.

MVP-mode note: ROADMAP.md marks Phase 2 `Mode: mvp`, but the goal is a measurement-outcome sentence, not "As a ..., I want to ..., so that ...", so the User Flow Coverage table would be invented. I applied standard goal-backward verification, as the Phase 3 and Phase 1 regenerations did. The owner may want to drop the `mvp` tag.

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Method, predictions and escape clause are committed before the first run; git history shows that order | VERIFIED | `fd40abc` (PR #5, 2026-10-08 15:28:21 +0600 = 09:28:21Z) carries `02-SPIKE.md` with Method, Predictions and Escape clause; the first reading of the first run (`2026-10-08-a-ksweep`) is 2026-10-08T11:01:06Z, 1 h 33 min later. I read all nine JSONL headers: every one records `protocol_blob 4e1959e` and `protocol_commit fd40abc09947744b3e030446085e26a9e1a0c87f`, and `git rev-parse fd40abc:.planning/phases/02-thread-spike/02-SPIKE.md` is `4e1959e` (also the blob at `7615de2^`, the parent of the campaign PR). The only change to `02-SPIKE.md` in the campaign PR `7615de2` is one hunk from line 274, the `## Results` section: the text above it is byte-equal to the registered blob. Nothing in `src/`, `tests/`, `Makefile`, `pyproject.toml`, `requirements.txt` or the `bench/` code differs between `fd40abc` and `7615de2` (`git diff --quiet`, exit 0). Later edits to the protocol text (`e772716`: WR-01 reads exactly `<prefix>-<block>.jsonl`; WR-04 nut-body clause moves second) are marked "Amended 2026-10-10 ... owner ruling" inside the text and post-date the campaign; the WR-04 note says re-reading the campaign under the amended rule gives a byte-identical verdict, which I confirmed under truth 3. `check-protocol` today: "protocol guard: held", exit 0, against the amended blob `c705ee7` (see the second point above for why that alone is not the ordering proof). |
| 2 | SC2: Every run sits behind a quiet-host gate; every load reading is labelled with when it was taken | VERIFIED | I parsed all nine headers: each carries a `decisive` flag and a `readings` list whose every entry is `[ISO-8601 UTC time, load]` (0 unlabelled across ksweep 31, grid 31, frontier 31, ladder 27, pair 11, trim 10, controls 3, rss 3, container 3). Decisive: ladder, trim, controls, rss, pair. Non-decisive: ksweep, grid, frontier, container. The two departures (host Apple M5 Max against the registered M2 Max, kernel pair identical; owner ruling R4 overridden) are stated at the head of `## Thread spike (Phase 2)` in `bench/RESULTS.md`, in `02-SPIKE.md` Results and in L11 "Conditions of the record"; the owner accepted them (UAT test 6). Caveat, not a gap: WR-03 (`decisive` fixed at block start) is deferred by owner ruling and filed as `docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md` (Severity must, trigger "before the next campaign"). No decisive-only claim in the verdict rests on it. |
| 3 | SC3: The results answer four questions with run ids, over the whole allowed grid (M2 to M20, every standard length), not a sample | VERIFIED (seconds clause deferred) | Re-ran `.venv/bin/python -m bench.thread_spike verdict --campaign 2026-10-08-a` with today's harness (post PR #9, post Phase 3 and 4): exit 1 (the designed "not a pass"), 1074 lines, and its stdout is contained verbatim in both `bench/results/thread-spike/2026-10-08-a-campaign.md` and the `### 2026-10-08-a-verdict` entry of `bench/RESULTS.md` (substring test, both True). So the amendments and the move of the closed form to `src/` changed no recorded outcome. Record sizes: 17,250 JSONL lines = 9 headers + 17,241 rows (grid 7160, container 7160, ksweep 192, frontier 2236, ladder 16, pair 272, trim 30, controls 85, rss 90). sha256 of each of the nine JSONLs recomputed today appears exactly once in `bench/RESULTS.md`. The four questions: construction and frontier (`-ksweep`, `-grid`, `-frontier`, `-container`, `-controls`; K = 3 selected, frontier reached 250 turns at all 15 sizes, both hands, with no stop); mesh budget (triangles and bytes over the whole grid, bytes caps M8 67.5 mm, M10 56, M12 60, M14 58, M16 52, M18 65, M20 64, none below M8; peak RSS and gzip from decisive `-rss`; seconds "not established" because the grid is non-decisive, pre-registered rule R4, never re-run toward a value); pair check (decisive `-pair`, half-pitch controls, 272 cells: 14 of 15 sizes falsifiable on both hands, M18 not); estimator (`precise`, max abs error 8.147e-06, `T_gate` 9e-05). Pass bar held with 1025 of 7160 host meshes unchecked, printed beside it. The seconds clause is the one sub-part not answered; it is deferred to Phase 7 SC1 (Deferred Items). |
| 4 | SC4: A new decision entry records the construction, the estimator, the turn cap per size and the pinned ISO 68-1:2023 profile; no field that builds a thread exists in `src/` when it is committed | VERIFIED (historical clause by git) | `docs/architecture/decision_log.md:284` `## L11`: Profile (basic, pinned 2026-10-06, four coefficients), Construction (sewn twist-section, K = 3), Volume estimator (`BRepGProp` eps 1e-6, `T_gate` 9e-05, never `Volume()`), Turn cap table for all 15 sizes, Pair check with excluded clearances per size, THRD-04 known-bad inputs, Container, Escape clause, Conditions of the record, Inputs still UNVERIFIED, Reason, Reversibility. I cross-checked against today's verdict output: the 15 known-bad tuples in L11 equal the verdict's `naive_sweep_fuse` list (script, True); K, `T_gate`, the unchecked count, the bytes-cap and construction-cap columns and the M18 all-excluded clearances match; container 7160 of 7160. **Historical clause.** The L11 commit is `7615de2` (PR #6 squash, 2026-10-09; its parent `fd40abc`; `## L11` absent at `7615de2^`, present at line 284 in it). `git diff --quiet fd40abc 7615de2 -- src/` exits 0 and `git grep -n -e helix -e Helix -e PipeShell -e left_hand -e thread_length -e Sewing 7615de2 -- src/screw` exits 1 (no match): no thread-building field existed in `src/` when L11 landed. The first thread builder in `src/` is `66d9393` (Phase 3, 2026-10-11), two days later. **Discrepancy to note:** the task brief named the L11 commit as `bfd5a45`; that object does not exist in this repository (`git cat-file -t bfd5a45` fatal, also under `git log --all`), and neither does the campaign header's `head` `32cdeac`. Both are pre-squash PR commits. I used the squash commit `7615de2`, which is what `main` holds. L11 has since gained one dated additive paragraph (the 2026-10-11 "Known-bad inputs, platform note", quick 261011-fbb, lines 369 to 384); it adds no number to any other section and states its own emulation-figure status; the owner read L11 on 2026-10-13 (UAT test 7). |
| 5 | SC5: If the pair check cannot be made falsifiable or the worst case trips the escape clause, the spike says so and the roadmap is revised before Phase 5 is planned; no constant is tuned toward a pass | VERIFIED | Verdict: "escape clause: FIRED - pair: not falsifiable for size M18 (right, left hand)" (verdict section Escape clause and Falsifiability; every M18 cell at c 0.05 to 0.2, both hands, inconclusive because one control reads empty at one pose). Stated unsoftened in `02-SPIKE.md` `## Verdict`, L11 "Escape clause", `STATE.md` line 201 and `ROADMAP.md` line 231 (`**Precondition (L11 escape clause)**` under Phase 5). The owner chose "revise: Phase 5" on 2026-10-09 (`02-08-SUMMARY.md`). Phase 5 is still gated at HEAD: `.planning/phases/` holds directories 01 to 04 only, `STATE.md` line 26 reads "not plannable until the roadmap is revised per L11's escape clause". No constant was tuned: the harness is identical between `fd40abc` and the campaign PR, the nine records are untouched since `7615de2` (`git status` clean for `bench/`, `src/`, `docs/`), and the verdict reproduces from them. |

**Score:** 5/5 truths verified (0 behavior-unverified; 1 sub-clause deferred to Phase 7). The truths are record and ordering claims, not runtime state transitions, so none is behavior-dependent in the Step 3 sense.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Seconds caps per size (non-decisive grid, "not established") | Phase 7 | Phase 7 SC1: per-build timeout measured over the whole allowed grid on linux/amd64 and recorded with a decision entry; L11 Reversibility: "unestablished seconds caps and the INTERIM budgets are reversible by design: Phase 7 re-measures them." |

### Required Artifacts

No Phase 2 plan declares `must_haves.artifacts` that `verify.artifacts` could run against beyond the files below; checked directly.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/architecture/decision_log.md` `## L11` | Decision entry | VERIFIED | Line 284; full structure; numbers cross-checked to a fresh verdict |
| `.planning/phases/02-thread-spike/02-SPIKE.md` (`## Results`, `## Verdict`) | Results and Verdict by citation | VERIFIED | Present; four question subsections plus Verdict; text above `## Results` equals the registered blob apart from two dated, owner-ruled amendment notes |
| `bench/RESULTS.md` `### 2026-10-08-a-verdict` and nine run entries | Verbatim record | VERIFIED | Verdict entry at line 5202; sha256 of all nine JSONLs present |
| `bench/results/thread-spike/*` | Raw records | VERIFIED | 19 files (9 JSONL, per-run md, campaign log); 17,241 rows |
| `STATE.md`, `ROADMAP.md` | Escape consequence | VERIFIED | `STATE.md` 26 and 201; `ROADMAP.md` 231 |
| `bench/thread_spike/` harness | Reproduces the verdict | VERIFIED | Verdict re-run byte-identical (truth 3); 72 protocol, guard and verdict tests in `tests/test_bench.py` pass (`pytest tests/test_bench.py -n0 -k "protocol or guard or frozen or pre_reg or verdict"`: 72 passed, 377 deselected, 14.46 s) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| L11 | `bench/RESULTS.md` | every value cites a `2026-10-08-a-*` run id | WIRED | Each cited id has an entry; known-bad list, K, `T_gate`, caps equal the verdict |
| Verdict command | JSONL records | recomputes every row's class from raw rows | WIRED | Re-run reproduces the committed output byte for byte |
| Run headers | Protocol commit | `protocol_blob` / `protocol_commit` | WIRED | All nine name `4e1959e` / `fd40abc`, which are the registered blob and commit |
| `bench/RESULTS.md` | JSONL files | sha256 per file | WIRED | All nine hashes recomputed and found |

### Data-Flow Trace (Level 4)

Not applicable in the UI sense (no rendered dynamic data). The analogue was traced: JSONL rows to verdict tables to L11 numbers. All match a fresh verdict run; none is a literal or placeholder.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Protocol guard | `.venv/bin/python -m bench.thread_spike check-protocol` | "protocol guard: held", exit 0 (against amended blob `c705ee7`) | PASS |
| Verdict reproducible | `.venv/bin/python -m bench.thread_spike verdict --campaign 2026-10-08-a` | exit 1 (designed "not a pass"); stdout contained in campaign log and `RESULTS.md` | PASS |
| Harness protocol tests | `.venv/bin/python -m pytest tests/test_bench.py -n0 -k "protocol or guard or frozen or pre_reg or verdict"` | 72 passed, 377 deselected | PASS |
| L11 known-bad list equals verdict | script over `decision_log.md` and the verdict text | 15 tuples, equal | PASS |
| Ordering of protocol and first run | `git log` on `fd40abc` against first reading `11:01:06Z` | 09:28:21Z before 11:01:06Z | PASS |
| SC4 at the L11 commit | `git diff --quiet fd40abc 7615de2 -- src/`; `git grep ... 7615de2 -- src/screw` | exit 0; exit 1 | PASS |
| Reference package stays out of dependencies | `git grep -n warehouse -- pyproject.toml requirements.txt` | exit 1 (no match) | PASS |
| Full regression gate | `make test` (run by the orchestrator before this run, not by me) | 2637 passed in 70.49 s, coverage 97.33 % | Taken from the orchestrator |

I did not run `campaign`, `run` or `smoke` (they write records), nor `make verify` myself.

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and no Phase 2 plan declares a probe. SKIPPED.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| INFR-03 | 02-01 to 02-08 (all eight declare `requirements: [INFR-03]`, confirmed by grep) | Spike pre-registered, run behind a quiet-host gate with time-labelled load readings, result is a decision entry (construction, estimator, turn cap per size) before any thread field exists | SATISFIED | SC1 to SC4; L11 writes seconds caps as "not established" rather than inventing them |

`REQUIREMENTS.md` maps only INFR-03 to Phase 2 (line 158, "Complete"; the requirement text at line 73): no orphaned requirement. The ROADMAP progress row now reads `8/8 | Complete | 2026-10-09`, so the bookkeeping gap the 2026-10-09 report noted is closed.

### Prohibitions (ADR-550)

All Phase 2 `must_haves.prohibitions` are judgment-tier with `status: resolved` (plans 02-01 to 02-04 and 02-08). The three 02-08 ones were the open flags in the previous report; both the owner's 2026-10-09 UAT (tests 2 to 4, passed) and today's UAT (test 7, L11 wording) settle them, and I re-judged them on current evidence. My reading is non-authoritative; the owner's UAT results are the resolution.

| Prohibition | Re-judged now | Owner resolution |
|-------------|---------------|------------------|
| P1: escape outcome, non-falsifiable size and non-pass verdict not softened | Holds: `02-SPIKE.md` `## Verdict` and L11 "Escape clause" say FIRED, M18, "not a pass", beside the unmodified verdict output | UAT 2026-10-09 test 2 pass; 2026-10-13 test 7 pass |
| P2: no thread-building field in `src/` before or with the decision entry | Holds at `7615de2` (see truth 4) | UAT 2026-10-09 test 3 pass |
| P3: no number in L11 that no record or rule produced; unestablished values written "not established" | Holds: cross-checks under truth 4; seconds column reads "not established" in L11 and verdict | UAT 2026-10-09 test 4 pass; 2026-10-13 test 7 pass |

### Anti-Patterns Found

State of the 12 code-review findings (`02-REVIEW-DISPOSITION.md`, `open: 0`; the old report called them all "open by design"):

| Finding | Severity | State on `main` |
|---------|----------|-----------------|
| WR-01 prefix glob reads a longer-prefix campaign | Warning | Fixed in `e772716` (`verdict` reads exactly `<prefix>-<block>.jsonl`), protocol note dated 2026-10-10 |
| WR-02 `--k-from` / `--frontier-from` accept incomplete records | Warning | Fixed in `e772716` |
| WR-03 `decisive` fixed at block start | Warning | Deferred by owner ruling; active must-severity debt, trigger "before the next campaign" (`docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md`). No effect on any recorded claim |
| WR-04 mixed-hand cell does not check nut body | Warning | Fixed in `e772716`; campaign re-read byte-identical (0 built cells off their nut body), reproduced today |
| WR-05 dirty working tree not detected | Warning | Fixed in `e772716` (a run refuses while the harness has uncommitted changes and records the HEAD it started at); the 2026-10-08 campaign predates the fix, so whether `bench/thread_spike/` on disk matched HEAD while it ran is still not recorded. The harness at `7615de2` equals `fd40abc`'s, and the headers' blob is the registered one, which bounds the doubt to uncommitted edits |
| IN-02 `PAIR_TIMEOUT_S` against its own comment | Info | Deferred with WR-03; `-pair` recorded no timeout cell |
| IN-01, IN-05, IN-06 | Info | Fixed in `e772716` |
| IN-03, IN-04, IN-07 | Info | Skipped with reasons in the disposition file |

No `TBD`, `FIXME` or `XXX` introduced by the phase. No code in `src/` was changed by Phase 2 (`fd40abc..7615de2` empty); the later `src/` changes belong to Phases 3 and 4.

### Human Verification Required

None open. The seven owner checkpoints were passed on 2026-10-13 (`02-UAT.md`, 48 of 48, 0 issues): owner rulings recorded faithfully (test 1); the basic profile coefficients (2); the pre-registered thresholds (3); the cq_warehouse legitimacy checkpoint (4); the PR #5 cross-CLI review evidence, which the repo cannot show directly (`gh pr view` returns no review object) and the owner accepts as satisfying D-19 (5); the campaign's two departures (6); the L11 wording (7). I did not re-ask for them.

### Gaps Summary

No gaps against the roadmap contract. Things the owner should keep in view, all recorded in the artifacts:

- The verdict is "not a pass": escape clause FIRED at M18 (both hands). Phase 5 stays unplannable until the roadmap is revised; no direction is named yet.
- Seconds caps are unestablished for all 15 sizes (grid ran non-decisive after the R4 override); Phase 3's cap-and-warn input is the construction and bytes columns until Phase 7.
- WR-03 and IN-02 are two pre-registered-input amendments waiting for the owner before any next campaign (active must debt).
- The task brief's L11 commit `bfd5a45` and the campaign header's `32cdeac` are not objects in this repository (squash merges). History-based claims here cite `fd40abc` and `7615de2`.

### Digest refresh (2026-10-13, PR #13 review)

Two covered files changed after the verifier ran, neither touching a verified claim: `docs/architecture/decision_log.md` gained L11's additive "Escape clause, revision direction" paragraph (`b4f9a96`, the Phase 5 roadmap revision), and `bench/RESULTS.md` corrected one sentence of the GitHub-runner column key (`timeout-minutes` bounds the job wall, not the pytest wall). The verdict section, the pair tables and every value this report cites are unchanged; `covered_digest` is recomputed with `verification.fingerprint` over the same 33 files.

---

_Verified: 2026-10-13T08:56:00Z_
_Verifier: Claude (gsd-verifier)_
