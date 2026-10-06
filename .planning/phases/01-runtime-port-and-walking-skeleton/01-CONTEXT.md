# Phase 1: Runtime Port and Walking Skeleton - Context

**Gathered:** 2026-10-05
**Status:** Ready for planning

<domain>
## Phase Boundary

spur's runtime (`pool`, `records`, `app`, `cli`, `build_errors`, the schema-driven form,
viewer and vendored three.js, `scripts/pr_land.py` + `skip_tokens.py`, the commit-msg hook,
`docker/` + compose, the coverage floor, the `bench/` harness) ported per L07 onto screw's
own parameter model: a `FastenerParams` base, one registered `bolt` kind with `d`, `pitch`,
`length` and a plain unthreaded cylinder, served on the web UI, the HTTP API and the CLI, with
one registry-driven parity test and import-linter contracts 1–5 and 8 in `make verify`.

An internal milestone, never released: version stays `0.0.x`, no tag. No thread, no head, no
table, no nut, no pair check. Phase 2 (thread spike) may run alongside; nothing here waits on
it. Gear modules (`calc.py`, `model.py`, `params.py`, their tests, the regression fixture)
are never copied (L07).

Roadmap wording corrected by this discussion (planner: build to this, not to the loose text):
- SC1 "schema and health under the `bolt` kind path" → the actual shape is D-08 below:
  schema is `/api/schema?kind=`, health is global.
- SC3 "the `main` ruleset [is] in place" → the code lands in this phase; the GitHub ruleset
  is enabled by the owner after the Phase 1 PR merges, as the phase's last manual checkpoint
  (D-11).

</domain>

<decisions>
## Implementation Decisions

### Interim runtime bounds (OPER-01/02/03 are Phase 7; the ported pool needs values to run)
- **D-01:** spur's shipping figures are carried as explicitly labelled **interim** defaults:
  `SCREW_BUILD_TIMEOUT=30` s, `SCREW_BUILD_WORKERS=2`, `SCREW_MAX_QUEUED_BUILDS=2×workers`,
  `SCREW_EXPORT_CACHE_MB=64`, the gzip level spur L19 measured, `SCREW_WORKERS=1` (one
  server process), compose `mem_limit: 4g`. Every such constant carries a comment reading
  `INTERIM` + the spur entry it came from (L17/L19/L34) + "Phase 7 re-sweeps (OPER-02)".
  None is presented as measured for screw. Not measured on the skeleton; not waited for from
  the spike.
- **D-02:** One tech-debt item, `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md`
  (from `docs/tech_debt/TEMPLATE.md`, INDEX row in the same commit), `Severity: must`,
  trigger "Phase 7 operability re-sweep", enumerating every interim knob, its value and its
  spur source so Phase 7 cannot miss one. Resolved in Phase 7's commit per AGENTS.md.
- **D-03:** `compose.yaml` ships `mem_limit: 4g` as interim rather than uncapped: a labelled
  cap beats none, and the skeleton is lighter than the gear corpus 4g was measured on.

### Skeleton shape and frozen defaults
- **D-04:** The `bolt` kind builds a plain cylinder of diameter `d` and length `length`.
  No head, no chamfer, no thread: head dimensions come from ISO 4014/4017 rows in Phase 4
  and bolt ends from ISO 4753 in Phase 5; inventing either now is the plausible number L02
  forbids. `pitch` is a validated model field with no geometric effect until Phase 3.
- **D-05:** Frozen defaults: `d=6.0`, `pitch=1.0`, `length=20.0` (absolute mm, L02).
  — **Reversibility:** one-way — every shareable link omits fields at default; moving a
  default silently rebuilds a different part from an old link. `ASSUMPTION:` 1.0 mm is the
  ISO 262 coarse pitch for M6; Phase 4's ISO 262 row test must assert the default
  `(d, pitch)` equals a row. Phase 5's `defaults mate` test guards the pair.
- **D-06:** Info panel for the skeleton: `d`, `pitch`, `length` echoed; `volume` as the
  closed form π·(d/2)²·length (INFO-03's shape from day one, never the kernel's
  `Volume()`); and a standing entry in `warnings`:
  `walking skeleton: plain unthreaded cylinder, not a product build`. Same document on
  `/api/bolt/info` and `screw info bolt` (parity). Version stays `0.0.x`; no release tag.
- **D-07:** Validation at the model boundary: `d > 0`, `pitch > 0`, `length > 0`, all
  finite. No size or length cap: a cap is an unmeasured number; the interim timeout is the
  backstop; Phase 7 sets caps from the sweep (OPER-03). `pitch >= d` is a Phase 3 question.

