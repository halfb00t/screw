---
phase: "02"
slug: "thread-spike"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-09"
---

# Phase 02 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

The register is the union of the `<threat_model>` blocks of plans 02-01..02-08 (authored at plan
time; every disposition is `mitigate`). Verified on 2026-10-09 at ASVS level 1 (grep depth, the
workflow's short-circuit: no open threat, register authored at plan time) by the orchestrator on
`gsd/phase-02-thread-spike-runs` at `e925100`, after the campaign `2026-10-08-a` and plan 02-08.
Line numbers are as of that tree; `bench/thread_spike/` and `bench/quiet.py` are byte-identical to
`origin/main` (`fd40abc`), the code the other CLI reviewed before PR 5 landed.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| owner reply -> `02-SPIKE.md` | a human ruling becomes the protocol every run is judged by | rulings R0-R5, profile pin |
| purchased standard -> repository | licensed ISO text could be copied into a public file | coefficients only |
| worker child stdout -> parent | a crashed or misbehaving kernel process returns text the parent parses | one JSON line per row |
| git remote (`origin/main`) -> guard | the guard's verdict depends on refs fetched from GitHub | protocol blob id |
| temp directory -> disk | each row writes an STL of up to hundreds of MB | STL bytes |
| CLI argument (run id) -> file path | a user-typed id names files under `bench/` | `[a-z0-9-]` run id |
| campaign records -> verdict | the verdict re-reads JSONL that could be edited by hand | JSONL rows, sha256 |
| GitHub (git-only package) -> scratch directory | third-party code executes inside a reference worker | `cq_warehouse` at a pinned sha |
| host repository -> container | `bench/` is mounted into the production image | read-only mount |
| fresh children -> host memory | single rows reach several GB of RSS | peak RSS per child |
| kernel boolean -> pair verdict | an OCCT boolean that can return an empty result with no error decides a proof | common-volume readings |
| campaign driver -> result files | one command writes nine run records | `PREFIX-<block>.jsonl/.md` |
| phase branch -> `main` | the protocol and harness become the immutable reference | squash commit |
| PR title/body -> `main`'s commit message | the squash text lands verbatim | commit message text |
| run output -> `RESULTS.md` | a transcription step between what ran and what the repo claims | block `.md` files verbatim |
| owner's terminal -> campaign | the run happens outside any agent's supervision | the campaign process |
| records -> decision entry | numbers move from JSONL into a locked decision others build on | L11 values with run ids |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-02-01 | R | `02-SPIKE.md` Owner rulings | medium | mitigate | the owner's replies are quoted in `02-SPIKE.md` Owner rulings and in 02-01-SUMMARY; Task 1 was a blocking decision checkpoint, so a missing ruling stopped the plan instead of defaulting | closed |
| T-02-02 | I | `02-SPIKE.md` | low | mitigate | the protocol and L11's Profile section carry the pinned choice and coefficient values only, no clause text (02-01-SUMMARY Threat Flags) | closed |
| T-02-03 | T | `verdict.parse_record` | medium | mitigate | `bench/thread_spike/verdict.py:172` `json.loads`; `:295` "JSON only (never pickle or eval)"; no `pickle`/`eval(` under `bench/thread_spike/` beyond that docstring; the record predicates ran green on 2026-10-09 (`-k 'quiet or ... or row ...'`, 140 passed) | closed |
| T-02-04 | D | `runner.Worker` | medium | mitigate | `bench/thread_spike/runner.py:103` and `:120` `proc.kill()` on the deadline; `:88` child stderr goes to a file (`stderr=self._stderr`), never a pipe; a dead child is one `worker_died` row (no such row occurred in `2026-10-08-a`) | closed |
| T-02-05 | T | `__main__` guard | high | mitigate | `bench/thread_spike/__main__.py:213-215` refuses or prints "protocol guard: held" with no flag to skip it; `:318` smoke labels itself "not a campaign run"; the 2026-10-09 smokes wrote only under `/var/folders/.../screw-spike-smoke-*`; `-k 'guard or results_heading'` 15 passed on 2026-10-09 | closed |
| T-02-06 | E | git subprocess calls | low | mitigate | `bench/thread_spike/__main__.py:169` `subprocess.run(["git", *args], ..., check=False)` with list argv; `git grep shell=True -- bench` finds nothing | closed |
| T-02-07 | D | `measure.mesh_stl` temp files | low | mitigate | `bench/thread_spike/measure.py:55` and `:75` `tempfile.TemporaryDirectory(prefix="screw-spike-")` per mesh | closed |
| T-02-08 | T | `__main__` run id -> `RESULTS_DIR` path | medium | mitigate | `bench/thread_spike/__main__.py:156` `RUN_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")` (fullmatch), paths built under the fixed `RESULTS_DIR`; refusal cases in `tests/test_bench.py` (`-k guard`, green 2026-10-09) | closed |
| T-02-09 | R | JSONL records | medium | mitigate | `bench/thread_spike/__main__.py:1229` `target.open("x")` (exclusive, never overwrites) and `:1769` for the campaign log; the verdict recomputes every class from raw rows (re-run on 2026-10-09 identical to the campaign log); every JSONL sha256 is in `bench/RESULTS.md` (02-07, loop green 2026-10-09) | closed |
| T-02-10 | D | frontier rows (hundreds of MB STLs, several GB RSS) | medium | mitigate | `ROW_TIMEOUT_S` and `FINE_CHECK_CEILING` imported at `bench/thread_spike/__main__.py:93-98` and applied per row (`:239`); the campaign recorded 1025 of 7160 host meshes as unchecked above the ceiling and no timeout row | closed |
| T-02-SC | T | pip install of the ruled-surface package | high | mitigate | 02-04 Task 1 blocking-human checkpoint: owner approved the pinned commit `daa46507ecc429c0e2dce11d9d5ffd09b12a42af`; installed `--no-deps` under `$HOME/.cache/screw-spike/`, outside the repo; `git grep cq_warehouse -- pyproject.toml requirements.txt` finds nothing | closed |
| T-02-11 | T | ruled reference worker | medium | mitigate | `bench/thread_spike/__main__.py:493` `CQW_ENV = "SCREW_SPIKE_CQW"`; the package is importable only in the second worker whose `PYTHONPATH` adds that directory (`:27-28`), and the block refuses when it is absent; `make verify` (import-linter `Contracts: 7 kept, 0 broken.`) never sees it | closed |
| T-02-12 | T | container mount | medium | mitigate | `bench/thread_spike/runner.py:45-55`: list argv ("never a shell string"), `-v .../bench:/probe/bench:ro`, `--rm`, `--name` for `docker_kill`; `Dockerfile:33-34` `useradd --uid 10001` and `USER 10001`; 7160 container rows ran under it in `2026-10-08-a` | closed |
| T-02-13 | D | rss fresh children | low | mitigate | `bench/thread_spike/__main__.py:17` one fresh `--once` child per row under `ROW_TIMEOUT_S`; per-mesh temp directories (T-02-07); 90 rss rows `ok` in `2026-10-08-a` | closed |
| T-02-14 | S | `pair.common` result | high | mitigate | `bench/thread_spike/verdict.py:1325` `PAIR_BAND = 1e-3`; `:1582` a cell is proven only when every control is non-empty within the band, otherwise `inconclusive` (`:1587`, `:1591`); c <= 0 is inconclusive by definition; in `2026-10-08-a-pair` the M18 cells read inconclusive, not proven, which is the mitigation working | closed |
| T-02-15 | D | pair worker teardown | medium | mitigate | `bench/thread_spike/pair.py:28-29` `_KEEP` holds the boolean alive and the worker ends with `os._exit(0)` after flushing; `PAIR_TIMEOUT_S` at `bench/thread_spike/__main__.py:96`, `:392`; 272 cells, no `worker_died` | closed |
| T-02-16 | R | campaign result files | medium | mitigate | `bench/thread_spike/__main__.py:1161` a run id already recorded is refused; `:33` a block that refuses or crashes is logged in `PREFIX-campaign.md`; `-k campaign` 18 passed on 2026-10-09 (the live `plan-check` probe was not re-run: with the protocol landed it would start a real campaign) | closed |
| T-02-17 | T | PR 1 title, body, commits | medium | mitigate | 02-06-SUMMARY: a grep for `skip ci`, `ci skip`, `[skip`, `no ci`, `skip-checks` over PR 5's title and body counted 0; the commit-msg hook "reject GitHub Actions skip tokens" ran on every commit of this branch (last seen on `e925100`) | closed |
| T-02-18 | R | protocol after review | high | mitigate | 02-06-SUMMARY: `059aa59^{tree}` equals `fd40abc^{tree}` (what was reviewed is what landed); `-k protocol` 13 passed on 2026-10-09; every block header of `2026-10-08-a` carries protocol blob `4e1959ea085dae8b7e9e5e29e488e1c64ef0964e` and `check-protocol` reads "held" on 2026-10-09 | closed |
| T-02-19 | E | landing on `main` | medium | mitigate | PR 5 merged by the owner (`mergedBy halfb00t`, 2026-10-08T09:28:22Z) with the required jobs `image`, `test (3.12)`, `vendor-bundle` green; no forced update in the reflog; the main ruleset (01-10) requires those jobs regardless of merge path. Whether `make pr.land` or the GitHub button performed the merge is unverified (02-06-SUMMARY) | closed |
| T-02-20 | T | `RESULTS.md` entries | medium | mitigate | 02-07-SUMMARY: the section was built by `cat` of the run's `.md` files and every fenced block `cmp`-matched its file; the sha256 loop over nine JSONL files against `bench/RESULTS.md` exited 0 on 2026-10-09 | closed |
| T-02-21 | R | quiet-gate claims | medium | mitigate | each block header prints its release line and every reading with its UTC time (31 readings per non-decisive block); the three non-decisive blocks and the by-construction container block are recorded as such and nothing was re-run; the owner's R4 override is stated in `RESULTS.md` and 02-07-SUMMARY | closed |
| T-02-22 | T | harness between review and run | medium | mitigate | `git diff --quiet origin/main -- bench/thread_spike bench/quiet.py` exit 0 on 2026-10-09; the guard held at every block (header `protocol_commit` `fd40abc...`) | closed |
| T-02-23 | T | L11 values | medium | mitigate | `verdict --campaign 2026-10-08-a` re-run (02-08 Task 1 and again on 2026-10-09) is byte-identical to campaign log lines 13-1086; every L11 number names a run id; the owner reviewed the draft at the 02-08 Task 2 checkpoint on 2026-10-09 | closed |
| T-02-24 | R | escape-clause outcome | high | mitigate | `bench/RESULTS.md` `### 2026-10-08-a-verdict` records exit 1 and the output verbatim; the owner's "revise: Phase 5" choice is in `STATE.md` and the `ROADMAP.md` precondition line in the same commit as L11 (`bfd5a45`) | closed |
| T-02-25 | E | `src/` before the decision | medium | mitigate | the SC4 command (`git diff --quiet origin/main -- src/` and the `src/screw` identifier grep exiting 1) exited 0 before the L11 commit and again on 2026-10-09 | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-09 | 26 | 26 | 0 | orchestrator (secure-phase, ASVS 1 short-circuit; no auditor spawned) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log (none)
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-09
