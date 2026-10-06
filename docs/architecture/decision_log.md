# Decision log

Locked decisions. Cite by id (L01, L02, ...). Agents must not re-litigate a logged
decision; to change one, add a new entry that supersedes it and say which.

L01–L06 were taken on 2026-10-05 while scaffolding the repo, before any product code
existed. Where an entry inherits a choice from the sibling project `spur`
(github.com/halfb00t/spur) it names spur's entry (`spur L..`) so the original evidence can
be read there; the reasons that are only true here are stated here.

## L01 — Stack

Python 3.12 only, CadQuery over OpenCascade (`cadquery-ocp`) for the solid, FastAPI +
Pydantic v2 + uvicorn for the API, argparse for the CLI, pytest, Docker, GitHub Actions. A
viewer, when it arrives, is vanilla JS plus a vendored three.js bundle (spur L11).

Reason: the owner's call on 2026-10-05 — screw is spur's sibling (threads and fasteners
instead of gears), aimed at the same users with the same three front ends, so it takes
spur's stack as proven rather than re-deciding it. The 3.12 ceiling is not a preference:
`cadquery-ocp` publishes wheels for nothing newer, and pip otherwise spends minutes trying
to build OpenCascade from source (spur L01, L23). `requires-python = ">=3.12,<3.13"` makes
that checkable: pip refuses instead of failing slowly. The floor equals the ceiling for the
reason spur L23 records — mypy cannot hold a floor below its own `python_version`, so a
lower floor with no interpreter behind it in CI is a floor checked by hope.

Reversibility: costly once code exists. A different kernel is a rewrite of the solid
module; a different web framework is a rewrite of the API layer.

## L02 — The product rules screw inherits

Three rules shape every feature, carried over from spur where they were learned the hard
way:

- **No number is better than a wrong number** (spur L08). A value that cannot be computed
  honestly is reported as a warning and no number — never a plausible one. People cut
  metal to what this tool prints.
- **Defaults are absolute millimetres and do not rescale** (spur L05). Every shareable
  link omits the fields left at default; a default that moved would silently rebuild a
  different part from an old URL.
- **Cap and warn, or refuse — never guess** (spur L03). A dimension that can be trimmed
  without contradicting an explicit choice is trimmed and the trim reported in
  `warnings`. A direct conflict between two things the user set is a `422` naming the
  fields.

Reason: these are the properties that make spur trustworthy, and none of them depends on
the part being a gear. Locking them before the first line of product code means the
parameter model, the maths and the API are designed around them instead of retrofitted.
What the rules apply *to* — which parameters, which defaults — is gsd's to discover in
`.planning/`; this entry fixes the rules, not the values.

## L03 — `make verify` is the gate

`make verify` = ruff + mypy `--strict` + import-linter + an unfinished-work scan + pytest.
No Docker. It runs in three places: a developer's shell, the pre-commit hook, and CI
(`.github/workflows/ci.yml`); `make worktree.land` also runs it on the merged result
before it commits. (spur L13, L34.)

Reason: "it works" has to mean "the checks passed", and there has to be exactly one
command that says so, or agents and humans end up asserting different things.

## L04 — Types are strict from the first line, and `Any` is not written here

mypy `strict = true`, `warn_unreachable`, `ignore-without-code`, and
`disallow_any_explicit = true` on globally — `src`, `tests`, everything the gate checks —
with no per-module override. A genuinely untyped value is `object`, narrowed where it is
used; a value a library already names keeps the library's own alias. The pydantic mypy
plugin runs with `init_typed` and `init_forbid_extra`, without which it writes an explicit
`Any` into every generated model initialiser (spur L21 counted six, one per model).

Reason: spur spent a phase (spur L14 → L21) ratcheting this on after the fact. A
greenfield tree pays nothing to start there, and a ratchet that starts closed cannot grow
an exception.

## L05 — The house lint profile: no formatter, TRY003 off

Ruff runs spur's rule set (`E F W I N UP B SIM C4 PTH TID ARG ERA TRY LOG G PT RUF`) with
`TRY003` ignored and no `D`/`ANN`/`ALL`. `ruff format` is not run and there is no
`make fmt`; `E`/`W` still enforce line length (100) and whitespace.