### API paths, kind selector, parity proof
- **D-08:** Routes: `GET /api/{kind}/info` and `GET /api/{kind}/model.{stl,step}` written
  explicitly per kind (two five-line routes delegating to one `_serve()`; no route loop —
  mypy `disallow_any_explicit`, L04); `GET /api/schema?kind=` with `kind` required (no
  API-side default); `GET /api/kinds`; `GET /api/health` global. An unknown kind is a 404
  by construction. A field the kind does not define is a `422` naming it (`extra="forbid"`
  on a `Query()` model, research Q1). — **Reversibility:** costly — the URL shape is the
  API contract every consumer and the UI bind to.
- **D-09:** The UI renders a kind selector from `/api/kinds` now, with one entry; the form
  fetches `api/schema?kind=<kind>`; `kind=` omitted in the hash means `bolt`.
  — **Reversibility:** one-way — the hash is the shareable link; an omitted `kind` must
  mean `bolt` forever (L02). Phase 5 adds a nut by a registry entry, not by JS edits.
- **D-10:** The one parity test iterates `KINDS` and asserts, per kind: API schema
  `properties` == the model's fields; a foreign field on `/api/{kind}/info` is a `422`
  naming it; the CLI subparser's flags == the model's fields and a foreign flag exits 2
  naming it; `static/app.js` builds the form from `schema.properties` and contains no
  field-name literal (source assertion, spur's `test_every_key_the_ui_reads...` pattern);
  the hash round-trips every field through generic code. No browser in the gate (L01).
  The test stays in `make verify` for every later phase (SC2).

### Walling `main` and the landing flow
- **D-11:** The wall's code lands in this phase on the phase branch: `scripts/pr_land.py`,
  `scripts/skip_tokens.py` and their tests, the `commit-msg` hook in
  `.pre-commit-config.yaml` (`default_install_hook_types: [pre-commit, commit-msg]`, verify
  pinned to `stages: [pre-commit]`), `.github/workflows/required-jobs.txt`, the `image` and
  `vendor-bundle` CI jobs, `make pr.land`. The GitHub ruleset itself is enabled by the owner
  **after** the Phase 1 PR merges (the `image`/`vendor-bundle` jobs it requires do not exist
  on `main` before that), as the phase's last manual checkpoint, with spur's
  `docs/HOW_TO_DEVELOP.md` §8 `gh api` calls. The planner writes this as a checkpoint task,
  not an automated one. Same commit: a new `Lxx` in `docs/architecture/decision_log.md`
  (walls `main`, cites spur L22/L25), `docs/ideas/2026-10-05-wall-main-like-spur.md` closed
  (INDEX row updated), `docs/HOW_TO_DEVELOP.md` §0 and §9 updated to `make pr.land`.
- **D-12:** Phase 1 lands as one PR from `gsd/phase-01-runtime-port-and-walking-skeleton`
  with plan-level commits on the branch; the reviewer reads per commit. Merged with
  `gh pr merge --squash --delete-branch` (pre-wall, HOW_TO_DEVELOP §9).
- **D-13:** `main` was pushed before the phase PR (this session), so the PR diff is phase
  work only.

### Research-finding resolutions (owner decisions, 2026-10-06, after 01-RESEARCH.md § Findings to Surface)
- **D-14 (F1, amends D-07):** One explicitly `INTERIM`-labelled upper bound on `d` and
  `length`, chosen from the measured table in RESEARCH F1 (everything up to `d=1e5` is
  cheap; `d=1e7` is 25 s and 6.0 GiB RSS, past `mem_limit: 4g`). Carries the D-01 label
  (`INTERIM` + source + "Phase 7 re-sweeps (OPER-02)") and a D-02 debt row; Phase 7
  replaces it from the sweep (OPER-03). D-07's "no cap" is superseded by this; its reason
  ("a cap is an unmeasured number") no longer holds for the skeleton. A value above the
  bound is a `422` naming the field (L02), never a silent clamp.
- **D-15 (OQ1/F8/F2):** Info document is self-describing:
  `PartInfo(kind: str, rows: list[InfoRow], warnings: list[str])`,
  `InfoRow(key: str, label: str, value: float, unit: str)`. The UI renders rows
  generically (no per-kind JS, no field-name literal, D-09/D-10). `volume` is absent from
  `rows` and explained in `warnings` when it cannot be computed honestly (overflow or
  non-finite, F2: `?d=1e200` must not 500). Parity test asserts the same document on API
  and CLI and that no row key is read by name in JS.
- **D-16 (F4):** `pool.py` is ported with the one-guard fix for spur's open same-slot
  timeout race (compare the executor with `self._executors[hash(p) % self.workers]` in
  `_run_with_timeout`'s `except TimeoutError` before touching `_processes`; skip to
  `raise BuildTimeout`) plus a regression test. The divergence from spur is recorded in
  L09 and in `docs/tech_debt/active/2026-10-05-shared-infra-extraction.md` (first change
  that must land in both repos — L07's extraction trigger).
- **D-17 (F5, option a):** Follow L07: `docker/refresh-requirements.sh` output is the
  runtime closure only; ruff, mypy, pytest and import-linter are no longer pinned by
  `requirements.txt`. L08 states that this narrows L06's promise (spur L34 accepted the
  same). No second host-side pin file.
- **D-18 (OQ3):** `make test-image` is not ported (no success criterion names it; A4).
- **D-19 (OQ4):** Two decision-log entries land in this phase: `L08` = the wall of
  `main` (D-11, cites spur L22/L25, records D-17's L06 narrowing); `L09` = registry with
  a frozen default kind, URL shape (D-08), hash `kind=` omitted at default (D-09),
  interim-bounds policy (D-01/D-14), and the `pool.py` divergence (D-16).
- Also adopted from research, planner-level (no owner question): F3 parity-test regex
  restricted to parameter-carrying receivers plus a positive control; F6 CI matrix
  shape and `POST`+`PATCH` ruleset checkpoint with read-back; F9 knob list added to
  D-02's item. F7 (L01 reason) is surfaced only, no Phase 1 action.

### Claude's Discretion
- Env prefix `SPUR_*` → `SCREW_*`; the 503 text says "parts", not "gears".
- The `httpx` dev dependency starlette's `TestClient` needs (research: `starlette 1.7.0`
  refuses without it — verify the exact package name on the pinned stack, then `make lock`).
- Coverage floor: spur L34's rule (`floor(L - max(0.25, S))`, measured on the finished
  skeleton suite, serial baseline vs `-n 8` spread) — pinned in the phase's last plan, never
  a round number; the measurement recorded in `bench/RESULTS.md` or the decision entry.
