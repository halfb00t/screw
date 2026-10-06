---
phase: "1"
slug: "runtime-port-and-walking-skeleton"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-05"
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (+ pytest-xdist, pytest-cov, httpx2 — installed in 01-01 Task 3 after the owner's legitimacy checkpoint) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`--strict-markers --strict-config`, `xfail_strict`, `filterwarnings = ["error"]`); `[tool.coverage.*]` from 01-09 |
| **Quick run command** | `.venv/bin/python -m pytest tests/<file>.py -q -p no:cacheprovider` (add `-n0 --no-cov` once 01-09 puts `-n`/`--cov` into `make test`) |
| **Full suite command** | `make verify` (ruff, mypy src tests docker [bench scripts], lint-imports, no-fake-done, pytest); `make check` adds in-image smoke and vendor-check (01-06 on) |
| **Estimated runtime** | unmeasured for screw; the tracer suite is seconds, the finished suite with spawned workers and `-n 8 --cov` is measured in 01-09 (spur's comparable gate: 63.6 s warm on its suite) |

---

## Sampling Rate

- **After every task commit:** the touched file's tests (quick command), then `make verify` — the pre-commit hook runs it on every commit anyway
- **After every plan wave:** `make verify` (each wave is one plan; the phase is serial because all plans share one working tree and `.venv`)
- **Before `/gsd-verify-work`:** `make verify` and `make check` green; the 01-04 human-check list walked in a browser
- **Max feedback latency:** one `make verify` run (Bash timeout 600000 ms; gsd's own commit helper times out at 30 s, so commits use plain `git commit`)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | FRNT-01, FRNT-03, INFR-01, INFR-02 | T-01-01, T-01-02, T-01-03, T-01-07 | bound, finite, foreign-field refusal; kernel only in workers | e2e + unit + contract | `.venv/bin/python docker/smoke.py` ; `make verify` | ❌ W0 (created by the task) | ⬜ pending |
| 01-01-02 | 01 | 1 | — | T-01-SC | packages vetted before install | manual (blocking-human) | n/a | n/a | ⬜ pending |
| 01-01-03 | 01 | 1 | FRNT-03 | T-01-04 | same-slot timeout never a 500 | pool (real workers) | `.venv/bin/python -m pytest tests/test_pool.py -q -p no:cacheprovider` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | FRNT-01, FRNT-03 | T-01-08, T-01-09 | 422 naming the field; 503 + Retry-After | API contract | `.venv/bin/python -m pytest tests/test_api.py -q -p no:cacheprovider` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | INFR-01 | T-01-10, T-01-11 | no traceback in records; knobs inventoried | unit + doc grep | `.venv/bin/python -m pytest tests/test_records.py -q -p no:cacheprovider` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 3 | FRNT-04, FRNT-01 | T-01-12, T-01-13 | no abbreviation binding; CLI never imports web layer | CLI + contract | `make verify` ; `.venv/bin/screw info bolt --len 5; test $? -eq 2` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 3 | FRNT-04 | — | N/A | README commands as tests | `.venv/bin/python -m pytest tests/test_cli.py -q -p no:cacheprovider -k readme` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 4 | FRNT-02 | T-01-15, T-01-16 | textContent only; unknown kind builds nothing | API + syntax + smoke + human-check | `.venv/bin/python -m pytest tests/test_api.py -q -k index_and_static` ; node --check on an .mjs copy | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 4 | INFR-01 | T-01-17 | bundle byte-identical to web/ | integration (Node) | `make vendor-check` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 5 | FRNT-05, FRNT-01, FRNT-02, FRNT-04 | T-01-18, T-01-19 | parity non-vacuous; no HTML-string assignment | parity | `.venv/bin/python -m pytest tests/test_parity.py -q -n0 -p no:cacheprovider` and `-n 4` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 5 | FRNT-05 | T-01-18 | three planted drifts go red | negative control | `git diff --quiet -- src/screw tests && .venv/bin/python -m pytest tests/test_parity.py -q -n0 -p no:cacheprovider` | ✅ (after 01-05-01) | ⬜ pending |
| 01-06-01 | 06 | 6 | INFR-01 | T-01-23 | closure proven by smoke at resolve and build | integration (Docker) | `make verify` ; `make smoke` | ❌ W0 | ⬜ pending |
| 01-06-02 | 06 | 6 | INFR-01 | T-01-20, T-01-21, T-01-22 | non-root, read-only, localhost-only, INTERIM mem cap | integration (Docker) | `make up` + curl + `make down` ; `make check` | ❌ W0 | ⬜ pending |
| 01-07-01 | 07 | 7 | INFR-01 | T-01-25, T-01-26, T-01-27 | skip tokens refused; required jobs in sync | unit | `.venv/bin/python -m pytest tests/test_pr_land.py tests/test_skip_tokens.py -q -p no:cacheprovider` | ❌ W0 | ⬜ pending |
| 01-07-02 | 07 | 7 | INFR-01 | T-01-25 | hook active on this clone | hook run | `.venv/bin/pre-commit run no-skip-token --hook-stage commit-msg --commit-msg-filename <file>` | ✅ (after 01-07-01) | ⬜ pending |
| 01-08-01 | 08 | 8 | INFR-01 | T-01-29 | numbers labelled not-a-bound | unit + harness run | `.venv/bin/python -m pytest tests/test_bench.py -q -p no:cacheprovider` ; `make bench.build` | ❌ W0 | ⬜ pending |
| 01-08-02 | 08 | 8 | INFR-01 | T-01-29, T-01-30 | containers torn down | harness run | `make bench.latency` (with `make serve`) ; `make bench.memory` | ❌ W0 | ⬜ pending |
| 01-09-01 | 09 | 9 | INFR-01 | T-01-31 | floor gates the run | gate + negative control | `make test` ; `make test PYTEST_ARGS=--cov-fail-under=100; test $? -ne 0` | ✅ | ⬜ pending |
| 01-09-02 | 09 | 9 | INFR-01, INFR-02 | T-01-32 | every INTERIM knob inventoried | doc audit + gate | D-02 audit command ; `make verify` ; `make check` | ✅ | ⬜ pending |
| 01-10-01 | 10 | 10 | INFR-01 | T-01-33 | owner applies the ruleset after merge | manual (blocking-human) | n/a | n/a | ⬜ pending |
| 01-10-02 | 10 | 10 | INFR-01 | T-01-33, T-01-34, T-01-35 | contexts equal required-jobs.txt; no bypass actors | read-back | `gh api repos/halfb00t/screw/rules/branches/main` compared with required-jobs.txt | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

No separate Wave 0 plan: every test file ships in the same task as the code it tests (AGENTS.md
"new behaviour ships with its tests"). The framework additions are front-loaded in 01-01:

- [ ] `httpx2`, `pytest-xdist`, `pytest-cov` dev extras — 01-01 Task 3, after the 01-01 Task 2 legitimacy checkpoint
- [ ] `tests/conftest.py` (autouse root-logger reset, ported) — 01-01 Task 3
- [ ] `tests/test_smoke.py` deleted when the first real tests land — 01-01 Task 1
- [ ] `tests/test_params.py`, `test_calc.py`, `test_solid.py` — 01-01 Task 1; `test_pool.py` — 01-01 Task 3
- [ ] `tests/test_api.py`, `test_records.py` — 01-02; `test_cli.py` — 01-03; `test_parity.py` — 01-05
- [ ] `tests/test_pr_land.py`, `test_skip_tokens.py` — 01-07; `test_bench.py` — 01-08
- [ ] coverage floor measured on the finished suite — 01-09

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live preview, form, info panel, hash round trip, copy link, downloads in a browser | FRNT-02 | WebGL and clipboard; no browser in the gate (L01) | The seven-step human-check list in 01-04 Task 1, with `make serve` |
| Stale responses never render while typing or switching kind (edge FRNT-02 concurrency, backstop) | FRNT-02 | timing in a real browser | 01-04 human-check step 7 |
| Package legitimacy of httpx2, pytest-xdist, pytest-cov | INFR-01 | supply-chain judgement (blocking-human) | 01-01 Task 2 |
| GitHub ruleset on main | INFR-01 | owner-applied repository setting after the merge (D-11) | 01-10 Task 1; Task 2 reads it back |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (the two blocking-human checkpoints are verified by the next task)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (each test file ships in its own task)
- [x] No watch-mode flags (`gh pr checks --watch` in 01-10 waits on CI, not a test watcher)
- [ ] Feedback latency measured (one `make verify` run; measured in 01-09)
- [ ] `nyquist_compliant: true` set in frontmatter (set by validate-phase after execution)

**Approval:** {pending / approved YYYY-MM-DD}