Reason: TRY003 wants long messages moved into exception classes, and this project's
error messages are the product — they name the offending parameter and say what to change
(spur L15). The formatter choice is consistency, not measurement: spur measured that a
formatter would flatten hand-aligned geometry comments (spur L16), and an agent working
both repos should meet one house style. Revisit here if the codebase grows past what
hand-formatting can hold; the cost of switching is lowest now and rises with every file.

## L06 — `requirements.txt` is the pinned closure, used as a pip constraint

`pyproject.toml` keeps loose ranges. `requirements.txt` is generated by `make lock` (a
fresh venv resolve plus `pip freeze`, no Docker) and is never hand-edited. `make venv` and
CI install with `PIP_CONSTRAINT=requirements.txt` whenever the file exists, so a fresh
checkout resolves exactly the closure the last lock did — including the gate's own tools,
so a ruff or mypy release cannot turn the gate red on its own.

Reason: a reproducible build (same inputs, same result) is a must-have, and the kernel
pair is the thing most likely to move under a regression fixture (spur L34). spur resolves
its closure inside a linux/amd64 container because it feeds a Docker image; screw has no
image yet, so the simpler host-side freeze is enough and is replaced, not patched, when an
image arrives. Constraints pin versions, not wheels, so one file serves macOS/arm64 and
CI's linux/amd64 as long as both have wheels for the pinned versions — CI proves that on
every run.

## L07 — Infrastructure is forked from spur at `ec195fb`, and extracted into a shared package only on a named trigger

Date: 2026-10-05. Decided by the owner in spur's `/gsd-new-milestone` session the same day,
over the alternative of turning spur into a "parts generator".

screw copies spur's infrastructure rather than depending on it. The copy is done in two
cuts: the scaffold took the house rules and the gate's shape; the first phase ports the
runtime. Nothing is extracted into a package shared by both repos until the first time a
fix has to land in both — that trigger, and nothing earlier, is when the duplication
starts costing more than a third repository would
(`docs/tech_debt/active/2026-10-05-shared-infra-extraction.md`, severity `nice`).

**Ported by the scaffold (commit `46315f3`):** the `AGENTS.md`/`CLAUDE.md` shape;
`docs/CODING_VALUES.md`; `docs/HOW_TO_DEVELOP.md`; the `docs/tech_debt/` and
`docs/ideas/` templates and INDEX shape; `.ai_skills/README.md`; `Makefile` (`venv`,
`verify`, `lint`, `typecheck`, `lint-imports`, `no-fake-done` — with `-w` in place of the
`\b` that git grep -E does not implement on macOS — `test`, `lock`, `worktree.*`,
`clean`); `.github/workflows/ci.yml` (the `test` job); `.pre-commit-config.yaml` (the
`verify` hook); the `pyproject.toml` tooling blocks (ruff, mypy, pydantic-mypy, pytest,
import-linter shape); `.gitignore`.

**To port in the first phase, as-is:** `scripts/pr_land.py`, `scripts/skip_tokens.py` and
their tests; the `commit-msg` hook and the `main` ruleset (spur L22, L25); `docker/`
(`Dockerfile`, `compose.yaml`, `smoke.py`, `refresh-requirements.sh`, replacing L06's
host-side freeze); the coverage floor and `pytest-xdist`/`pytest-cov` wiring (spur L34);
`src/spur/static/` and `web/` (the schema-driven form, the viewer, the vendored three.js
bundle, `make vendor` / `vendor-check`, spur L11); the `vendor-bundle` and `image` CI jobs.

**To port with one generalization:** `src/spur/pool.py`, `records.py`, `app.py`,
`cli.py`, `build_errors.py` — each is typed on spur's `GearParams`; retype over screw's
parameter model.

**To port as a harness, not as numbers:** `bench/latency.py`, `memory.py`,
`build_time.py`, `export_cost.py`, `bench/README.md`'s method. Re-sweep the build timeout,
memory limit, gzip level and worker count for threaded parts. None of spur's figures carry.

**Never copied:** `calc.py`, `model.py`, `params.py`, their tests, and the regression
fixture — all involute-gear geometry.

Reason: the two repos share a team, a stack and a working method, and spur's runtime is
measured and proven; re-deriving it would spend a milestone on what is already known.
A shared package now would be a third thing to keep green before either product needs it,
and its API would be guessed from one consumer. The fork is cheap today and the trigger
for undoing it is observable.

Reversibility: moderate. Extraction is a mechanical move once both copies have diverged
only in the typed parameter model; the longer the fork lives, the more they diverge.