- `records.py` log fields from `params.model_dump()` plus `kind`.
- `bench/` corpus for the skeleton: a grid over `d × length`; the harness runs, the numbers
  are not bounds (L07).
- Per-kind query subclasses (`BoltModelQuery(BoltParams, _Quality)`) plus one generic
  `strip()` helper, per research Q1; `quality: preview|fine` inherited.
- The checkbox branch for boolean fields lands with the first boolean field (Phase 3), not
  now. `argparse.BooleanOptionalAction` likewise.
- `screw pair` is Phase 5; `screw serve | info | export` here.
- Import-linter contracts landing here: 1 (present), 2, 3, 4, 5, 8 as written in research
  ARCHITECTURE.md § Import-linter contracts; 6 and 7 in Phase 4, 9 in Phase 5.
- Module layout per research § Recommended Project Structure (`calc/`, `solid/` as packages
  from the start; `tables/` absent until Phase 4).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 1 — goal, success criteria 1–4 (read with the two
  corrections in `<domain>`)
- `.planning/REQUIREMENTS.md` — INFR-01, INFR-02, FRNT-01…FRNT-05 (this phase);
  OPER-01…03 (why bounds are interim)
- `.planning/PROJECT.md` § Context — the port list and the spur lessons; § Constraints

### Architecture and research
- `.planning/research/ARCHITECTURE.md` — § Executive answers, § Recommended Project
  Structure, § Import-linter contracts (the nine contracts, which land when),
  § Q1 (registry, per-kind models, `Query()` subclass, `strip()`, hash `kind=`),
  § Q6 (walking skeleton), § Integration Points (ported-code touchpoints that are not
  mechanical retypes; `httpx` dev dependency)
- `.planning/research/SUMMARY.md` — build order, P1 gate output
- `docs/architecture/overview.md` — intended module map
- `docs/architecture/decision_log.md` — L01–L07; L07 is the exact copy list

### House rules
- `AGENTS.md` / `CLAUDE.md` — the gate, L02 rules, debt capture
- `docs/CODING_VALUES.md` — coding standard (read before writing code)
- `docs/HOW_TO_DEVELOP.md` — the loop; §0 and §9 are updated by D-11
- `docs/ideas/2026-10-05-wall-main-like-spur.md` — closed by D-11
- `docs/tech_debt/TEMPLATE.md`, `docs/tech_debt/INDEX.md` — D-02's item

