---
phase: "02"
slug: "thread-spike"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-06"
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (floating >=8; pytest-xdist 3.8.0, pytest-cov 7.1.0 pinned per L10; `filterwarnings = ["error"]`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`; coverage source is `src/screw` only, so bench code never moves the 94 floor |
| **Quick run command** | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k '<filter>'"` (pytest exits 5 when the filter selects nothing) |
| **Full suite command** | `make verify` |
| **Estimated runtime** | quick: under 30 s (one worker spawn ~4 s, a few real-kernel rows ~1 s each); full: the Phase 1 gate plus under 20 s |

---

## Sampling Rate

- **After every task commit:** the pre-commit hook runs `make verify`; the task's quick command runs first
- **After every plan wave:** `make verify` plus the plan's `smoke` command(s)
- **Before `/gsd-verify-work`:** full suite green on PR 2's head; PR 1 additionally reviewed by the other CLI before `make pr.land` (D-19)
- **Max feedback latency:** 60 seconds for task-level commands (the campaign itself is a measurement, never a gate; no timing assertion enters `make verify`, D-15)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | INFR-03 | T-02-01, T-02-02 | owner's pin and rulings recorded verbatim, no ISO clause text | manual (checkpoint:decision) | — (owner reply) | n/a | ✅ owner reply recorded (02-01-SUMMARY; 02-SPIKE.md Owner rulings) |
| 02-01-02 | 01 | 1 | INFR-03 | T-02-01 | protocol file with Owner rulings and the `## Results` boundary | docs | `grep -n '^## Owner rulings' .planning/phases/02-thread-spike/02-SPIKE.md && grep -nx '## Results' .planning/phases/02-thread-spike/02-SPIKE.md` | ❌ (created by task) | ✅ green 2026-10-09 (both greps hit) |
| 02-02-01 | 02 | 2 | INFR-03 | T-02-03, T-02-04, T-02-07 | worker output parsed as strict JSON; dead or hung child is one recorded row with null numbers | integration (tracer) | `.venv/bin/python -m bench.thread_spike smoke` | ❌ (created by task) | ✅ green 2026-10-09 (`smoke` exit 0 in 1 s; written to a temp dir, never recorded) |
| 02-02-01 | 02 | 2 | INFR-03 | T-02-03 | quiet gate, closed form, classify_row, stl_check, parse_record predicates | unit | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'quiet or section_area or presets or row or stl_check or worker or rod'"` | ✅ file exists, cases new | ✅ green 2026-10-09 (140 passed) |
| 02-02-02 | 02 | 2 | INFR-03 | T-02-05, T-02-06 | no campaign run before the protocol is on origin/main | unit + CLI | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'guard or results_heading'"`; `check-protocol` exits 2 | ✅ | ✅ green 2026-10-09 (15 passed; `check-protocol` now exits 0 "held" because the protocol is on origin/main; the refusal path is the `-k guard` cases) |
| 02-03-01 | 03 | 3 | INFR-03 | — | exact grid counts (1790 per hand), integer-turn exactness, frontier ends | unit (tdd) | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'grid or lengths or integer_turn or frontier or depth_presets'"` | ✅ | ✅ green 2026-10-09 (74 passed) |
| 02-03-02 | 03 | 3 | INFR-03 | T-02-08, T-02-09, T-02-10 | run id validated, never overwritten; guarded blocks | integration (smoke) + CLI | `.venv/bin/python -m bench.thread_spike smoke --block grid`; guarded `run` exits 2 and writes nothing | ✅ | ✅ green 2026-10-09 (`smoke --block grid` exit 0 in 4 s; the guarded `run` probe was not re-run: with the protocol landed the guard passes and a run would record; run-id refusal is a `-k guard` case) |
| 02-03-03 | 03 | 3 | INFR-03 | T-02-09 | budget, frontier, K, estimator, T_gate, pass bar, turn caps at every threshold +/- one step | unit (tdd) | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'budget or frontier_stop or select_k or estimator or gate_tolerance or pass_bar or turn_cap or verdict'"` | ✅ | ✅ green 2026-10-09 (104 passed) |
| 02-04-01 | 04 | 4 | INFR-03 | T-02-SC | git-only package vetted before install | manual (checkpoint:human-verify, blocking-human) | — (owner "approved") | n/a | ✅ owner approved the pinned commit (02-04-SUMMARY) |
| 02-04-02 | 04 | 4 | INFR-03 | T-02-11 | reference package only in its own worker; never in dependency files | integration (smoke) | `SCREW_SPIKE_CQW=... .venv/bin/python -m bench.thread_spike smoke --block controls`; `smoke --block trim` | ✅ | ✅ green 2026-10-09 (`smoke --block controls` exit 0 in 5 s with `SCREW_SPIKE_CQW` set; `smoke --block trim` exit 0 in 4 s) |
| 02-04-03 | 04 | 4 | INFR-03 | T-02-12, T-02-13 | container mount read-only; RSS only from fresh children | integration (smoke) | `.venv/bin/python -m bench.thread_spike smoke --block rss`; `smoke --block container` | ✅ | ✅ green 2026-10-09 (`smoke --block rss` exit 0 in 3 s; `smoke --block container` exit 0 in 5 s, linux/amd64 under OrbStack) |
| 02-05-01 | 05 | 5 | INFR-03 | T-02-14 | closed-form pins (M6 m=5.2: 12.213, 14.1335, 16.1427, 4.3627, 18.2374) and D-12/D-14 rules | unit (tdd) | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'interference or cell_verdict or falsifiable or excluded or mixed_hand or sensitivity or variant'"` | ✅ | ✅ green 2026-10-09 (44 passed) |
| 02-05-02 | 05 | 5 | INFR-03 | T-02-14, T-02-15 | proven only when every control fires; diagnostics kept alive, never verdict inputs | integration (smoke) | `.venv/bin/python -m bench.thread_spike smoke --pair` | ✅ | ✅ green 2026-10-09 (`smoke --pair` exit 0 in 37 s) |
| 02-05-03 | 05 | 5 | INFR-03 | T-02-16 | one guarded campaign; existing records refuse it | unit + CLI | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'campaign'"`; `campaign --run-id plan-check` exits 2 | ✅ | ✅ green 2026-10-09 (18 passed; the `campaign --run-id plan-check` probe was not re-run: with the protocol landed it would start a real campaign; refusal of an existing run id is a `-k campaign` case) |
| 02-06-01 | 06 | 6 | INFR-03 | T-02-17, T-02-18 | every constant pre-registered; PR text free of skip tokens | unit + docs | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k 'protocol'"` | ✅ | ✅ green 2026-10-09 (13 passed) |
| 02-06-02 | 06 | 6 | INFR-03 | T-02-19 | other-CLI review before landing | manual (checkpoint:human-action) | — (owner "land") | n/a | ✅ satisfied out of band; indirect evidence, human judgment (02-06-SUMMARY D5) |
| 02-06-03 | 06 | 6 | INFR-03 | T-02-18, T-02-19 | landed through make pr.land; guard holds on the runs branch | CLI | `gh pr list --state merged --head gsd/phase-02-thread-spike --json number,state --jq '.[0].state'`; `check-protocol` exits 0 | ✅ | ✅ green 2026-10-09 (MERGED; `check-protocol` held) |
| 02-07-01 | 07 | 7 | INFR-03 | — | guard holds; image amd64; reference package imports; smoke ok | CLI | `.venv/bin/python -m bench.thread_spike check-protocol` | ✅ | ✅ green 2026-10-09 (protocol guard: held) |
| 02-07-02 | 07 | 7 | INFR-03 | T-02-21 | campaign on a quiet host, agents closed | manual (checkpoint:human-action) | — (owner "done") | n/a | ✅ owner decision recorded: R4 overridden on 2026-10-08, campaign launched from the agent session with applications open; ksweep, grid, frontier released non-decisive, seconds claims not established (02-07-SUMMARY) |
| 02-07-03 | 07 | 7 | INFR-03 | T-02-20, T-02-22 | outputs verbatim, JSONL hashed, harness unchanged since review | CLI | sha256 loop over `bench/results/thread-spike/*.jsonl` against `bench/RESULTS.md`; `git diff --quiet origin/main -- bench/thread_spike bench/quiet.py` | ✅ | ✅ green 2026-10-09 (9 JSONL hashes present; harness unchanged against origin/main) |
| 02-08-01 | 08 | 8 | INFR-03 | T-02-23 | verdict reproducible from committed records | CLI | `verdict --campaign <prefix>` (exit 0 or 1) diffed against the campaign log; `check-protocol` exits 0 | ✅ | ✅ green 2026-10-09 (exit 1 = not a pass; output identical to campaign log lines 13-1086; guard held) |
| 02-08-02 | 08 | 8 | INFR-03 | T-02-24 | owner accepts L11 / chooses the roadmap consequence | manual (checkpoint:decision) | — (owner reply) | n/a | ✅ owner chose "revise: Phase 5" on 2026-10-09 (02-08-SUMMARY) |
| 02-08-03 | 08 | 8 | INFR-03 | T-02-25 | L11 committed with no thread field in src/ (SC4) | CLI | `grep -n '^## L11' docs/architecture/decision_log.md && git diff --quiet origin/main -- src/` plus the src/screw identifier grep exiting 1 | ✅ | ✅ green 2026-10-09 (SC4 held: L11 at line 284, src/ unchanged, identifier grep exit 1) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements: pytest, the `make test` / `make verify`
targets and `tests/test_bench.py` already exist. Each plan writes its tests in the same task as the
code (tdd tasks write them first); no separate Wave 0 plan is needed and no `MISSING` sentinel is used.

- [x] `tests/test_bench.py` exists (cases are added per task)
- [x] framework installed (pytest, xdist, cov pinned per L10)
- [x] `bench/thread_spike/` and `bench/quiet.py` — created by plan 02-02 (tracer); on main since PR 5 (`fd40abc`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ISO 68-1:2023 read and profile pinned before any section code (D-01) | INFR-03 | the owner reads a purchased standard | plan 02-01 Task 1 checkpoint; reply quoted in 02-SPIKE.md |
| Pre-registration order on main (SC1) | INFR-03 | a property of main's history | `git log --format='%h %s' origin/main -- .planning/phases/02-thread-spike/02-SPIKE.md` shows PR 1's squash commit before any `bench/results/thread-spike` commit; `check-protocol` holds |
| Quiet host for timing claims (SC2) | INFR-03 | an agent session itself keeps the load near 2.0 | plan 02-07 Task 2: the owner runs the campaign detached with every agent closed; each block header records its release and timestamped readings |
| Cross-CLI review of PR 1 | INFR-03 | the author may not review its own diff (AGENTS.md) | plan 02-06 Task 2 |
| Decision entry acceptance and escape-clause consequence (SC4, SC5) | INFR-03 | L11 is a locked decision the owner stands behind | plan 02-08 Task 2 checkpoint |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (the five owner checkpoints are manual-only rows, each with the owner's recorded reply)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (no two manual rows are adjacent)
- [x] Wave 0 covers all MISSING references (no MISSING sentinel was used; every test shipped with its task)
- [x] No watch-mode flags
- [x] Feedback latency < 60s for task-level commands (measured 2026-10-09: the seven `tests/test_bench.py` filters ran in 2.0 s to 22.5 s each under `-n0 --no-cov`)
- [x] `nyquist_compliant: true` set in frontmatter (validate-phase, 2026-10-09)

**Approval:** approved 2026-10-09 (validate-phase audit after plan 02-08: every automated command re-run green on `gsd/phase-02-thread-spike-runs` at `623c210`; the five manual-only rows carry the owner's recorded replies)

## Validation Audit 2026-10-09

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
