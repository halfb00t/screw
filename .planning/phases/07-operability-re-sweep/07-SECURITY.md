---
phase: "07"
slug: "operability-re-sweep"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-31"
approved_by: owner
approved: "2026-10-31"
---

# Phase 07 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (21 `07-*-PLAN.md` `<threat_model>` blocks), deduped by id; verified
> at ASVS L1 (grep depth, file:line evidence) against HEAD f3b907d. block_on: high. T-07-71 and
> T-07-72 were registered from the audit's flag after the owner's rulings, and they cite HEAD 6d05169.
> The earlier `scripts/pr_land.py` line numbers are f3b907d's.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| workflow input -> runner shell (07-01) | a dispatcher types the `set` name; it reaches scripts on the runner | free text from a human; untrusted until checked against `[a-z0-9-]+` and an existing file |
| child container -> parent record (07-01) | the child's stdout line becomes a recorded figure | JSON line; numbers that become bounds (integrity-critical, L02) |
| probe -> runner resources (07-01, 07-03, 07-06) | a reading or probe can allocate past the runner's 16 GB, cross the kernel's SIGSEGV wall, or run N workers at once | CPU, memory, wall time |
| client -> pool / serving process (07-02, 07-16, 07-21) | concurrent unauthenticated requests meet the queue, the per-slot deadlines, the caches and the Retry-After hint | request params; worker slots and memory |
| server -> log stream (07-02) | anyone reading `docker logs` sees the records | part fields, fmt, quality, artifact, seconds; no traceback |
| reviewer -> rules (07-03) | the pre-registered protocol decides which numbers become bounds | rules R1-R31, thresholds, seeds |
| phase branch -> main (07-04, 07-20) | only `make pr.land` merges, on green required jobs and the full tier | code and records |
| runner artifact -> repository (07-05, 07-15) | downloaded JSONL becomes the evidence every bound cites | runner records (integrity-critical) |
| executor -> RESULTS (07-05) | prose written by hand next to measured numbers | figures in bench/RESULTS.md |
| records -> generated point sets; model -> point sets (07-05, 07-15) | walk-down, confirm, Runs II and tier sets are derived from readings and the shipped envelope | point files under bench/points, tier-order.json |
| point file -> container argv / environment (07-06, 07-08) | a point's JSON becomes one argv element; a load point's numbers become `-e` elements | validated JSON, integers |
| client -> parameter model (07-07) | an unauthenticated request picks d, pitch and lengths up to the walls | query params |
| records -> constants / model; fit.json -> calc; runtime.json -> code (07-07, 07-09, 07-11, 07-16, 07-21) | committed records decide what the model accepts, refuses and how the service is sized | walls, coefficients, envelopes, budgets, timeouts, runtime knobs |
| instrument server -> runner network (07-08) | the instrument server listens on a published port during a load reading | HTTP on loopback |
| Dockerfile -> probe (07-08) | the probe command is read from the Dockerfile | HEALTHCHECK command |
| owner ruling -> every front end (07-10) | the budget decides refusals on the API, the CLI and the page | B-01/B-02/B-03 rulings |
| client -> refusal / download rule (07-11, 07-13) | a request asks for any part and artifact; a retired cap left reachable would judge by a stale rule | params, artifact; 422 `over_budget` text |
| query keys -> explicit set (07-12) | which fields the request named decides whether a part is capped | raw query keys, CLI flags |
| server text -> page DOM (07-14) | the refusal sentence is shown as status | server-built text |
| container -> host (07-17) | mem_limit and tmpfs bound what one unauthenticated request can take from the host | memory, /tmp |
| PR code -> CI runner / full tier (07-18, 07-19) | a `pull_request` run executes the PR's code with a read-only token | PR code; GITHUB_TOKEN (contents: read) |
| image artifact -> bounds job (07-18) | the image passes between jobs of one run | docker image tarball, bounds records |
| schedule -> main (07-19) | the weekly run measures main | none beyond the full-tier run |
| PR author -> merge gate (07-19) | the author controls the PR's workflow file and its paths filter | workflow YAML, paths |
| gh API -> pr.land (07-19) | the files and runs reads decide whether a merge happens | changed-file list, run status/conclusion |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-07-01 | Tampering | `parse_child_line`, `read_peak` | high | mitigate | NaN/inf/negatives refused, non-ok lines cut to their reason, missing cgroup is `no_cgroup`: bench/oper.py:77, 225-298, 301-340; bench/oper_child.py:74-85, 274-275; tests/test_oper.py:60, 126, 168, 223 | closed |
| T-07-02 | Elevation of privilege | operability.yml | high | mitigate | `permissions: contents: read` (.github/workflows/operability.yml:50-51), no `secrets.`, `set` via env only (:66, :79) and checked in `load_set` (bench/oper.py:90, 811-817); tests/test_oper.py:1071-1097, 543, 548. Dispatch-only trigger superseded by 07-19's schedule + `pull_request` (see T-07-47) | closed |
| T-07-03 | Denial of service | a reading on the runner | medium | mitigate | `--memory`/`--memory-swap` at CAP_BYTES (bench/oper.py:40, 353), DEADLINE_S + `docker kill` (:49, 399), `timeout-minutes: 350` (operability.yml:74, 140) | closed |
| T-07-04 | Denial of service | `_run_with_timeout` deadline | medium | mitigate | deadline = own timeout + pending on slot (src/screw/pool.py:183); pending bounded by `BUILD_QUEUE` BoundedSemaphore(MAX_QUEUED_BUILDS) (src/screw/app.py:141-142, 348); tests/test_pool.py:608 | closed |
| T-07-05 | Denial of service | `_pending` lists | high | mitigate | removal in `finally` (src/screw/pool.py:246-249); autouse fixture asserts empty lists after every test (tests/test_pool.py:88-106) | closed |
| T-07-06 | Information disclosure | `cost_model.miss` record | low | mitigate | part fields, fmt, quality, artifact, timeout_s only (src/screw/records.py:222-235); tests/test_records.py:167-188 (`"traceback" not in record`, :183) | closed |
| T-07-07 | Denial of service | `tail` probe below 1e-8 mm | medium | mitigate | guard lowered only inside the probe, restored in `finally` (bench/oper_child.py:140-152); non-zero exit is `crashed` (bench/oper.py:320); tests/test_oper.py:1388, 1408 | closed |
| T-07-08 | Repudiation | rules tuned after data | high | mitigate | protocol PRs #22 9dea01e, #23 8aa143f, #24 cac3a84, #25 67a9d02 are ancestors of the first reading's GITHUB_SHA a142c27 (bench/results/phase-07/tracer-40645463872 header); R30 07-SWEEP-PROTOCOL.md:650-657; every later rule change labelled and ruled (G25-G37, 07-GAP-RULINGS.md). Codex-review element: see T-07-11 | closed |
| T-07-09 | Tampering | point files drifting from their generator | medium | mitigate | `oper_sets --check` (bench/oper_sets.py:4073-4098) run by tests/test_oper.py:1574-1579 inside `make verify` (Makefile:56) | closed |
| T-07-10 | Tampering | local main history | high | mitigate | main reflog 2026-10-22..10-27 shows only `pull --ff-only` fast-forwards; phase branch merged origin/main as 80d70d7 (parents cd02386, 9dea01e); the refused `git branch -D` follow-up is reported in 07-04-SUMMARY.md Issues | closed |
| T-07-11 | Repudiation | PR A review | medium | accept | AR-04; finding commits exist (23 commits 40f667d..bfb4064); owner rulings recorded (07-04-SUMMARY.md key-decisions); the review texts were kept outside the repo (07-04-SUMMARY.md), and no review record is on PR #22 (`gh pr view 22`: 0 reviews, 0 comments) | accepted (AR-04) |
| T-07-12 | Tampering | RESULTS figures | high | mitigate | RESULTS subsections state the `summarize --reps` command (bench/RESULTS.md:7553-7560); consistency tests: tests/test_runtime_bounds.py:273, 312, 338 (constants vs L23/L24, every cited run id has its RESULTS section). Shipped constants are independently pinned to records (T-07-19, T-07-29, T-07-40) | closed |
| T-07-13 | Repudiation | which commit was measured | medium | mitigate | header carries GITHUB_RUN_ID/JOB/SHA (bench/__init__.py:70-71); each subsection records run id and dispatched sha (bench/RESULTS.md:7553-7555) | closed |
| T-07-14 | Denial of service | runner minutes | low | accept | AR-02; rationale verified: per-reading deadline (bench/oper.py:49) and per-job timeout (operability.yml:74, 140) | accepted (AR-02; signed off by the owner) |
| T-07-15 | Denial of service | contention and drift containers | medium | mitigate | same cap (bench/oper.py:353); drift uses its own deadline (:383); contention builds terminated and `killed` at deadline (bench/oper_bound.py:151, 160-164) | closed |
| T-07-16 | Tampering | point fields reaching the container | medium | mitigate | per-kind key sets and validation (bench/oper.py:109-111, 629-669); point is one argv element of a list (bench/oper.py:353-355); tests/test_oper.py:406-412, 804, 943, 970 | closed |
| T-07-17 | Tampering | memory figure from a scaled single reading | high | mitigate | one contention reading per N (bench/oper_sets.py:1583-1597); mem_limit takes the measured load peak at N and requires 5 ok load reps at that N (bench/oper_sets.py:2504-2525) | closed |
| T-07-18 | Denial of service | a part past the kernel's wall | medium | mitigate | field ceilings and `_turn_cap` at the model (src/screw/params.py:37-55, 66, 208-219; src/screw/calc/thread.py:35, 62); tests/test_params.py:167 at every ceiling | closed |
| T-07-19 | Tampering | constants drifting from evidence | high | mitigate | tests/test_oper_followup.py:971-990 recomputes walls with `derive_walls` and compares to params/thread constants | closed |
| T-07-20 | Repudiation | a debt closed without evidence | low | mitigate | resolved items cite their runs and sha: docs/tech_debt/resolved/2026-10-11-root-radius-floor-is-not-the-kernel-boundary.md (runs 40646134133, 40678150220; 683a434), 2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md (a804806) | closed |
| T-07-21 | Information disclosure | published port | low | mitigate | `-p 127.0.0.1::8000` (bench/oper_load.py:104), `rm -f` in `finally` (:551-554); tests/test_oper_load.py:244-255 | closed |
| T-07-22 | Tampering | instrument timeouts leaking into the product | high | mitigate | overrides only in bench/oper_serve.py:88-90; `git diff 80d9cd0 c6b09d4 -- src/` empty; image copies no bench/ (Dockerfile:23-28) | closed |
| T-07-23 | Denial of service | load container | medium | mitigate | same cap (bench/oper_load.py:101), whole reading under deadline (:521), OOM/cap is `capped` with no figures (:555-560) | closed |
| T-07-24 | Tampering | a model tuned toward a pass | high | mitigate | tests/test_oper_fit.py:299 recomputes fit.json from committed records; R11/R12 landed before data (T-07-08) | closed |
| T-07-25 | Denial of service | an under-predicting model admitting a heavy part | high | mitigate | envelope covers every fitted point (tests/test_oper_fit.py:110, 323); Runs II widening 54965a0 + tests/test_oper_followup.py:1698; tiers fail on a miss (bench/oper.py:989-995; ci.yml `bounds`; operability.yml `verdict`); timeout backstop (src/screw/pool.py:194; records.cost_model_miss) | closed |
| T-07-26 | Repudiation | who chose the budget | medium | mitigate | 07-OWNER-RULINGS.md:3-5 (table blob sha 5ddf7b8), :14 and :39 (verbatim replies) | closed |
| T-07-27 | Elevation of privilege | an unattended run choosing a published contract | high | mitigate | 07-10-PLAN.md:89, 129, 167 `gate="blocking-human"`, no `auto_select` attribute on any checkpoint | closed |
| T-07-28 | Denial of service | an over-budget part reaching the pool | high | mitigate | `download_refusal` first in `_serve` (src/screw/app.py:517-526, both model routes :484-509) and `cmd_export` (src/screw/cli.py:168-170); G28 band guard (src/screw/calc/cost.py:160-252); tests/test_api.py:1213, 1245 | closed |
| T-07-29 | Tampering | constants drifting from fit.json and B-01 | high | mitigate | emit-constants block (src/screw/calc/cost.py:86-180); tests/test_cost.py:97, 105, 115 | closed |
| T-07-30 | Information disclosure | refusal text | low | mitigate | src/screw/calc/cost.py:304-328 prints no figure; tests/test_cost.py:278 | closed |
| T-07-31 | Tampering | cap moving an explicit value | high | mitigate | explicit set from raw query keys (src/screw/app.py:469-474) and given flags (src/screw/cli.py:93-107); `named()` skip (src/screw/calc/cost.py:369-373); tests/test_api.py:1401, tests/test_cost.py:551, 561, tests/test_cli.py:453 | closed |
| T-07-32 | Denial of service | the cap scan | low | mitigate | kernel-free imports (src/screw/calc/cost.py:10-22); scan bounded by default/step (:379), 39+39 / 51 candidates (:362-364) | closed |
| T-07-33 | Repudiation | a silent cap | medium | mitigate | `_cap_warning` (src/screw/calc/cost.py:397); tests/test_api.py:1372-1396 (info warning + download name), tests/test_cli.py:423, 435 | closed |
| T-07-34 | Tampering | a stale cap path | medium | mitigate | tests/test_thread_maths.py:503-513 pins absence; grep of src/ finds no code hit (one comment, src/screw/app.py:522) | closed |
| T-07-35 | Tampering | refusal text in the DOM | low | mitigate | `setStatus` uses `textContent` (src/screw/static/app.js:519); no `innerHTML` in app.js | closed |
| T-07-36 | Spoofing | a stale mesh shown for a refused part | medium | mitigate | `dropMesh()` on the refused branch (src/screw/static/app.js:575-580); source pin tests/test_parity.py:1140-1158 | closed |
| T-07-37 | Tampering | a set chosen to pass | high | mitigate | Runs II/runtime/full sets regenerated by `--check` (bench/oper_sets.py:3131-3147, 4093); tests/test_oper.py:1574; protocol predates data (T-07-08) | closed |
| T-07-38 | Denial of service | an under-predicted admitted part | high | mitigate | 54965a0 widens fit.json and cost.py together and precedes runtime.json's first commit 5c7e231; B-01 guard stop (bench/oper_sets.py:2236-2240); tests/test_oper_followup.py:1698 | closed |
| T-07-39 | Denial of service | worker count, queue and caches | high | mitigate | non-ok load reps do not qualify (bench/oper_sets.py:2511-2513); tests/test_runtime_bounds.py:56-70 | closed |
| T-07-40 | Tampering | constants drifting from records | high | mitigate | tests/test_runtime_bounds.py:46-53 | closed |
| T-07-41 | Denial of service | clients retrying too early | low | mitigate | src/screw/app.py:147-156; tests/test_runtime_bounds.py:102, 120 | closed |
| T-07-42 | Denial of service | mem_limit and tmpfs | high | mitigate | compose.yaml:27, 33; tests/test_runtime_bounds.py:204-219 (< 16e9, < MemTotal, = runtime.json) | closed |
| T-07-43 | Repudiation | a bound with no source | medium | mitigate | tests/test_runtime_bounds.py:273, 312, 338, 360 | closed |
| T-07-44 | Elevation of privilege | bounds job | high | mitigate | job `permissions: contents: read`, no secret, no `pull_request_target` (.github/workflows/ci.yml:112-120); tests/test_oper.py:3193-3202 | closed |
| T-07-45 | Tampering | image and records artifacts | low | mitigate | image `retention-days: 1` (ci.yml:91-93), same-run download by name (:129-131), records retention 7 (:148); tests/test_oper.py:3205-3222 | closed |
| T-07-46 | Denial of service | a stale boundary set passing | medium | mitigate | tests/test_oper_followup.py:2583-2592 | closed |
| T-07-47 | Elevation of privilege | operability.yml pull_request trigger | high | mitigate | `pull_request` (operability.yml:41), `contents: read` (:50-51), inputs via env (:66, :79); tests/test_oper.py:1062-1097 | closed |
| T-07-48 | Denial of service | runner minutes on every PR | low | mitigate | paths filter (operability.yml:41-46); timeouts (:74, :140) | closed |
| T-07-49 | Repudiation | a missed miss | medium | mitigate | bench/oper.py:989-995; tests/test_oper_followup.py:2826 | closed |
| T-07-50 | Tampering | a PR that edits the workflow's paths to skip the full tier | high | mitigate | diff read against `FULL_TIER_PATHS` (scripts/pr_land.py:78-83, 416-431, 437-458); lists held equal (tests/test_pr_land.py:1186-1192; tests/test_oper.py:1067) | closed |
| T-07-51 | Spoofing | a green run for another sha | medium | mitigate | `?head_sha={sha}` + newest run (scripts/pr_land.py:467, 490); `--match-head-commit` (:596); tests/test_pr_land.py:387 | closed |
| T-07-52 | Denial of service | a gh read failure | low | mitigate | read failure is a refusal (scripts/pr_land.py:450-454, 471-475), refusals stop the merge (:582-586); tests/test_pr_land.py:1141, 1148 | closed |
| T-07-53 | Repudiation | a phase marked done on red gates | medium | mitigate | 07-20-SUMMARY.md:77-107 run ids per gate; `gh run view` confirms 41161227951 (95a99da), 41162982938 and 41162982868 (4a2b536) success | closed |
| T-07-54 | Denial of service | an admitted part over its timeout in production | high | mitigate | full tier green on 95a99da and 4a2b536 (1056/1056 ok); merge gated by `check_full_tier` (scripts/pr_land.py:580) | closed |
| T-07-55 | Tampering | a prediction-moving module left off the path list | medium | mitigate | import-closure test tests/test_pr_land.py:1252-1257; exclusions named in decision_log L27 (plan cites "L25") | closed |
| T-07-56 | Tampering | walk-down and confirm sets | high | mitigate | regenerated from recorded `sources` (bench/oper_sets.py:518, 3150-3166, 4079-4092) | closed |
| T-07-57 | Repudiation | a rule written after the data | high | mitigate | gap rulings G1-G24 landed in #23/#24/#25 before tracer sha a142c27; "Harness fixes" section 07-SWEEP-PROTOCOL.md:736-738; post-reading changes each under a G-ruling | closed |
| T-07-58 | Denial of service | a shard over the job timeout | medium | mitigate | bench/oper_sets.py:515-516, 649-658; tests/test_oper_followup.py:184, 189 | closed |
| T-07-59 | Tampering | contention slot routing | high | mitigate | slot check before build, `SlotMismatch` is `crashed` (bench/oper_bound.py:140-152, 186-188); tests/test_oper_bound.py:113, 129 | closed |
| T-07-60 | Tampering | a lifted or unconfirmed reading raising a wall | high | mitigate | bench/oper_sets.py:1157-1177; tests/test_oper_followup.py:315, 763 | closed |
| T-07-61 | Tampering | environment from point files | medium | mitigate | four `-e` elements from ints (bench/oper_load.py:105-108); validation (bench/oper.py:692-720); tests/test_oper_load.py:244-255 | closed |
| T-07-62 | Tampering | an incomplete point in the fit | medium | mitigate | tests/test_oper_fit.py:130, 157 | closed |
| T-07-63 | Tampering | a set redrawn after a widening | high | mitigate | envelope + sources in tier-order.json and bound.json; tests/test_oper_followup.py:1389-1415; widening commit 54965a0 touches no bench/points file | closed |
| T-07-64 | Denial of service | contention measured below N-way | medium | mitigate | one partner per slot by `hash % N`, empty slot is a stop (bench/oper_sets.py:1583-1596) | closed |
| T-07-65 | Tampering | a value from an incomplete point | high | mitigate | `Read.ok` = reps 1-5 once, all ok (bench/oper_sets.py:2299-2302); `_five_ok` stop (:2334-2342); exit 3 (:4066) | closed |
| T-07-66 | Denial of service | a drift reading that overruns its job | medium | mitigate | bench/oper_sets.py:2866-2870 | closed |
| T-07-67 | Tampering | a shipped knob drifting from runtime.json | high | mitigate | tests/test_runtime_bounds.py:72-171, 174, 360 | closed |
| T-07-68 | Denial of service | an env override that outgrows mem_limit | low | accept | AR-03; rationale verified: re-sweep comments at src/screw/app.py:107, 117, 131-132; src/screw/solid/__init__.py:283-284; compose.yaml:16-17 | accepted (AR-03; signed off by the owner) |
| T-07-69 | Tampering | a required tier redrawn to pass after a widening | high | mitigate | membership from tier-order.json only (bench/oper_sets.py:3193-3238); widening stop (:2236-2240); tests/test_oper_followup.py:2552, 2563, 2583 | closed |
| T-07-70 | Tampering | a near-timeout row passed on one runner instance | medium | mitigate | followup-plan/followup/verdict jobs (operability.yml:116-188), top-level `contents: read`, same-run artifacts only; tests/test_oper_followup.py:2995. Never exercised on the runner (docs/tech_debt/active/2026-10-31-full-tier-follow-up-job-never-run-on-the-runner.md); `verdict` fails closed on an unread follow-up | closed |
| T-07-71 | Tampering | a PR that edits its own full-tier judge (operability.yml, the bench code it runs, the point set) so its own `operability: full` run goes green | high | mitigate | da39988: `GATE_PATHS` (scripts/pr_land.py:104-114) and `gate_refusals` (:464-474) applied to the diff in `check_full_tier` (:502). A PR that touches a listed file is refused unless the owner passes `--owner-approves-gate-change` (:115, :746; Makefile:240-243). Tests: tests/test_pr_land.py:1191-1241 (refused without the flag, allowed with it, unaffected by other diffs, `land()` makes no merge call). Drift: the list is derived from the workflow at tests/test_pr_land.py:1249-1303, and the kinds are pinned at :1306-1316. L28 | closed |
| T-07-72 | Tampering | a PR that edits its own required-job workflow (ci.yml, required-jobs.txt, the `bounds` boundary set) so its own required jobs go green | high | mitigate | 6d05169: `.github/workflows/ci.yml`, `.github/workflows/required-jobs.txt` and `tests/data/oper_boundary.json` added to `GATE_PATHS` (scripts/pr_land.py:104-114), under the same rule and flag. Drift test over ci.yml's `bounds` job: tests/test_pr_land.py:1291-1303. The limit, stated in L28: `test (3.12)` runs the PR's own `make verify`, which is inherent to CI and not guarded. L28 | closed |
| T-07-SC | Tampering | package installs | low | accept | AR-01; requirements.txt unchanged since cc6bccf (pre-07-01). Rationale correction: `actions/upload-artifact@v4` (07-01) and `actions/download-artifact@v4` (07-18) are new to the repo's workflows, not "the same pinned actions as ci.yml and grid.yml" | accepted (AR-01; rationale corrected; signed off by the owner) |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Threat Flags (from SUMMARY.md)

