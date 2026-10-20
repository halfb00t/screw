---
phase: "05"
slug: "hex-nut-and-kernel-pair-proof"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-14"
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 with pytest-xdist and pytest-cov (floor 96 %) |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.coverage.*]`, import-linter contracts) |
| **Quick run command** | `make test PYTEST_ARGS="tests/<file>.py -q -n0 --no-cov"` |
| **Full suite command** | `make verify` (ruff, mypy --strict, lint-imports, no-fake-done, pytest); slow tiers `make pair [SIZE=]`, `make grid [SIZE=]` |
| **Estimated runtime** | about 40 s today (2637 tests); about 80 s once the verify cell (about 35 s, child process) and the watertight sweeps land; `make pair` hours |

---

## Sampling Rate

- **After every task commit:** the pre-commit hook runs `make verify` (every commit green)
- **After every plan wave:** Run `make verify`; after 05-15, `make pair SIZE=M6` locally where the plan says
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds for `make verify` (05-12 and 05-13 stop and surface if the suite passes it)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Task (behaviour) | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | PAIR-03, PAIR-04 | T-05-01, T-05-02, T-05-03 | Derive and pin the expected pair verdicts on the pre-registration branch | tdd | `git merge-base --is-ancestor origin/main gsd/phase-05-preregistration && s=$(git log --format=%s orig...` (main checkout, git plumbing; tests run in the worktree in the action) | W0 (plan creates) | ✅ green — pre-registration landed via PR A (05-03-02 checks origin/main ancestry and `tests/data/pair_expected.tsv`) |
| 05-01-02 | 01 | 1 | PAIR-03, PAIR-04 | T-05-01, T-05-02, T-05-03 | Write the M18 diagnosis protocol and the probe that reads exactly it | auto | `s=$(git log --format=%s origin/main..gsd/phase-05-preregistration) && printf '%s\n' "$s" \| grep -...` (main checkout, git plumbing; tests run in the worktree in the action) | W0 (plan creates) | ✅ green — as 05-01-01; the M18 protocol ran in 05-16-01 |
| 05-01-03 | 01 | 1 | PAIR-03, PAIR-04 | T-05-01, T-05-02, T-05-03 | Open PR A and return to the phase branch | auto | `gh pr view gsd/phase-05-preregistration --json state,baseRefName --jq '.state + " " + .baseRefName'` | n/a | ✅ done — PR A merged (05-03-02) |
| 05-02-01 | 02 | 2 | TYPE-03, THRD-05, INFO-01, INFO-02, FRNT-06 | T-05-04, T-05-05, T-05-06 | Probe the end cuts on the shipped thread and void and record the entry (D-10) | auto | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k oracle"` | yes | ✅ green |
| 05-02-02 | 02 | 2 | TYPE-03, THRD-05, INFO-01, INFO-02, FRNT-06 | T-05-04, T-05-05, T-05-06 | Owner read of ISO 4032, ISO 724, ISO 965-2 and ISO 4753, and the phase rulings | checkpoint | `owner reply, verified read-only` | n/a | ✅ done (05-OWNER-READS.md, rulings R1–R15) |
| 05-02-03 | 02 | 2 | TYPE-03, THRD-05, INFO-01, INFO-02, FRNT-06 | T-05-04, T-05-05, T-05-06 | Record the owner's reads and rulings | auto | `grep -c '^Permanence acknowledged: 20[0-9-]*, permanent: accepted' .planning/phases/05-hex-nut-an...` | n/a | ✅ done (05-OWNER-READS.md) |
| 05-03-01 | 03 | 3 | PAIR-03, PAIR-04 | T-05-07, T-05-08 | Codex reviews PR A | checkpoint | `owner reply, verified read-only` | n/a | ✅ done (owner checkpoint) |
| 05-03-02 | 03 | 3 | PAIR-03, PAIR-04 | T-05-07, T-05-08 | Apply the findings, land PR A, merge origin/main into the phase branch | auto | `gh pr view "$(gh pr list --state merged --head gsd/phase-05-preregistration --json number --jq '....` | n/a | ✅ green |
| 05-04-01 | 04 | 4 | TYPE-03, PAIR-01 | T-05-09, T-05-10, T-05-11 | End-to-end nut with a typed clearance on the API, the CLI, the pool and the page | tracer e2e | `out=$(mktemp -d) && .venv/bin/screw info nut --clearance 0.1 \| .venv/bin/python -c "import json,...` | n/a | ✅ green |
| 05-04-02 | 04 | 4 | TYPE-03, PAIR-01 | T-05-09, T-05-10, T-05-11 | Pin the nut's solid, gates and refusals of a missing clearance | tdd | `make test PYTEST_ARGS="tests/test_nut.py -q -n0 --no-cov"` | W0 (plan creates) | ✅ green |
| 05-05-01 | 05 | 5 | PAIR-01, PAIR-03, TYPE-03 | T-05-12, T-05-13 | The nut's three model rules (root radius with c, thin nut, turn cap on m + 2P) | tdd | `make test PYTEST_ARGS="tests/test_nut.py tests/test_params.py -q -n0 --no-cov"` | W0 (plan creates) | ✅ green |
| 05-05-02 | 05 | 5 | PAIR-01, PAIR-03, TYPE-03 | T-05-12, T-05-13 | The non-positive clearance warning and the nut fine-STL rule | tdd | `make test PYTEST_ARGS="tests/test_calc.py -q -n0 --no-cov -k nut"` | yes | ✅ green |
| 05-05-03 | 05 | 5 | PAIR-01, PAIR-03, TYPE-03 | T-05-12, T-05-13 | Kernel evidence that a positive clearance enlarges the nut's thread on both hand | auto | `make test PYTEST_ARGS="tests/test_nut.py -q -n0 --no-cov -k away_from_the_axis"` | W0 (plan creates) | ✅ green |
| 05-06-01 | 06 | 6 | TYPE-03, INFO-01 | T-05-14, T-05-15, T-05-43 | Transcribe the GOST ISO 4032-2014 rows from page images, then diff against the owner copy | tdd | `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py -q -n0 --no-cov"` | yes | ✅ green |
| 05-06-02 | 06 | 6 | TYPE-03, INFO-01 | T-05-14, T-05-15 | Relation tests per row and the frozen-default row test | tdd | `make test PYTEST_ARGS="tests/test_tables.py tests/test_params.py -q -n0 --no-cov -k 'nut or 4032'"` | yes | ✅ green |
| 05-07-01 | 07 | 7 | TYPE-03, INFO-01 | T-05-16, T-05-17 | The ISO 4032 catalogue on the API, the CLI and the page picker | tdd | `make test PYTEST_ARGS="tests/test_presets.py tests/test_parity.py -q -n0 --no-cov"` | yes | ✅ green |
| 05-07-02 | 07 | 7 | TYPE-03, INFO-01 | T-05-16, T-05-17 | The nut's exact match, cited values, designation and notes on the info document | tdd | `make test PYTEST_ARGS="tests/test_calc.py -q -n0 --no-cov -k nut"` | yes | ✅ green |
| 05-08-01 | 08 | 8 | INFO-01, INFO-02 | T-05-18, T-05-19 | GOST 24705-2004 basic diameters, double-entered, and the basic-profile formulas they agree with | tdd | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_tables.py tests/test_tables_second_entry.py -q -n0 --no-cov"` | yes | ✅ green |
| 05-08-02 | 08 | 8 | INFO-01, INFO-02 | T-05-18, T-05-19, T-05-44 | GOST 16093-2004 deviations and tolerances, double-entered, and the derived 6g and 6H limits | tdd | `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py -q -n0 --no-cov"` | yes | ✅ green |
| 05-09-01 | 09 | 9 | INFO-01, INFO-02, PAIR-01, PAIR-03 | T-05-20, T-05-21 | Pitch and minor diameters on both kinds, and the limits group on an exact size | tdd | `make test PYTEST_ARGS="tests/test_calc.py -q -n0 --no-cov -k 'limits or pitch_diameter'"` | yes | ✅ green |
| 05-09-02 | 09 | 9 | INFO-01, INFO-02, PAIR-01, PAIR-03 | T-05-20, T-05-21 | The nut's pair rows, derived from the section and pinned against it | tdd | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_calc.py -q -n0 --no-cov -k 'flank or...` | yes | ✅ green |
| 05-09-03 | 09 | 9 | INFO-01, INFO-02, PAIR-01, PAIR-03 | T-05-20, T-05-21 | The M18 note from the cited record | tdd | `make test PYTEST_ARGS="tests/test_calc.py -q -n0 --no-cov -k m18"` | yes | ✅ green |
| 05-10-01 | 10 | 10 | TYPE-04, PAIR-01 | T-05-22, T-05-23 | The counterpart key on every info document, with its off-row warnings | tdd | `make test PYTEST_ARGS="tests/test_calc.py tests/test_api.py tests/test_parity.py -q -n0 --no-cov ...` | yes | ✅ green |
| 05-10-02 | 10 | 10 | TYPE-04, PAIR-01 | T-05-22, T-05-23 | The generic counterpart link and the page's defaultless-field traps | auto | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` | yes | ✅ green |
| 05-10-03 | 10 | 10 | TYPE-04, PAIR-01 | T-05-22, T-05-23 | Amend 01-UI-SPEC.md for the clearance field, the new groups, the link and the ki | auto | `grep -c 'Matching <kind>' .planning/phases/01-runtime-port-and-walking-skeleton/01-UI-SPEC.md` | n/a | ✅ green |
| 05-11-01 | 11 | 11 | THRD-05 | T-05-24, T-05-25 | The five oracles and their independent identities | tdd | `make test PYTEST_ARGS="tests/test_end_oracles.py -q -n0 --no-cov"` | W0 (plan creates) | ✅ green |
| 05-11-02 | 11 | 11 | THRD-05 | T-05-24, T-05-25 | End models, capped depths, the differential tolerance, and the bench import-back | tdd | `make test PYTEST_ARGS="tests/test_end_oracles.py tests/test_bench.py -q -n0 --no-cov -k 'oracle o...` | W0 (plan creates) | ✅ green |
| 05-12-01 | 12 | 12 | THRD-05 | T-05-26, T-05-27 | The cited fillet radii, double-entered, and their kernel-free copy | tdd | `make test PYTEST_ARGS="tests/test_tables.py tests/test_tables_second_entry.py -q -n0 --no-cov"` | yes | ✅ green |
| 05-12-02 | 12 | 12 | THRD-05 | T-05-26, T-05-27 | Tip cone and fillet ring built, gated whole and by piece, with positive controls | tdd | `make test PYTEST_ARGS="tests/test_solid.py tests/test_calc.py -q -n0 --no-cov -k 'tip or fillet o...` | yes | ✅ green |
| 05-12-03 | 12 | 12 | THRD-05 | T-05-26, T-05-27 | The bolt watertight sweep | auto | `make test PYTEST_ARGS="tests/test_solid.py -q --no-cov -k watertight"` | yes | ✅ green |
| 05-13-01 | 13 | 13 | THRD-05, TYPE-03 | T-05-28, T-05-29 | Countersinks and face chamfers on both nut faces, gated whole and by piece | tdd | `make test PYTEST_ARGS="tests/test_nut.py tests/test_calc.py -q -n0 --no-cov -k 'nut'"` | W0 (plan creates) | ✅ green |
| 05-13-02 | 13 | 13 | THRD-05, TYPE-03 | T-05-28, T-05-29 | The nut catalogue watertight sweep and the crossing assertion | auto | `make test PYTEST_ARGS="tests/test_nut.py -q --no-cov -k 'watertight or crosses'"` | W0 (plan creates) | ✅ green |
| 05-13-03 | 13 | 13 | THRD-05, TYPE-03 | T-05-28, T-05-29 | Rewrite the standing warning now that the ends are modelled | auto | `.venv/bin/screw info bolt \| .venv/bin/python -c "import json,sys; w=json.load(sys.stdin)['warnin...` | n/a | ✅ green |
| 05-14-01 | 14 | 14 | PAIR-03, PAIR-04 | T-05-30, T-05-31, T-05-32 | Move the verdict rule into calc/pair.py and pin it with positive controls | tdd | `make test PYTEST_ARGS="tests/test_pair.py tests/test_bench.py -q -n0 --no-cov"` | W0 (plan creates) | ✅ green |
| 05-14-02 | 14 | 14 | PAIR-03, PAIR-04 | T-05-30, T-05-31, T-05-32 | solid/pair.py with prove and PairReport, and the contract in the same commit | tdd | `make test PYTEST_ARGS="tests/test_pair.py tests/test_import_boundaries.py tests/test_bench.py -q ...` | W0 (plan creates) | ✅ green |
| 05-14-03 | 14 | 14 | PAIR-03, PAIR-04 | T-05-30, T-05-31, T-05-32 | The shipped-solid evidence row beside the verdict | tdd | `make test PYTEST_ARGS="tests/test_pair.py -q -n0 --no-cov -k shipped"` | W0 (plan creates) | ✅ green |
| 05-15-01 | 15 | 15 | PAIR-03, PAIR-04 | T-05-33, T-05-34, T-05-35 | screw pair with honest exit codes, generated flags and no route | tdd | `make test PYTEST_ARGS="tests/test_cli_pair.py tests/test_parity.py tests/test_api.py -q -n0 --no-...` | W0 (plan creates) | ✅ green |
| 05-15-02 | 15 | 15 | PAIR-03, PAIR-04 | T-05-33, T-05-34, T-05-35 | The verify cell, the pair-marked grid, make pair and pair.yml | auto | `make test PYTEST_ARGS="tests/test_pair.py tests/test_grid.py -q --no-cov"` | W0 (plan creates) | ✅ green |
| 05-15-03 | 15 | 15 | PAIR-03, PAIR-04 | T-05-33, T-05-34, T-05-35 | Read the verify cell on ubuntu before anything lands | auto | `gh pr view gsd/phase-05-hex-nut-and-kernel-pair-proof --json isDraft,state --jq '(.isDraft\|tostr...` | n/a | ✅ green — PR #18, ubuntu verify cell `proven`, 167.50 s |
| 05-16-01 | 16 | 16 | PAIR-03, PAIR-04 | T-05-36, T-05-37 | Run the M18 diagnosis and record the finding | auto | `grep -q '^## M18 control diagnosis (Phase 5, D-08)' bench/RESULTS.md && test "$(wc -l < bench/res...` | n/a | ✅ green |
| 05-16-02 | 16 | 16 | PAIR-03, PAIR-04 | T-05-36, T-05-37 | Run the full pre-registered pair grid locally and record it | auto | `grep -q '^## Pair tier (Phase 5, D-07)' bench/RESULTS.md && for s in M2 M2.5 M3 M3.5 M4 M5 M6 M7 ...` | n/a | ✅ green |
| 05-16-03 | 16 | 16 | PAIR-03, PAIR-04 | T-05-36, T-05-37 | Predict, then run, the product cells at the verified m | auto | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k product_cells"` | yes | ✅ n/a by design — no ISO 4032 `m` differs from the recorded one, so no product_cells test exists; the `## Product pair cells` entry is present |
| 05-17-01 | 17 | 17 | FRNT-06 | T-05-38, T-05-39 | State the rule, then run the deviation ladder and record it | auto | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k deviation"` | yes | ✅ green |
| 05-17-02 | 17 | 17 | FRNT-06 | T-05-38, T-05-39 | Set the fine preset by the rule and pin ControlSurfaceDeflection and the deviati | tdd | `make test PYTEST_ARGS="tests/test_mesh.py tests/test_bench.py -q -n0 --no-cov -k 'mesh or deviati...` | W0 (plan creates) | ✅ green |
| 05-17-03 | 17 | 17 | FRNT-06 | T-05-38, T-05-39 | Re-derive the fine-STL caps if the preset moved | auto | `make verify` | n/a | ✅ green — preset kept (0.01 mm, 0.1 rad), no cap re-derived |
| 05-18-01 | 18 | 18 | FRNT-06, TYPE-03, TYPE-04, THRD-05, PAIR-01, PAIR-03, PAIR-04, INFO-01, INFO-02 | T-05-40, T-05-41, T-05-42 | The preview download names its quality, on the API and the CLI | tdd | `make test PYTEST_ARGS="tests/test_parity.py tests/test_cli.py tests/test_api.py -q -n0 --no-cov -...` | yes | ✅ green |
| 05-18-02 | 18 | 18 | FRNT-06, TYPE-03, TYPE-04, THRD-05, PAIR-01, PAIR-03, PAIR-04, INFO-01, INFO-02 | T-05-40, T-05-41, T-05-42 | L15, the overview and the UI contract's remaining strings | auto | `grep -c '^## L15' docs/architecture/decision_log.md && ! grep -q 'No nut yet' docs/architecture/o...` | n/a | ✅ green |
| 05-18-03 | 18 | 18 | FRNT-06, TYPE-03, TYPE-04, THRD-05, PAIR-01, PAIR-03, PAIR-04, INFO-01, INFO-02 | T-05-40, T-05-41, T-05-42 | Requirement, roadmap and state lines, and the debt the phase leaves | auto | `test -f docs/tech_debt/active/2026-10-14-first-pair-yml-dispatch.md && grep -q '2026-10-14-first-...` | n/a | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_pair.py` — created by 05-01 (PAIR-03 pre-registration), extended by 05-14 and 05-15
- [x] `tests/test_nut.py` — created by 05-04 (TYPE-03, PAIR-01)
- [x] `tests/conftest.py` — `part_of` fixture and `REQUIRED_VALUES`, created by 05-04 (a required field)
- [x] `tests/test_end_oracles.py` — created by 05-11 (THRD-05)
- [x] `tests/test_cli_pair.py` — created by 05-15 (PAIR-04)
- [x] `tests/test_mesh.py` — created by 05-17 (FRNT-06)

Framework: existing pytest infrastructure; no install.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Owner read of ISO 4032, 724, 965-2, 4753 and the rulings | TYPE-03, THRD-05, INFO-02, FRNT-06 | purchased standards, owner decisions (D-14); since 2026-10-20 the pending reads are of the free GOST texts L14 maps | 05-02 Task 2 checkpoint; the preconditions of 05-06, 05-07, 05-08, 05-11 and 05-12 |
| Owner copies generated from the GOST text layer, labels fixed by the owner | TYPE-03, INFO-02, THRD-05 | owner action outside the executor's session, so the agent's image transcription stays independent (05-OWNER-READS.md, 2026-10-20) | the preconditions of 05-06, 05-08 and 05-12 check the file and its header line only |
| Codex review of the pre-registration PR | PAIR-03 | the author never reviews (HOW_TO_DEVELOP section 8) | 05-03 Task 1 checkpoint |
| The page: counterpart link, empty clearance, kind switch | TYPE-04, PAIR-01 | no browser in the gate (L01); source assertions cover the code | end-of-phase human check in `/gsd-verify-work` |
| Verify cell on ubuntu-latest | PAIR-04 | platform difference possible (L11) | 05-15 Task 3 reads the CI log |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [ ] Feedback latency < 90s — not met: `make verify` 128–200 s on the shared host (owner accepted 101.65 s as R14; CI time filed as `docs/tech_debt/active/2026-10-20-ci-test-job-tripled-by-two-pair-tests.md`)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-20 (validate-phase audit: 9/9 requirements covered by passing automated tests; per-task quick commands re-run)

## Validation Audit 2026-10-20

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