## L08 — main is walled: required CI jobs on a current head, a commit-msg hook against skip tokens, and `make pr.land` (narrows L06)

Date: 2026-10-06. Decided by the owner in the Phase 1 discussion (D-11, D-12, D-17, D-19).
A port of spur's L22 and L25, which carry the evidence; this entry says what is ported,
what is different here, and what is deferred.

**The commit-msg hook (spur L22, L25).** `scripts/skip_tokens.py` refuses all six tokens
GitHub Actions honours anywhere in a commit message, subject or body, case-insensitively
and over the whole buffer with no `commit -v` cut (spur L25 removed the cut because a
hand-typed cut line is byte-identical to git's own). A token in a commit that rides into a
squash message silently disables CI for it, which is how two commits reached spur's `main`
with no run. The hook is `no-skip-token` in `.pre-commit-config.yaml`;
`default_install_hook_types: [pre-commit, commit-msg]` makes `pre-commit install` set up
both, and the `verify` hook is pinned to `stages: [pre-commit]` so it runs once per commit
(unpinned it ran twice, spur L22). Each existing clone re-runs `.venv/bin/pre-commit
install` once. `/gsd-ship`'s ship note carries a skip token in its subject, so the hook
refuses it and the commit is made by hand (HOW_TO_DEVELOP §7); the global gsd workflow is
not patched.

**`make pr.land PR=<n>` (spur L22, L25).** `scripts/pr_land.py` refuses unless the PR is
open, based on main, the tree is clean, the head is not behind main, the head's `ci.yml`
run finished `success` with every job in `.github/workflows/required-jobs.txt` green, and
the PR title and body carry no skip token. It then squash-merges exactly the verified head
with `--match-head-commit`, checks that a CI run appeared for the squash commit and tidies
the local branch. It is a tool, not a wall: the window between its read and the merge is
closed by the ruleset's strict up-to-date policy, not by anything the script reads.

**The required jobs, and the one list.** `test (3.12)`, `vendor-bundle`, `image`: every job
in `ci.yml`. The `test` job carries a one-entry `python` matrix so GitHub reports it as
`test (3.12)` (L01 makes 3.12 the only version). `required-jobs.txt` and `ci.yml` change in
one commit; `tests/test_pr_land.py` derives the effective job names from `ci.yml` and fails
when the list disagrees. The scripts and both test files are spur's, byte for byte apart
from the docstring in `scripts/__init__.py`; the recorded `gh api` fixtures in the tests
still name spur's repository because they are transcripts of real incidents.

**The ruleset is applied after the Phase 1 merge, by the owner (D-11).** A ruleset
requiring `vendor-bundle` and `image` cannot be put up before those jobs exist on `main`,
or no PR could ever merge, and a repository setting is not in git. So the code and the
record land in Phase 1; the three commands (squash message = PR title and body, create the
ruleset `default` on `refs/heads/main` with no bypass actors, read it back) are in
`docs/HOW_TO_DEVELOP.md` §9, and plan 01-10 records the ruleset id. The POST body is copied
from spur's live ruleset and was not run against screw; the read-back corrects the doc if
GitHub's accepted shape differs. Phase 1 itself lands before the wall, with `gh pr merge
--squash --delete-branch` (D-12).

**`requirements.txt` is now the runtime closure only (D-17, D-19; narrows L06).** Since
plan 01-06 it is generated by `docker/refresh-requirements.sh` in linux/amd64 (L07) and is
still the pip constraint for every install, but ruff, mypy, pytest, import-linter and
pre-commit are not in it and float. L06's promise that a ruff or mypy release cannot turn
the gate red on its own no longer holds; the kernel pair, the thing that can move a
regression fixture, is still pinned. spur L34 accepted the same trade. A second pin file for
the dev tools would be speculative, so there is none. (L10 pins the four owner-vetted dev tools inside
the extras; the rest still float.)

Reason: the wall is what turns "every commit on main has a green run" from a habit into a
property, and spur proved each piece against a real failed merge before screw has a merge to
fail.

Reversibility: reversible. The ruleset is one `gh api -X DELETE` call, the hook is one
config entry, `pr.land` is one Makefile target; none of them touches product code.

## L09 — Fasteners are a registry of kinds with a frozen default, per-kind URLs, interim runtime bounds, and one deliberate pool divergence from spur

Date: 2026-10-06. Decided by the owner in the Phase 1 discussion (D-01 to D-19). L08 (the
wall of `main`) lands later in the same phase.

**The registry.** Each fastener kind is one frozen, `extra="forbid"` Pydantic model over the
shared `FastenerParams`, registered in `KINDS`. `DEFAULT_KIND = "bolt"` is a literal, not
"whatever the registry lists first", so adding a kind can never move it. Defaults are
`d=6.0`, `pitch=1.0`, `length=20.0`, absolute millimetres (D-05, L02).

**The URLs (D-08).** Explicit per-kind routes over one `_serve()`: `/api/{kind}/info` and
`/api/{kind}/model.{stl,step}`. `/api/schema?kind=` requires `kind` (the API has no
default), `/api/kinds` returns the default and the list, `/api/health` is global. An unknown
kind is a 404 by construction; a field the kind does not define is a 422 naming it, which
is why `quality` is a 422 on the info route.

**The hash (D-09).** The shareable link writes `kind=` only when it differs from the
default. An omitted `kind` means bolt forever, so a link made today still builds the same
part after a second kind exists.

**The info document (D-15).** `PartInfo(kind, rows, warnings)` with self-describing
`InfoRow(key, label, value, unit)`, identical on the API and the CLI, rendered by the UI
with no per-kind code. A value that cannot be computed honestly is absent from `rows` and
explained in `warnings` (L02).

**Interim runtime bounds (D-01, D-14).** spur's measured figures (build timeout, workers,
queue depth, byte-cache budget, gzip level and threshold, `Retry-After`, solid cache,
tessellation) are carried as defaults, each commented `INTERIM` with its spur source, and
none is presented as measured for screw. `INTERIM_MAX_MM = 1e5` bounds `d` and `length`,
taken from the 01-RESEARCH.md F1 memory table plus the worst corner measured in plan 01-01;
above it is a 422 naming the field, never a clamp. Phase 7 re-sweeps all of them
(OPER-01 to OPER-03); `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` lists
every one so none is missed.

**One deliberate divergence from spur (D-16).** `pool.py` guards `_run_with_timeout`'s
timeout branch against a same-slot race: a second timeout on a slot whose executor the
first had already replaced reached for `_processes` after CPython set it to `None` and
surfaced as an `AttributeError`, a 500. spur still carries that race as an open `must`
debt. This is the first change that has to land in both repos, so it is L07's extraction
trigger (recorded in `docs/tech_debt/active/2026-10-05-shared-infra-extraction.md`).

Reason: the registry makes the second kind (a nut) an entry rather than a rewrite while
keeping the route, CLI and form layers generic; explicit routes are the shape mypy
`disallow_any_explicit` (L04) permits where a route loop would not. Freezing the default
kind and the hash rule is what keeps every shared link meaning the same part. The interim
policy is honest about what was not measured instead of waiting on a sweep the skeleton
cannot yet feed, and the pool guard fixes a known 500 now rather than porting the bug.

Reversibility: the defaults and the omitted-`kind` hash rule are one-way (an old link
rebuilds a different part if either moves). The URL shape is costly: every consumer and the
UI bind to it. The interim numbers are reversible by design; replacing them is Phase 7.

## L10 — The owner-vetted dev tools are pinned `==` in the dev extras (narrows L08)

Date: 2026-10-06. Decided by the owner at the Phase 1 security audit (threat T-01-SC).

`httpx2==2.13.1`, `pytest-xdist==3.8.0`, `pytest-cov==7.1.0` and `pre-commit==4.6.2` in
`[project.optional-dependencies] dev` of `pyproject.toml`. The first three are the packages the
owner vetted at the 01-01 Task 2 legitimacy checkpoint; `73a0d13` pinned them in
`requirements.txt` and `ff4b22c` (plan 01-06, D-17) dropped them with the rest of the dev tools
when `requirements.txt` became the runtime closure, leaving `>=` floors only. L08's "no second
pin file" stands: the pin lives in the extras, not in a file. `ruff`, `mypy`, `pytest` and
`import-linter` still float per L08, and so do the transitive dependencies of the four.

Reason: a package vetted by hand at one version is not vetted at the next. With a floor only,
the first release after the vetted one installs into every fresh venv and CI run unvetted — a
supply-chain gate that holds once and then opens. None of the four enters the image, so the pin
costs nothing at runtime.

Reversibility: reversible. Four lines in `pyproject.toml`; bumping one is a deliberate re-vet,
which is the point.
