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
| 05-19-01 | 19 | 19 | TYPE-03 | T-05-46 | Owner decides how the nut's fine-STL cap treats clearance (R16) | checkpoint | `owner reply, verified read-only` | n/a | ✅ done (R16 in 05-OWNER-READS.md) |
| 05-19-02 | 19 | 19 | TYPE-03 | T-05-47, T-05-49, T-05-50 | Pre-register and run the nut fine-STL cap measurement, and record it | auto | `make test PYTEST_ARGS="tests/test_bench.py -q -n0 --no-cov -k nut_fine_caps"`; records check (30 ladder keys); sha256 in RESULTS.md | yes | ✅ green — 13 passed; records ok (1238 lines); sha256 cited once (re-run 2026-10-21) |
| 05-19-03 | 19 | 19 | TYPE-03 | T-05-45, T-05-46, T-05-48 | Encode the measured caps as the nut's fine-STL refusal, resolve the debt, record L16 | tdd | `make test PYTEST_ARGS="tests/test_thread_maths.py tests/test_calc.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov -k nut_fine_stl"` | yes | ✅ green — 40 passed (re-run 2026-10-21) |
| 05-20-01 | 20 | 20 | TYPE-03 | T-05-56, T-05-57 | A nut narrower than sqrt(3) mm across flats builds; no shipped nut changes (WR-01) | tdd | `make test PYTEST_ARGS="tests/test_nut.py -q -n0 --no-cov -k narrow_nut"` | yes | ✅ green — 9 passed (re-run 2026-10-21); s in (1.732, 3.464) not built by a test, review IN-07 |
| 05-20-02 | 20 | 20 | PAIR-03, PAIR-04 | T-05-52, T-05-53, T-05-54, T-05-55 | The pair rule and the report never believe or print what was not measured (WR-02..04) | tdd | `make test PYTEST_ARGS="tests/test_pair.py tests/test_cli_pair.py -q -n0 --no-cov -k 'not_finite or compared_closed_form or cannot_hold_the_void or re_derived'"`; table re-derivation identical | yes | ✅ green — 36 passed; table identical (re-run 2026-10-21) |
| 05-20-03 | 20 | 20 | PAIR-03, THRD-05 | T-05-58 | Engagement as the exact quotient, the evidence bolt, the countersink comment (WR-05, WR-06, IN-01) | tdd | `make test PYTEST_ARGS="tests/test_pair.py tests/test_end_oracles.py -q -n0 --no-cov -k 'exact_quotient or evidence_bolt or smallest_and_largest_da_over_d or shipped'"` | yes | ✅ green — 24 passed (re-run 2026-10-21) |
| 05-20-04 | 20 | 20 | PAIR-04 | T-05-59 | Record the fixes in L15, file the deferred findings, set every disposition | auto | disposition and debt greps from the plan | n/a | ✅ done — the disposition check was point-in-time: the 2026-10-21 re-review added WR-07, WR-08, IN-05..IN-07 rows (open), so its exact-set assertion no longer holds by design |
| 05-21-01 | 21 | 21 | TYPE-03 | T-05-60, T-05-61, T-05-62 | With the nut's clearance empty, a preset pick holds its row in the selects (G-05-1) | tracer tdd | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` (source assertions); browser behaviour by a scratch Playwright probe | yes | ✅ green — 69 passed (re-run 2026-10-21); behaviour in a browser is manual-only (below) |
| 05-21-02 | 21 | 21 | TYPE-03 | T-05-60 | The UI contract says the selects follow the fields after a failed update | auto | `grep -q 'plan 05-21, gap G-05-1' 01-UI-SPEC.md` and the plan's greps | n/a | ✅ green |
| 05-21-03 | 21 | 21 | TYPE-03 | — | The owner gets the open decision on a browser test in the gate | auto | `test -f docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md` and INDEX grep | n/a | ✅ green |
| 05-22-01 | 22 | 22 | TYPE-04 | T-05-63..T-05-68 | A clearance typed on a nut rides the bolt's Matching nut link, with the L15 amendment (G-05-3) | tracer tdd | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"`; `lastTyped` / no-storage greps | yes | ✅ green (source assertions); review WR-07 and WR-08 closed by plan 05-23 (rows below) |
| 05-22-02 | 22 | 22 | TYPE-04 | T-05-67 | The UI contract describes the matching-part link as built | auto | `grep -q 'plan 05-22, gap G-05-3' 01-UI-SPEC.md` and the plan's greps | n/a | ✅ green |
| 05-23-01 | 23 | 23 | TYPE-04 | T-05-69, T-05-71, T-05-72, T-05-75 | A clearance typed during a kind switch is kept under the form on screen; update() waits for the switch; navigate rebuilds a form that is not the link's kind (WR-07, IN-06, IN-05) | tracer tdd | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` (source assertions); browser behaviour by the plan's scratch Playwright probe (9 FAIL at BASE, 2 after Task 1, PASS after Task 2, outputs in 05-23-SUMMARY.md) | yes | ✅ green — 71 passed (re-run 2026-10-21); behaviour in a browser is manual-only (below) |
| 05-23-02 | 23 | 23 | TYPE-04 | T-05-70, T-05-73, T-05-74 | Reset and a link forget a remembered value the field no longer holds; L15 amendment and UI-SPEC rules describe it (WR-08) | tdd | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov -k forget"`; the plan's decision-log difflib and UI-SPEC greps | yes | ✅ green — included in the 71 passed above |
| 05-24-01 | 24 | 24 | TYPE-04 | T-05-76..T-05-81 | A kind switch takes the old kind's form and picker off screen before it fetches the new ones (WR-09), pinned, with the UI contract | tracer tdd | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` (source assertions); browser behaviour by the plan's scratch Playwright probe (`probe_05_24.py`, outputs in 05-24-SUMMARY.md) | yes | ✅ green — included in the 73 passed below; behaviour in a browser is manual-only (below) |
| 05-24-02 | 24 | 24 | TYPE-04 | T-05-23 | WR-09 recorded fixed in 05-REVIEW-DISPOSITION.md | auto | the plan's disposition ancestor check | n/a | ✅ green |
| 05-25-01 | 25 | 25 | TYPE-04 | T-05-82..T-05-86 | A kind switch takes the whole old part off screen (info panel, Matching link, downloads, status) and refuses a failed switch whole unless overtaken (WR-10, IN-08), pinned, with the UI contract | tracer tdd | `make test PYTEST_ARGS="tests/test_parity.py -q -n0 --no-cov"` (source assertions, IN-08 mutant run 11 ok); browser behaviour by the plan's scratch probe (`probe_05_25.py` 11 FAIL at BASE, PASS after; 05-23/05-24 probes 17/17 and 11/11 before and after, outputs in 05-25-SUMMARY.md) | yes | ✅ green — 73 passed (re-run 2026-10-22); behaviour in a browser is manual-only (below) |
| 05-25-02 | 25 | 25 | TYPE-04 | T-05-82..T-05-86 | WR-10 and IN-08 recorded fixed in 05-REVIEW-DISPOSITION.md | auto | the plan's disposition ancestor check | n/a | ✅ green |

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
| The page: counterpart link, empty clearance, kind switch; the selects after a failed update (G-05-1, 05-21); the typed clearance on the Matching nut link (G-05-3, 05-22) | TYPE-03, TYPE-04, PAIR-01 | no browser in the gate (L01); source assertions cover the code text only; the 05-21/05-22 Playwright probes ran from a scratch dir on spur's venv; a browser test in the gate is an open owner decision (`docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md`) | end-of-phase human check in `/gsd-verify-work`; re-check WR-07 (type a clearance while switching bolt to nut; Back before the catalogue loads) and WR-08 (type 0.1, Reset, open the bolt, read its Matching nut link), both fixed by 05-23; re-check WR-09/WR-10 (block the schema request, then a throttled kind switch, then Matching nut and Back: no old info panel, link, download or status beside the new form; picking any kind retries), fixed by 05-24 and 05-25 |
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

**Re-audit:** 2026-10-21 after plans 05-19 to 05-22 — 12 task rows added, every automated command re-run green; no requirement without automated coverage; the page's browser behaviour stays manual-only (L01).

**Re-audit:** 2026-10-21 after plan 05-23 — 2 task rows added, `tests/test_parity.py` re-run green (71 passed); WR-07/WR-08 browser behaviour stays manual-only (L01), proven by the plan's scratch probe.

**Re-audit:** 2026-10-22 after plans 05-24 and 05-25 — 4 task rows added, `tests/test_parity.py` re-run green (73 passed); WR-09/WR-10 browser behaviour stays manual-only (L01), proven by the plans' scratch probes.

## Validation Audit 2026-10-20

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