### spur (the house-style reference at `../spur`, HEAD `cd1eddc` = `ec195fb` + one docs commit)
- `../spur/docs/architecture/decision_log.md` — L04 (admission control), L11 (vendored
  three.js), L17 (memory ceiling), L19 (gzip level), L20 (logging), L22 + L25 (ruleset,
  `pr.land`, commit-msg hook), L24 (mesh on a copy), L31 (parity), L34 (coverage floor rule)
- `../spur/docs/HOW_TO_DEVELOP.md` §8 — the exact `gh api` ruleset calls (D-11)
- `../spur/pyproject.toml` — the five contracts, coverage config with its rationale
- `../spur/src/spur/{pool,app,cli,records,build_errors,__init__}.py`, `static/`, `web/` —
  the code to port; `calc.py`, `model.py`, `params.py` are read for pattern only, never copied
- `../spur/scripts/`, `../spur/docker/`, `../spur/Dockerfile`, `../spur/compose.yaml`,
  `../spur/.github/workflows/`, `../spur/.pre-commit-config.yaml`, `../spur/Makefile`
- `../spur/bench/README.md` — the harness method (numbers do not carry)
- `../spur/tests/test_api.py`, `test_cli.py`, `test_pool.py`, `test_pr_land.py`,
  `test_skip_tokens.py`, `test_records.py`, `conftest.py` — test patterns to port

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/screw/__init__.py` stub + `tests/test_smoke.py`: the only code; the smoke test is
  replaced as the first subsystem lands.
- `Makefile`: `venv`, `verify`, `lint`, `typecheck`, `lint-imports`, `no-fake-done`,
  `test`, `lock`, `worktree.*`, `clean` present. Missing vs spur: `serve`, `check`,
  `image`, `test-image`, `smoke`, `up/down/logs`, `bench.*`, `vendor`, `vendor-check`,
  `pr.land`, `clean-docker`.
- `pyproject.toml`: ruff/mypy/pydantic-mypy/pytest blocks final (L04/L05); import-linter
  has contract 1 only; no `[tool.coverage]`; no `httpx` dev dep; `OCP.*` mypy override.
- `.github/workflows/ci.yml`: `test` job only; spur adds `vendor-bundle` and `image`.
- `.pre-commit-config.yaml`: `verify` hook only; no `commit-msg` stage.
- `requirements.txt`: host-side freeze (L06); replaced by `docker/refresh-requirements.sh`
  when the image lands (L07).

### Established Patterns
- `make verify` is the only definition of done; runs in the pre-commit hook (needs `.venv`,
  first build minutes long — commits that trigger it need a long timeout, PROJECT.md lesson).
- Comments carry the measurement or the constraint (CODING_VALUES); an interim value says so.
- `Any` never written; `object` narrowed; pydantic plugin `init_typed`/`init_forbid_extra`.
- Debt/ideas: one file per item + INDEX row in the same commit.

### Integration Points
- `pool` → `solid` by `importlib` inside the worker only (contract 5/8).
- `params` → `calc.feasibility` by lazy import inside the validator (spur pattern).
- `app` → `pool` async `export()`; admission control and bytes cache in `app` only.
- `cli` → `solid` lazy import inside a command (contract 2 allows indirect).
- UI → `/api/kinds`, `/api/schema?kind=`, `/api/{kind}/info`, `/api/{kind}/model.*`.
- gsd: `git.branching_strategy: phase`; branch
  `gsd/phase-01-runtime-port-and-walking-skeleton` already cut from `main` (`1d4bac1`).

</code_context>

<specifics>
## Specific Ideas

- Warning text, verbatim: `walking skeleton: plain unthreaded cylinder, not a product build`.
- Interim knob table (D-01): timeout 30 s, build workers 2, queued builds 2×workers, export
  cache 64 MB, gzip level per spur L19, server workers 1, `mem_limit` 4g.
- Phase 1's last task is a manual owner checkpoint: enable the ruleset after the merge.
- The `L/P` turn count is **not** shown on the skeleton panel: a turns number on an
  unthreaded body would be a plausible number for a feature that does not exist.

</specifics>

<deferred>
## Deferred Ideas

- Boolean form control (checkbox) and `argparse.BooleanOptionalAction` — Phase 3, with
  `left_hand`.
- `screw pair` subcommand — Phase 5.
- Import-linter contracts 6, 7 — Phase 4; contract 9 — Phase 5.
- Runtime bounds measured for threaded parts on linux/amd64 — Phase 7 (D-02's trigger).

</deferred>

---

*Phase: 01-runtime-port-and-walking-skeleton*
*Context gathered: 2026-10-05*
