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

## L11 — The thread is a sewn twist-section at K = 3, volumes are `BRepGProp` at eps 1e-6 gated at 9e-5, and the pair proof is not falsifiable at M18 (blocks Phase 5)

Date: 2026-10-09. Decided by the owner at the Phase 2 verdict checkpoint on the
pre-registered rules of `02-SPIKE.md`. Every value below names the
`bench/RESULTS.md` entry (run id) that holds it; the rules that produced it are the ones in
`02-SPIKE.md` (Rules), written before any run. A value the campaign could not establish is
written "not established".

**Profile.** ISO 68-1:2023 basic profile, flat crest and flat root, read by the owner on
2026-10-06 and pinned at the D-01 checkpoint (`02-SPIKE.md`, Owner rulings): H = (sqrt(3)/2) P,
crest flat P/8 at radius d/2, root flat P/4 at radius d/2 - 5H/8, flanks at 60 degrees. Every
measured row builds this section; a profile change re-runs the whole campaign.

**Construction.** The sewn twist-section, segment length K = 3 turns, selected by the K rule
over `2026-10-08-a-ksweep` (`### 2026-10-08-a-verdict`, K section; all three K qualified and K = 3
had the fewest fine triangles at the standard max). Sewing tolerance 1e-4 mm, `MAX_SEGMENTS` 500
and 14 section samples per flank are protocol inputs labelled MEASURED-PRIOR (research probes),
not campaign results; they ran unchanged in every row. Result: the host grid
(`2026-10-08-a-grid`) and the container grid (`2026-10-08-a-container`), both hands, rod and
void, read ok on every row, with 1025 of 7160 host meshes unchecked above the 1 000 000-triangle
check ceiling (a skipped check is not a pass for its mesh). The frontier walk
(`2026-10-08-a-frontier`) reached 250 turns with no stop for all 15 sizes and both hands; the
run is non-decisive, so it applied no clock stop. Reference rows: the one-pipe twist reads
inverted at the 160-turn step on 8 of the 8 sizes tried there (`2026-10-08-a-controls`) and the
ruled-surface reference reads silent_wrong against the pinned closed form (its profile is not
the pinned one); neither is a candidate.

**Volume estimator.** `BRepGProp.VolumeProperties_s` at eps 1e-6 (`precise`), never the default
`Volume()`. Rule `select_estimator` over `2026-10-08-a-grid`: largest absolute error 8.147e-06
against the closed form; the shipped gate is `T_gate` = 9e-05 (`GATE_FACTOR` 10 times the winner's
largest error, rounded up to one significant figure) (`### 2026-10-08-a-verdict`, Volume estimator
section). Phase 3's postcondition compares the precise volume to the closed form inside `T_gate`,
sign included.

**Turn cap per size.** Phase 3's cap-and-warn input is the smallest of the three columns. The
construction cap is from `2026-10-08-a-frontier`; the bytes cap is the largest length below the
first grid row whose fine raw STL plus gzip-1 exceeds the INTERIM 64 MiB budget, from
`2026-10-08-a-grid`; the seconds cap is not established for any size, because the grid run is
non-decisive (owner ruling R4), and nothing was re-run toward a value.

| Size | Construction cap (turns) and stop reason | Bytes cap (mm) | Bytes cap (turns) | First row over the bytes budget (`2026-10-08-a-grid`) | Seconds cap |
|---|---|---|---|---|---|
| M2 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M2.5 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M3 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M3.5 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M4 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M5 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M6 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M7 | 250, no stop up to 250 turns | no row over budget | no row over budget | none | not established |
| M8 | 250, no stop up to 250 turns | 67.5 | 54 | M8 right L=68 rod | not established |
| M10 | 250, no stop up to 250 turns | 56 | 37.3333 | M10 right L=57 rod | not established |
| M12 | 250, no stop up to 250 turns | 60 | 34.2857 | M12 right L=61 rod | not established |
| M14 | 250, no stop up to 250 turns | 58 | 29 | M14 right L=59 rod | not established |
| M16 | 250, no stop up to 250 turns | 52 | 26 | M16 right L=53 rod | not established |
| M18 | 250, no stop up to 250 turns | 65 | 26 | M18 right L=66 rod | not established |
| M20 | 250, no stop up to 250 turns | 64 | 25.6 | M20 right L=65 rod | not established |

"No row over budget" means no grid row up to min(10 d, 200 mm) exceeded the budget; it says
nothing beyond the grid. The bytes budget is the INTERIM fine preset (0.01 mm, 0.1 rad) with
gzip level 1. Phase 3 cannot read a seconds cap from this entry.

**Pair check** (`2026-10-08-a-pair`, decisive, locked K = 3; nut heights UNVERIFIED). Falsifiable
on both hands at every size except M18; M18 is **not falsifiable on either hand** (all four proof
clearances 0.05, 0.1, 0.15, 0.2 mm excluded: one control reads empty at one pose in every cell).
Excluded clearances (identical on both hands at every size): M2 0.1, 0.2; M2.5 0.1; M3 0.05,
0.15; M3.5 none; M4 0.05; M5 0.05; M6 none; M7 0.05; M8 none; M10 0.05, 0.1; M12 0.05; M14 0.1;
M16 none; M18 0.05, 0.1, 0.15, 0.2 (all); M20 none. Mixed-hand pair (right-hand rod, left-hand
nut): read violated at every matched pose at every size (4 cells each). Sensitivity (c = -0.05
reads near the closed form): ok at every size and hand. c = 0 is inconclusive by definition. No
same-hand cell read violated. The variant rules and the reference-K rows (K = 5 and 10 at M2,
M6, M10, M20) are reported in `### 2026-10-08-a-verdict` for Phase 5's revision and never
changed the verdict (owner ruling R1).