| Plan | Flag | Mapping | Note |
|------|------|---------|------|
| 07-11 | gap: cost model admits out-of-fit head heights | T-07-28 (informational) | Resolved: G28 band guard bc7b2ab (src/screw/calc/cost.py:160-252); debt item moved to docs/tech_debt/resolved/ by 54965a0. |
| others | "None" / restatements of registered ids | — | 07-01, 07-10, 07-20 have no section. |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-07-SC | No Python package is installed or added in phase 7 (requirements.txt and pyproject dependencies unchanged since cc6bccf; the bench parent runs on the bare runner interpreter). Two GitHub first-party actions were added to workflows, `actions/upload-artifact@v4` and `actions/download-artifact@v4`, tag-pinned like every existing action (not SHA-pinned). | owner: "Sign off all three (Recommended)" | 2026-10-31 |
| AR-02 | T-07-14 | Public-repo hosted runners; every reading has a deadline (bench/oper.py:49) and every measure/followup job a 350-minute timeout (operability.yml:74, 140). | owner: "Sign off all three (Recommended)" | 2026-10-31 |
| AR-03 | T-07-68 | `SCREW_BUILD_WORKERS`, `SCREW_MAX_QUEUED_BUILDS`, `SCREW_EXPORT_CACHE_MB` and `SCREW_SOLID_CACHE` overrides are a deployer's documented choice on other hardware (D-16); each comment says the value was measured for the runner-sized container and a deployer who moves it re-sweeps. | owner: "Sign off all three (Recommended)" | 2026-10-31 |
| AR-04 | T-07-11 | The PR A review record is the 23 finding commits 40f667d..bfb4064 together with the owner rulings in 07-04-SUMMARY.md key-decisions. The review texts were kept outside the repo, and none is on PR #22. | owner: "Accept, cite fix commits (Recommended)" | 2026-10-31 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-31 | 71 | 67 (+3 accepted, sign-off pending) | 1 (T-07-11, medium, non-blocking); 0 at or above high | gsd-security-auditor (ASVS L1, HEAD f3b907d) |
| 2026-10-31 | 73 | 73 (69 mitigated, 4 accepted: AR-01..AR-04) | 0 | owner rulings; T-07-71 and T-07-72 registered and closed by quick 261031-ken (HEAD 6d05169) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log (AR-01..AR-03 signed off by the owner; AR-04 accepted by the owner)
- [x] `threats_open: 0` confirmed (no open threat at or above high)
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-31 by the owner

## Security Audit 2026-10-31

| Metric | Count |
|---|---|
| Threats found | 73 |
| Closed | 73 |
| Open | 0 |
