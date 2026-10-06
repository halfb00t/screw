---
phase: "01"
slug: "runtime-port-and-walking-skeleton"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-06"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

The register is the union of the `<threat_model>` blocks of plans 01-01..01-10 (authored at plan
time). Verified on 2026-10-06 by the security auditor (opus) against the merged tree at `e69d351`
plus the `docs/phase-01-close` branch: `lint-imports --no-cache` printed `Contracts: 6 kept, 0
broken.`; a targeted run of the 21 cited test node IDs printed `35 passed`; the live ruleset was
read back with `gh api`. Line numbers below are as of that tree.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| HTTP client → `app.py` query string | untrusted numbers and field names reach the model boundary | floats, field names |
| `app.py` → spawned worker (`pool.py`) | parameters cross a process boundary into the CAD kernel | validated `BoltParams` |
| browser → `app.js` DOM | API responses (labels, warnings, errors) rendered into the page | strings from `/api/*` |
| URL hash → `navigate()` | a shared link names a kind and fields | `kind=`, field values |
| PyPI / npm → `.venv`, `web/node_modules` | dev and build packages enter the toolchain | package contents |
| compose network → container | the service listens for HTTP | unauthenticated requests |
| developer → `main` | commits, PR text and merges reach the default branch | commit messages, PR bodies, heads |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | D | `params.py` d/length | high | mitigate | `le=INTERIM_MAX_MM` on d and length (`params.py:33,63,84`); `asyncio.wait_for` build timeout (`pool.py:172`, 30 s at `app.py:152`); `BoundedSemaphore` admission queue (`app.py:108,255`); `test_api.py:236` | closed |
| T-01-02 | D | `calc.derive` volume | medium | mitigate | `except OverflowError` + `isfinite` guard (`calc/__init__.py:54-62`); `test_calc.py:36,45` with `model_construct` | closed |
| T-01-03 | T | `/api/bolt/*` query model | medium | mitigate | `extra="forbid"` (`params.py:55`), inherited by `BoltModelQuery` (`app.py:216`); `test_api.py:218,226` | closed |
| T-01-04 | D | `pool._run_with_timeout` | medium | mitigate | identity guard before `_processes` (`pool.py:189`); `test_pool.py:522` | closed |
| T-01-05 | I | build failure responses and logs | low | mitigate | 422 `build_error` body carries `str(exc)` only (`app.py:424-428`); `build_failed` passes no `exc_info` (`records.py:202-219`); `test_records.py:146` | closed |
| T-01-06 | T | Content-Disposition filename | low | mitigate | slug built with `:g` (`params.py:75`); regex tests `test_params.py:91`, `test_api.py:274` | closed |
| T-01-07 | E | app → kernel import path | medium | mitigate | import-linter contract 5 (`allow_indirect_imports=false`, `pyproject.toml:184`) and contract 8 (`:196`), both KEPT | closed |
| T-01-08 | D | `/api/bolt/model.*` under load | medium | mitigate | `test_api.py:306`: saturated queue → 503 `busy`, `Retry-After: 5`; `test_api.py:576`, `test_pool.py:237`: timeout and pool_broken → 503 | closed |
| T-01-09 | T | foreign query fields | medium | mitigate | `test_api.py:218` (info and model routes), `test_parity.py:133` | closed |
| T-01-10 | I | `build.failed` log records | low | mitigate | `test_records.py:146` (no traceback field), `:167` (one physical line) | closed |
| T-01-11 | R | interim knobs with no owner | low | mitigate | `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`: every row has a source; Phase 7 trigger under "Next step" | closed |
| T-01-12 | T | argparse prefix matching | medium | mitigate | `allow_abbrev=False` on all 6 parsers (`cli.py:102,107,117,121,126,129`); `test_cli.py:79` | closed |
| T-01-13 | E | cli → web-serving policy | low | mitigate | contract 3 (`pyproject.toml:165`) KEPT | closed |
| T-01-14 | T | `-o` output path | low | accept | accepted risk R-01-01 (`01-03-PLAN.md:236`) | closed |
| T-01-15 | T | `app.js` rendering of warnings, labels, errors | medium | mitigate | all nodes built with `textContent`/`Object.assign` (`app.js:56,83-89,157-158,184-185`); no HTML sink in `app.js` | closed |
| T-01-16 | T | hash `kind=` naming an unregistered kind | medium | mitigate | `navigate()` refuses an unknown kind, names it via `textContent`, builds nothing (`app.js:111-121`) | closed |
| T-01-17 | T | vendored three.js bundle | medium | mitigate | `make vendor-check` (`Makefile:168-170`); CI `vendor-bundle` job: `npm ci`, rebuild, `git diff --exit-code` (`ci.yml:40-56`); job is in the ruleset | closed |
| T-01-18 | R | the parity test itself | medium | mitigate | `test_parity.py:98` asserts the registry non-empty; `:194` is the teeth control; three planted drifts shown red (`01-05-SUMMARY.md:136-173`) | closed |
| T-01-19 | T | `app.js` HTML injection | medium | mitigate | `test_parity.py:242-245` refuses `innerHTML`, `outerHTML`, `insertAdjacentHTML` | closed |
| T-01-20 | E | container runtime | medium | mitigate | `USER 10001` (`Dockerfile:33-34`); `read_only`, `tmpfs /tmp:size=256m`, `cap_drop: [ALL]`, `no-new-privileges` (`compose.yaml:21-29`). Note: `make smoke` and CI's `docker run` start the image without `read_only`/`cap_drop`; only the uid applies there | closed |
| T-01-21 | S | network exposure without authentication | medium | mitigate | bound to `127.0.0.1:8000:8000` with the "put authentication in front" comment (`compose.yaml:6-8`) | closed |
| T-01-22 | D | container OOM kills every worker and the parent | medium | mitigate | `mem_limit: 4g` (`compose.yaml:20`) plus the D-14 bound (`params.py:33`); Phase 7 re-sweeps | closed |
| T-01-23 | T | closure drift with `--no-deps` | medium | mitigate | fresh resolve then smoke (`refresh-requirements.sh:34-36`); smoke again at image build (`Dockerfile:30`) | closed |
| T-01-24 | T | GitHub Actions pinned by tag, not SHA | low | accept | accepted risk R-01-02 (`01-06-PLAN.md:245`) | closed |
| T-01-25 | T | commit messages and PR text | high | mitigate | `no-skip-token` commit-msg hook (`.pre-commit-config.yaml:13,28-36`, installed at `.git/hooks/commit-msg`); `message_refusals` (`pr_land.py:241-254,467`); `test_pr_land.py:539` | closed |
| T-01-26 | T | merges into `main` | high | mitigate | `head_refusals` refuses a head behind main or any required job not green (`pr_land.py:279-306,466`); server-side ruleset (T-01-33) | closed |
| T-01-27 | T | `required-jobs.txt` vs `ci.yml` drift | medium | mitigate | `test_pr_land.py:269` under `testpaths=["tests"]` in `make verify` | closed |
| T-01-28 | E | a developer bypassing hooks with `--no-verify` | low | accept | accepted risk R-01-03 (`01-07-PLAN.md:245`); the ruleset is live | closed |
| T-01-29 | R | `bench/RESULTS.md` | low | mitigate | `bench/RESULTS.md:18,27,69,116,157` each say "not a bound (L07)" with machine, load and date | closed |
| T-01-30 | D | `bench.memory` containers left running | low | mitigate | `_teardown` runs `docker rm -f` (`bench/memory.py:125-126`), called in `finally` (`:205-210`, `:298-299`) | closed |
| T-01-31 | R | coverage floor | low | mitigate | `fail_under = 94` (`pyproject.toml:136`) with `--cov` in `make test` (`Makefile:105`); negative control exits 2 (`01-09-SUMMARY.md:118-121`, re-run 2026-10-06) | closed |
| T-01-32 | R | interim knobs with no inventory row | low | mitigate | 18 `INTERIM` labels in `src/`, `Dockerfile`, `compose.yaml`, `app.js`; each maps to a row in the D-02 item | closed |
| T-01-33 | T | `main` branch | high | mitigate | ruleset 24563199 `enforcement: active` on `refs/heads/main`: deletion, non_fast_forward, pull_request, required checks with `strict_required_status_checks_policy: true`. Note: `allowed_merge_methods` is `merge, squash, rebase`; squash-only was not part of the declared mitigation | closed |
| T-01-34 | E | ruleset bypass actors | high | mitigate | `"bypass_actors": []`, `"current_user_can_bypass": "never"` | closed |
| T-01-35 | T | ruleset contexts vs `required-jobs.txt` | medium | mitigate | contexts `[image, test (3.12), vendor-bundle]` (integration 15368) equal sorted `required-jobs.txt`; drift test passed | closed |
| T-01-SC | T | package installs in plans 01-01..01-10 | high | mitigate | 01-01: owner approved httpx2 2.13.1, pytest-xdist 3.8.0, pytest-cov 7.1.0 on 2026-10-06 (`01-01-SUMMARY.md:58,153`); the `==` pins were dropped by `ff4b22c` (D-17) and restored in the dev extras by L10 (`pyproject.toml`, together with `pre-commit==4.6.2`; the 01-07 register's "pre-commit is already pinned" was false until L10). 01-04: all 29 `web/package-lock.json` entries identical to spur's (three 0.186.0, esbuild 0.25.12, same sha512), `npm ci` only. 01-06: `ff4b22c` added no package; smoke proves the closure. 01-02, 01-03, 01-05, 01-08, 01-09, 01-10: no new package (01-03 `151cd6f` adds `[project.scripts]` and a contract; 01-09 `5fb4e3d` adds the coverage config) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-01-01 | T-01-14 | `screw export -o` writes into the local user's own filesystem with their own permissions; no privilege boundary is crossed | owner (plan 01-03 approval) | 2026-10-05 |
| R-01-02 | T-01-24 | GitHub Actions in `ci.yml` are pinned by tag, not SHA, inherited from spur's workflow unchanged; out of Phase 1 scope | owner (plan 01-06 approval) | 2026-10-05 |
| R-01-03 | T-01-28 | local hooks are advisory by nature; the server-side ruleset (01-10, live as 24563199) is the control that cannot be bypassed locally | owner (plan 01-07 approval) | 2026-10-05 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-06 | 36 (35 numbered + T-01-SC over 10 plans) | 35 | 1 (T-01-SC, high: vetted dev-tool pins dropped) | gsd-security-auditor (opus), verify mode, ASVS L1 |
| 2026-10-06 | 36 | 36 | 0 | owner chose to re-pin (L10); orchestrator recorded the closure |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-06