**Known-bad inputs for THRD-04** (naive `sweep` + `fuse`, one solid, `isValid()` true, precise
volume below half the closed form; `naive_sweep_fuse(d, pitch, length)` in
`bench/thread_spike/helical.py`; `### 2026-10-08-a-verdict`, Controls section;
`2026-10-08-a-controls`): (d=2.0, pitch=0.4, length=4.0), (2.0, 0.4, 10.0), (2.0, 0.4, 20.0),
(2.5, 0.45, 4.5), (2.5, 0.45, 10.0), (3.0, 0.5, 10.0), (6.0, 1.0, 10.0), (8.0, 1.25, 10.0),
(8.0, 1.25, 80.0), (10.0, 1.5, 10.0), (10.0, 1.5, 100.0), (16.0, 2.0, 10.0), (20.0, 2.5, 10.0),
(20.0, 2.5, 20.0), (20.0, 2.5, 200.0). Recipe: the naive row's builder as it stands in
`helical.py` at the commit of this entry. The same control also produced failure rows
(`Null TopoDS_Shape` and one `MakeSolid` error), which a positive-control gate refuses by
raising; the silent rows above are the ones the gate must catch by volume.

**Container.** `screw:latest` (sha256:7d992a89557b01bf2e35e0d368f8b68fd11e9c2774bbdfb45a26f1f7a31638f6) under linux/amd64: 7160 of 7160 rows ok
(`2026-10-08-a-container`, `### 2026-10-08-a-verdict` Container validity); non-decisive by
construction, timings are emulation and feed no bound (D-05); no row timed out.

**Escape clause.** FIRED, by the rule "Phase 5 is not planned until the roadmap is revised
(SC5)": size M18 is not falsifiable (right, left hand) in `2026-10-08-a-pair`. Not fired:
Phase 3's two rules (no failure, worker_died or silent_wrong row inside the standard range in the
host grid or the container; K qualified). The verdict reads "not a pass" (exit 1). Consequence
chosen by the owner on 2026-10-09 ("revise: Phase 5"): Phase 5 is not planned until the roadmap
is revised (via `/gsd-phase`); the owner named no direction for the revision, so the direction is
to be named when Phase 5 is revised. Phase 3 stays plannable and is planned on this entry. No
constant was tuned toward a pass and nothing was re-run to change the outcome.

**Conditions of the record.** The campaign ran on a host other than the registered one (Apple M5
Max, 18 CPUs, 64 GiB, macOS 27.0.1, Python 3.12.15 against the registered M2 Max, 12 CPUs,
32 GiB, Python 3.12.13; kernel pair identical: cadquery 2.8.0, cadquery-ocp 7.9.3.1.1), under
the owner's option A, and with owner ruling R4 overridden (launched from the orchestrating agent
session with other applications open). `ksweep`, `grid`, `frontier` and `container` are
non-decisive, so every seconds claim is not established; `ladder`, `trim`, `controls`, `rss` and
`pair` are decisive. Source: `02-07-SUMMARY.md` Deviations; the head of the `## Thread spike
(Phase 2)` section of `bench/RESULTS.md`.

**Inputs still UNVERIFIED** (the standard unread; labelled so in the protocol and the records):
the ISO 262 coarse pitches (secondary source), the ISO 4017 length cap (10 d, 200 mm), every ISO
4032 nut height m, and the 30 degree tip-chamfer cone (ISO 4753). **INTERIM** (Phase 1 carries,
Phase 7 re-measures): the 30 s build budget, the 64 MiB export budget, the preview (0.08 mm, 0.5
rad) and fine (0.01 mm, 0.1 rad) presets, gzip level 1. Peak RSS figures are a fresh child's for
one row each (`2026-10-08-a-rss`) and bound nothing.

Reason: the sewn twist built every row of the whole grid, both hands, rod and void, in the host
and the container, inside the pre-registered tolerance, and reached the 250-turn ceiling without
a stop, while the comparison constructions failed or read silently wrong where it did not. The
precise volume had the smaller error against the closed form and sets the gate by the
pre-registered factor. The pair check, as pre-registered, cannot be falsified at M18; a Phase 5 planned on it
would claim a proof that cannot fail. The seconds caps are left unestablished rather than filled with a
plausible number (L02).

Reversibility: costly. Phase 3's builder, its postcondition tolerance and its cap-and-warn input
read this entry; changing the construction, K, the estimator or `T_gate` later needs a
superseding entry and a re-run of the affected blocks. The profile pin is one-way (a change
re-runs the whole campaign). The unestablished seconds caps and the INTERIM budgets are
reversible by design: Phase 7 re-measures them.
