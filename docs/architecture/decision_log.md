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

**Known-bad inputs, platform note** (added 2026-10-11, quick 261011-fbb). The list above was
measured on macOS arm64 only (`2026-10-08-a-controls`); the container block ran the shipped
builder, not this control. The naive fuse depends on the platform with identical pins
(cadquery 2.8.0, cadquery-ocp 7.9.3.1.1): CI's ubuntu-latest x86_64 runner (runs 38111898740
and 38112071431) raises `Null TopoDS_Shape` on (6.0, 1.0, 10.0). An ad-hoc re-run of all 15 rows on
2026-10-11, under `screw:latest` (image id 8d0261837661) as linux/amd64 in qemu emulation on an
arm64 host, found ten rows still one solid with `isValid()` true. Five rows differ:
(2.5, 0.45, 4.5), (2.5, 0.45, 10.0), (6.0, 1.0, 10.0) and (8.0, 1.25, 80.0) raise
`Null TopoDS_Shape`, and (20.0, 2.5, 200.0) is two solids. That re-run is an emulation figure,
ad hoc and not a `bench/RESULTS.md` entry, and it agrees with CI on the test's three rows. So a
row is known-bad for a test only on a platform where it was measured silent: THRD-04's test uses
(2.0, 0.4, 4.0), (8.0, 1.25, 10.0) and (20.0, 2.5, 10.0), which are silent on both platforms.
The decision above is unchanged and the shipped builder is not implicated (container 7160 of
7160 ok). Phase 7's native linux/amd64 re-sweep (OPER-02) is where the controls get measured per
platform: `docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md`.

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

**Escape clause, revision direction** (named by the owner on 2026-10-13 after the Phase 2
verification refresh; ROADMAP Phase 5 revised the same day via `/gsd-phase --edit 5`). Direction:
scope the proof, M18 reads `inconclusive`. The D-14 rule stands as PAIR-03 writes it. Phase 5 ships
the check for every size, and a cell whose control reads empty at any pose returns `inconclusive`
naming the pose and clearance, never `proven`. The CI grid's expected verdicts are pre-registered
from `2026-10-08-a-pair` before the first Phase 5 run: M18 `inconclusive` on both hands at K = 3,
and each size's excluded clearances outside its proven set. The M18 nut ships; the M18 pair is
unproven in v1 and labelled so from the cited record, not from a kernel call. The failing reading
is one control pose, theta -2pi/3 on the right hand and +2pi/3 on the left, 0 solids at every
clearance including c = -0.05 and c = 0, with no boolean error or warning (`2026-10-08-a-pair`, M18
tables): the same pose on all twelve M18 cells, one observation each; whether the kernel repeats it
is not established and is the diagnosis task's to measure. Phase 5 carries one bounded diagnosis task,
its method committed before it runs, that changes no verdict rule. Rejected: amending the rule to the reported variants
(two of three controls; the same-pose c = -0.05 reading as the control), under which every M18 cell
reads proven, because that is a rule chosen after seeing which rule passes (D-17); and a decimal
diagnosis phase with its own campaign, because it costs the WR-03 and IN-02 amendments and a
campaign cycle before any Phase 5 work, and the M18 reading is reproducible from the recorded
cells. Phase 5 is plannable on this entry. No constant was tuned.

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

## L12 — The bolt is the L11 thread behind a gate in screw.solid; turns, root radius and the over-budget fine STL are refused, never trimmed; left_hand is on every kind

Date: 2026-10-10. Decided by the owner in the Phase 3 discussion (D-01 to D-16) and in the
planning rulings D-17 to D-19, both on 2026-10-10. Where a value comes from L11 it names the
`bench/RESULTS.md` run id that holds it; every other figure names its source, and those are
single runs on macOS arm64 under variable load (the "research probe 2026-10-10" and the "planner
probe 2026-10-10"), which bound nothing. This entry measures nothing new (D-15): the cap and gate
values are L11's, restated where the code carries them.

**Builder.** `screw.solid.helical.thread(d, pitch, length, *, clearance, left_hand, k)` is the one
builder, for the rod and for the void (the clearance-grown section Phase 5's nut subtracts). It is
L11's sewn twist-section at K = 3 (`2026-10-08-a-ksweep`, `### 2026-10-08-a-verdict`), moved out of
`bench/thread_spike/` without change of construction; the spike imports it back (D-13, 02 D-18), so
what was measured is what ships. It takes the length in mm and not a turn count, because 130 of 3750
integer-turn rows leave a float tail below 1e-3 mm and `pitch=0.6, length=5.4` leaves 8.9e-16 mm,
which crashes the kernel (research probe 2026-10-10). A tail shorter than `MIN_TAIL_MM` = 1e-3 mm is
folded into the previous segment, so the end face still sits at `z = length`, and a `length` below
`MIN_TAIL_MM`, or NaN, is a `BuildError` before any kernel call (D-17, the "doorway guard"). On the
rows whose float tail drifts, the folded builder agrees with the measured exact-turns builder to
7e-13 relative volume (research probe 2026-10-10, one run). `MIN_TAIL_MM` is INTERIM: the research
probe at `d=6, pitch=1` found `length <= 1e-8` mm kills the process, 3e-8 to 1e-6 mm raises and 1e-5
mm builds, and 1e-3 sits 100 times above the last failing tail; Phase 7 re-measures (OPER-03). Both
ends are plain planar cuts at `z = 0` and `z = length`, as every measured row was (D-16). The
kernel-free maths (the ISO 68-1:2023 basic profile, the closed form, `T_GATE`) lives in
`screw.calc.thread`.

**Gate (THRD-04, D-08).** `check_solid` runs inside the function `lru_cache` wraps, so a refused
build is an exception and is never stored, and the bytes cache only ever puts a returned export;
there is one gate and none in `app.py`. In this order: exactly one solid, `isValid()`, and the
`precise` volume (`BRepGProp.VolumeProperties_s` at eps 1e-6, never the default `Volume()`) within
`T_GATE` = 9e-05 of the closed form, sign kept in the message (L11, `### 2026-10-08-a-verdict`
Volume estimator). The comparison is written `not abs(rel) <= T_GATE` so NaN is refused. The
positive controls are L11's known-bad inputs (`2026-10-08-a-controls`): the naive sweep that the
kernel calls valid, and the inverted one-pipe twist, caught by volume and by sign. The export
checks belong to the same change: `exportStl()` returning False, a STEP status other than
`IFSelect_RetDone` and an STL header that disagrees with its byte length are each a `BuildError`,
which closes the collapsed-solid blocker.

**Caps (D-01 to D-03).** A `length / pitch` above 250, compared as the exact decimals the user typed,
is a 422 naming `length` and `pitch` (L11's construction cap, `2026-10-08-a-frontier`: no stop up to
250 turns at any size, both hands, rod and void; nothing above is measured). The fine STL is refused
above L11's bytes cap, on the seven measured `(d, pitch)` rows only (M8 67.5 mm, M10 56, M12 60,
M14 58, M16 52, M18 65, M20 64; `2026-10-08-a-grid`, right-hand rods: the fine raw STL plus its
gzip level-1 copy, measured over the INTERIM 64 MiB budget at the INTERIM fine preset): a 422 on
the API before the cache, the admission slot and the pool, exit 2 on the CLI before the kernel
import, and a warning on the info document. The preview STL and the
STEP are not capped. An off-row `(d, pitch)` gets the 250-turn cap alone, because a cap from an
unmeasured mapping to the nearest row is the plausible number L02 forbids. L11 says Phase 3's
"cap-and-warn input is the smallest of the three columns"; this entry reads that as the input, and
narrows "cap-and-warn" to a refusal for these two artefacts, because `length` is an explicit choice
and trimming it builds a part the user did not ask for (L02). It is a reading recorded here and not
a superseding entry. The seconds cap is still not established; the INTERIM 30 s timeout stays the
backstop below the 250-turn cap. Since Phase 4 the caps are keyed by hand and read on the built
thread; see L13, which supersedes this cap list (D-21, D-22).

**Pitch (D-04).** The only new `(d, pitch)` refusal is geometric: a root radius `d/2 - 5H/8` at or
below zero (`H = (sqrt(3)/2) * pitch`, zero at `pitch` about `0.9238 d`) is a 422 naming `d` and
`pitch`. There is no ISO 262 coarse check before Phase 4 (contract 6 keeps `params` away from
`tables`) and no lower bound on `length` or `d` in `params`: a collapsed solid is refused by the
gate's volume, and a length the kernel cannot model by the doorway guard above. This closes 01 D-07's
open `pitch >= d` question.

**Hand (D-09).** `left_hand: bool = False` is on `FastenerParams`, the base, not on `BoltParams`:
THRD-01 threads every part and the nut derives from the same `d`, pitch and hand. The default is
frozen (L02) and the hash writes `left_hand=true` only when it is set, so an omitted key means
right-hand forever. The download file name carries `left_hand0` or `left_hand1`. A left-hand rod
passes the same gate as a right-hand one and is proved left-handed by an `isInside` probe on the
helix, because the volume cannot see the hand. A left-hand pair proven by the pair check is
Phase 5's (PAIR-03).

**Links and keys (D-10, D-12).** A repeated query key is a 422 of type `duplicate` before any value
is judged (one app-level dependency), a repeated CLI flag exits 2 naming the option, and the page
refuses a link with a repeated, foreign or unreadable key exactly as it refuses an unknown kind,
naming the key and building nothing. That `#d=abc` is unreadable relies on a browser turning it into
an empty number input, which no test has run (the item's assumption, 03-05).

**Standing warning (D-06) and the info document (D-05).** The skeleton warning is gone. Every bolt
info document starts with `threaded rod: no head, plain-cut thread ends; not a product build`,
asserted on the API, the CLI and the parity test; Phase 4 rewrites it when the head lands and Phase 6
removes it at release. The rows add `turns`, `volume` (the closed form, never the kernel's
`Volume()`), `thread_depth` and `minor_diameter` (labelled "ISO 68-1:2023 basic profile"); a row that
is not a finite number is left out and explained in the warnings. The pitch diameter waits for
Phase 5 (INFO-01).

**Slow tier (D-14).** `tests/test_grid.py` runs L11's corpus (15 sizes, every integer-mm and
integer-turn length up to `min(10 d, 200 mm)`, both hands, rod and void: 7160 rows in 60 cells,
marker `grid`) through `helical.thread` and `check_solid`. It is outside `make verify`
(`addopts` has `-m 'not grid'`), runs by `make grid [SIZE=M6]`, and in `.github/workflows/grid.yml`
on `workflow_dispatch` and a weekly schedule only, with read-only permissions, one job per size. The
workflow is not in `ci.yml` and not in `required-jobs.txt`, so L08's "every job in `ci.yml` is
required" stays true. The corpus is the measured one and is never re-picked. The M3.5 and M4 shards
were run locally as a harness check (`bench/RESULTS.md`, Thread grid tier): every row ok, 131.89 s
and 148.15 s, which are not bounds. The first run on a GitHub runner is not made; the 120 minute job
timeout and the 15 shards are a guess until it is.

**Open, filed.** The in-cap off-row cost is accepted as built (D-18) and recorded, with its
figures, in `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` (must, Phase 7, OPER-03).

Reason: every later kind's builder runs through one gate, so a valid-but-wrong solid cannot reach a
cache, a preview or a download by any front end, and the numbers the tool prints are numbers someone
will cut metal to (L02). Refusing where the user made an explicit choice, and only where L11 measured
a limit, keeps the caps honest: nothing is capped at a value no run produced, and nothing is trimmed
silently. Putting `left_hand` on the base and writing it to the hash only when set keeps every link
made before and after this phase meaning the same part.

Reversibility: costly overall. Every later kind's builder runs through the gate, and loosening
`T_GATE` or changing the construction needs a superseding entry and a re-run of the grid block (L11).
One-way for the `left_hand` field on the base, its default and its hash spelling, which are part of
every shareable link from this phase on. Reversible for the caps and `MIN_TAIL_MM`: one constant and
one validator each, which Phase 7 replaces with measured per-size values (OPER-01, OPER-03).

## L13 — The bolt is an ISO 4014 bolt or ISO 4017 screw built from explicit millimetres; presets fill fields from cited, double-entered rows; the info document traces every number

Date: 2026-10-12. Decided by the owner in the Phase 4 discussion (D-01 to D-24, 2026-10-11), in the
planning rulings D-25 to D-28 and the D-21 clarification (2026-10-11, after `04-RESEARCH.md`'s
Planner Alerts), in the opening read of 2026-10-11 and in the full-copy rulings of 2026-10-12
(`04-OWNER-READS.md`). Every cap value is read from L11's run records, from the run named beside it; every other
figure names a test, a plan summary or the research probe it comes from. This entry measures nothing new
except the head-fuse probe of D-03, which it cites as a probe and not as a bound.

**Geometry (D-01 to D-03).** The head is a plain hex prism: across flats `s`, height `k`, sharp
corners at `s / cos 30 degrees`, no top chamfer and no washer face, because the standards' 15 to 30
degree chamfer is a band and not a number (L02). The top chamfer is superseded by L19 (phase 06.1),
which chamfers the head's top corners. The sharp head's closed form is exact, `(sqrt(3)/2) s^2 k`. The
shank is a plain cylinder of diameter `d`; the L11 thread (`helical.thread`, unchanged) is built
over the built thread `t` only, from the tip, and ends in its plain planar cut, which is fused to
the shank's end face, and the shank to the head's underside: two planar fuses, never a cylinder
over the thread. The closed form of the whole part is `section_area(d, pitch) t + pi (d/2)^2
(length - t) + (sqrt(3)/2) s^2 k`, so `T_GATE` holds as L12 set it; an ISO 4017 screw has
`length - t = 0`. The fuses were not measured by Phase 2, so D-03 asked for a probe first:
`bench/RESULTS.md` `## Head fuse probe (Phase 4, D-03)` (`bench/head_fuse.py`, run 2026-10-11 on
`d876dbd777fe2d7e75e47107d8bd39d707aac12e` with the shank and head fused before the thread, and
re-run 2026-10-12 on `979168d5d68009c113ae1dab0b672057efe38c28` through the shipped `bolt.thread`
and `bolt.assemble` in the product's order, 04-REVIEW WR-01: every geometry column identical)
built seven cases (M2 x 4, M6 x 20, M6 x 30, M10 x 80,
M16 x 160, M20 x 200 and a left-hand M6 x 30) and every one is one valid solid, with a whole-part
volume error of at most 1.6e-06 against `T_GATE` 9e-05 and zero open edges at both qualities; the
head and shank add 1.1 to 26.3 KB to a fine STL of 3.1 to 145 MB. It is a probe: single runs on
macOS arm64 at uncontrolled load, not linux/amd64, and its `s`, `k` and `t` are UNVERIFIED preview
readings used as inputs and not table rows. The ends stay plain planar cuts: the tip chamfer and
the under-head fillet move to THRD-05 (Phase 5) with ISO 4753, which joins the purchase list (D-02),
because an OCCT fillet on a fused junction is the fragile operation nothing measured, its volume
would have to enter the closed form, and a chamfer without ISO 4753 is an invented end (L02, 03
D-16). The standing warning on every bolt info document is now `plain-cut thread ends, no tip
chamfer or under-head fillet; not a product build` (D-04); the text quoted in L12 is the Phase 3
one and stays there as history. Phase 5 rewrites this warning when the ends land and Phase 6
removes its second clause at release. **The bare-thread gate** (RESEARCH Alert 5, taken by the
planner, which tightens L12's gate and so needs no superseding entry): `_build` also checks the bare
thread against its own closed form before the fuse, because the thread is only 0.19 of the volume of
an ISO 4014 M12 x 120 and 0.570 of the default M6 x 20 (04-03 summary), and at 0.19 a thread error of
4.7e-4 passes `T_GATE` on the whole part. It costs one more precise volume (0.44 s at M20 x 200, at
most 0.82 s over the grid, `volume_s` of `2026-10-08-a-grid`, a loaded single run). Its positive
control is a thread wrong by 1.1e-4 to 1.4e-4 that the whole-part check alone passes
(`tests/test_solid.py::test_a_thread_wrong_by_a_part_in_ten_thousand_is_refused_on_the_thread_not_the_whole`).
A thread's hand is probed on the bare thread (`bolt.thread`), not on the fused screw, because OCCT's
`isInside` misreads the fused M3.5 x 5.4 screw although it is valid and inside `T_GATE` (04-03).

**Fields and defaults (D-05 to D-07).** `BoltParams` gains `s`, `k` and `thread_length`, floats in
millimetres named by the ISO symbols, with the words in the schema `title` (`Across flats`, `Head
height`, `Thread length`) and the flags `--s`, `--k`, `--thread-length`; each is `gt=0`, finite and
`le=INTERIM_MAX_MM`, like `d` and `length`. Nothing else became a field: `e`, `dw`, `b`, `ls`, `lg`
and the product grade are read from the matching row or derived. The frozen defaults are the
ISO 4017 M6 x 20 row: `d` 6.0, `pitch` 1.0, `length` 20.0, `s` 10.0, `k` 4.0, `thread_length`
20.0, read by the owner from the purchased ISO 4017:2022 Table 1 (M6, grade A) and ISO 262:2023
Table 1 (first choice, coarse) on 2026-10-11, with `permanent: accepted` typed on its own the same
day (`04-OWNER-READS.md`). `tests/test_params.py::test_the_frozen_defaults_are_the_iso_4017_m6_x_20_row`
pins them against the row, which closes 01 D-05's `ASSUMPTION`. A link made in Phase 3 that omits
the new fields now opens a part with a head (RESEARCH Pitfall 3; 50 tests that pinned the old
default part were updated with it, 04-03). Whether `s` moves to `FastenerParams` for the nut is
Phase 5's call; a move between base and subclass changes no link.

**thread_length (D-08, D-25, D-27).** `thread_length` is measured from the tip, and the thread is
built over `t = built_thread_length(thread_length, length)`, which is `min(thread_length, length)`
except that a plain shank shorter than `MIN_TAIL_MM` (1e-3 mm, now in `calc/thread.py`) is folded
into the thread (D-27); the builder, both closed forms, both caps and `derive` all call it, and the
stored value is never rewritten. A `thread_length` above `length` therefore never changes the part
a link meant: `#length=10` opens a full-thread 10 mm screw and the info document says
`thread_length 20 (default) exceeds length 10: thread built to the full length`; the same text
without `(default)` covers any other value, and a folded shank has its own warning. A thread below
`MIN_TAIL_MM` is a `BuildError` naming `thread_length` and `length` before the kernel runs, and the
info document warns and prints no `turns` or `volume` for it. **Two explicit values are a 422 at
the request boundary, not in the model.** FastAPI 0.142.2 copies every field default into the query
model before validation (`fastapi/dependencies/utils.py:768-776`, a runtime probe in RESEARCH
Alert 1), and `app.py`'s `strip()` rebuilds the model route's parameters with every field, so
`model_fields_set` cannot tell an explicit value from a default on the API. The rule is therefore
one pure `thread_length_conflict(length, thread_length)` in `calc/thread.py`, called by an app-level
dependency (`refuse_thread_length_conflict`, after `refuse_repeated_keys`, `/api/bolt/` paths only)
that raises the 422 `thread_length_conflict` with `ctx.fields` naming both when both keys are in the
raw query and both parse as floats, and by `cli._params` after `--preset` expansion (exit 2); a
parity test asserts the API and the CLI print the same words. **The owner's exception (D-25,
2026-10-11).** L02 says a direct conflict between two explicit values is a 422. At the model level
that is not kept: a `BoltParams(length=10, thread_length=30)` built directly in Python is accepted,
built to `t = min(thread_length, length)` and warned, because the model cannot tell an explicit
value from a default on FastAPI 0.142.2. The owner accepted this exception and no other; on the API
and the CLI two explicit values are still a 422 naming both fields, decided at the request boundary
by the one `thread_length_conflict`. The `(default)` mark in the warning is keyed on the value
(`thread_length` equal to its field default), the only thing a model can test.

**Presets (D-09 to D-12, D-28).** No preset id is in the link, the query or the model: the page
writes the preset's millimetre fields and the part is always rebuilt from them (contract 6 below).
`GET /api/presets?kind=<kind>` returns one kernel-free document built in `calc`
(`{kind, axes, rows}`, axes `Standard`, `Size`, `Length`; each row has `id`, `display`,
`designation`, `picker`, `fields`, `citation`); an unknown kind is the `/api/schema` 404
`unknown_kind`; the model routes stay millimetres-only, so a `preset` key is a 422
`extra_forbidden`. The id grammar is `<standard token>:<size>x<length>` and, as shipped (04-07),
keeps the size as printed with its capital `M` and is case-sensitive: `iso4017:M6x20`, `iso4014:M10x80`
(CONTEXT D-11 wrote lowercase; the plan's regex is the later and more specific statement). The
display is `ISO 4017 M6 × 20`; the second-choice sizes M3.5, M7, M14 and M18 carry their brackets in
the picker, the catalogue `choice`, the badge and the display (`ISO 4017 (M7) × 20`, D-28) and not
in the designation. The CLI has `screw presets <kind>`, which prints the identical document, and
`--preset <id>` on `screw info` and `screw export`: the row is expanded before the model is built,
explicit flags win, the `thread_length` conflict rule runs on the merged values, and an unknown id
exits 2 naming it. `--preset` is the one flag not generated from a field, by a positive rule in
`tests/test_parity.py` (`HAND_WRITTEN`) that a planted stray flag fails. The page has three selects
above the form, each with a blank first option; a pick writes the six fields the row defines
(`d`, `pitch`, `length`, `s`, `k`, `thread_length`), leaves `left_hand` alone and builds at once;
`Reset` is still every field to its frozen default, which is ISO 4017 M6 x 20. **The badge, as
shipped** (04-13, `01-UI-SPEC.md` rule 33): `matches ISO 4017 M6 × 20` while the fields equal a row,
`custom, based on <display>` after an edit, `custom` for a reloaded link that matches no row. The
basis is the last row the part matched exactly (a pick, `Reset`, or an edit that lands on a row),
not only the last pick, so that an edit never reads against a stale row; the consequence is that
editing the default part reads `custom, based on ISO 4017 M6 × 20`. A failed catalogue fetch
refuses the link whole and the picker goes with it, and a change to the blank option is not a pick.
There is no nearest-row inference anywhere (a guessed basis is the plausible number L02 forbids).
The catalogue holds 294 rows, 186 ISO 4017 and then 108 ISO 4014, M2 to M20; that order is the tie
rule, so `match` reports ISO 4017 for a part equal to both (latent today: a screw is threaded to the
head and a bolt only `b` of it).

**Tables (D-13 to D-16).** The owner's precondition was met on 2026-10-11 (purchased ISO 4014:2022,
ISO 4017:2022 and ISO 262:2023 in hand), so rows enter `src/screw/tables/` verified from the first
commit. The package holds ISO 262:2023 Table 1 (the 15 sizes of TABL-05, coarse pitch, choice 2 for
M3.5, M7, M14 and M18), ISO 4017:2022 (18 heads, grade A for every size and grade B for M16, M18
and M20, and 186 lengths up to the 200 mm cap) and ISO 4014:2022 (18 heads, 15 `b` bands and 108
printed `ls,min` / `lg,max` shank cells); the tolerance columns are not stored. Every row carries a
required typed `Source(standard, edition, table, column)` with the table and the column as printed,
so a row without one is a `mypy --strict` error (a test runs `mypy` over a bad and a good file). The
ISO 4014 and ISO 4017 head values are equal per size and grade (the owner's answer A3) and are kept
as separate rows with separate sources, with a test that pins the equality. **Double entry, as it
was done.** The owner typed the M6 lines of the three ISO 262 and ISO 4017 files by hand on
2026-10-11. For the full tables the owner ruled `B` on 2026-10-12, which supersedes D-14's clause
"the owner types one copy" for this phase (`04-OWNER-READS.md`, `## Full copy`): the owner copy was
generated from the purchased PDFs' own text layer (`pdftotext -tsv`, poppler 26.10.0) by
`make_owner_copy.py`, kept beside the copy outside the repository; which lengths belong to which
size (the stepped bold lines) was read by pixel sampling of the rendered page (a white cell is a
standard length), and for ISO 4014 cross-checked against the printed `ls,min` / `lg,max` pair in
each cell; the generator reproduces the owner's hand-typed M6 lines byte for byte, and the series
bounds it produced were reported to the owner and not separately typed. The agent's independent
reading of the rendered page images is the second entry, written before the owner files were copied
into `tests/data/owner/`. The full tables are therefore not owner-typed, and the two copies share
the same PDFs and differ in reading method (text layer plus pixels against the eye on a rendered
image): the double entry catches a reading slip and cannot catch an error in the PDFs themselves.
The pages the agent read are the on-disk preview pages, under the owner's ruling `A - 3.` of
2026-10-11 that they are the same pages as the purchased edition; the rendered pages carry an iTeh
preview watermark, and plan 04-01's prohibition of "the iTeh previews" as a source is read through
that ruling (04-01 summary). The diff was empty at the first run for every file (04-07, 04-09,
04-10 summaries). A test in `make verify` diffs the two copies cell by cell, and every disagreement
is "go read the standard", never a majority vote. On top of it, one pure-data relation test per
catalogue row (`s,min < s`, `dw,min < s,min < e,min < s / cos 30`, `k,min <= k <= k,max`, the head
pitch equals the ISO 262 pitch, the grade from `(d, l)`, `lg,max = l - b` and `ls,min = lg,max - 5 P`
for ISO 4014, the series strictly increasing and equal to the listed lengths between its bounds); no
kernel build per row. **The UNVERIFIED gate** (D-15): `Source` carries a verification marker and
`make verify` fails on any UNVERIFIED row under `src/screw/tables/` (a text scan and a runtime walk
of every row, each with a positive control), so one cannot pass the hook, the CI job or `make
pr.land`; there is no runtime filtering and no version check, every row the catalogue serves is
verified by construction. TABL-04's "release build" is read as every build. **Licence stance**
(D-16): the modules store the numeric values the product needs for M2 to M20 with a typed source per
row; no clause wording, notes, figures or table layout is reproduced, and the catalogue serves the
same numbers; the purchased PDFs and every render of them stay out of git (`.gitignore`: `*.pdf`,
`/.standards/`). The stance is in the `tables` package docstring and in
`docs/architecture/overview.md`. **Contracts 6 and 7**, in `pyproject.toml` with the module: 6,
"The parameters never consult a table", forbids `screw.params` and `screw.calc.thread` (and what
they import) from importing `screw.tables`, indirect imports checked; 7, "Tables are a leaf",
forbids `screw.tables` from importing `screw.params`, `screw.calc`, `screw.solid`, `screw.app`,
`screw.cli`, `screw.records`, `cadquery`, `OCP`, `fastapi`, `pydantic` or `logging`; contract 2 is
widened with `screw.tables`. Import-linter cannot see the package `__init__` edge (RESEARCH Alert 3:
a contract with `screw.params` and `screw.calc.thread` as sources stays KEPT while
`screw/calc/__init__.py` imports a table), so the property that matters has its own control:
`calc/__init__.py` imports no table at top level, `_bolt` imports `screw.calc.presets` inside the
function, and `tests/test_import_boundaries.py` runs fresh `python -I` interpreters that show
`BoltParams()`, `import screw.solid` and `import screw.calc` leave `screw.tables` out of
`sys.modules` while `derive(BoltParams())` puts it in, so the test cannot pass vacuously.

**Info document (D-17 to D-20).** `InfoRow` gains a required `group` (`Shank and thread`, `Head`,
`Part`) and `PartInfo` gains `designation`, `preset` (`status` exact or custom, `id`, `display`) and
`notes`, all required keys on the API and the CLI; the page renders one heading per distinct group
in server order and reads no key by a field or row name (a parity assertion). Rows present always:
`d`, `pitch`, `length`, `thread_length`, the shank length, `turns`, thread depth and minor diameter
(the ISO 68-1:2023 basic profile), `s`, the geometric across corners `s / cos 30 degrees` (labelled
apart from the row's `e,min`), `k`, and the volume (the closed form of the whole part, never the
kernel's `Volume()`). Rows present only on an exact match of every field the row defines: `s,min`,
`e,min`, `k,max`, `k,min`, `dw,min` and, on ISO 4014, `b`, `lg,max` and `ls,min`, each labelled with
its sense and its source, such as `Across flats, min (ISO 4017:2022 Table 1)`, the table read from
the stored `Source`. A part that matches no row has none of them and gets one warning, `no ISO
4014:2022 or ISO 4017:2022 row matches these fields; row values not reported`. A non-coarse pitch
still builds (03 D-04), reads `custom` and gets no row numbers, which closes the coarse-pitch
question STATE.md carried. The designation is the standards' own: `Hexagon head screw ISO 4017 - M6
x 20`, `Hexagon head bolt ISO 4014 - M10 x 80`, no property class, ASCII `-` and `x` where Clause 7
prints an en dash and a multiplication sign, a decimal comma in the size (`M3,5`), and `null` for a
left-hand part, because Clause 7 of both standards gives no left-hand form (the owner's read,
`04-OWNER-READS.md`). `InfoRow.value` stays a float and the page shows `String(row.value)`: nothing
rounds anywhere, and the ui-rounds debt item is resolved. `notes` are present only on an exact match
and are not warnings: the product grade (`product grade A (ISO 4017:2022: l <= 150 mm and l <= 10
d)`, with the matched standard substituted, and the ISO 4014 clause itself was not read for this
wording, 04-11) and, for M10, M12 and M14 only, `wrench size 16 mm (ISO 4017:2022); the withdrawn
DIN 933 used 17 mm`. The ISO figure is the row's own `s`; the DIN figures (17, 19 and 22 mm) are a
constant read from two web pages that agree (Eurolink FSS and Wermac, `04-RESEARCH.md` Sources),
MEDIUM confidence and not from a purchased text; it is the only DIN text in v1.
`PartInfo` also carries `downloads` (the owner's IN-02 ruling a, UAT 2026-10-12, gap G-04-3), one
entry per format and quality the model route serves, per format the route's default quality first,
each with `refusal`, the sentence of `download_refusal` or null; the route, `screw export` and the
document read that one rule, and the page links per format the first entry not refused, so a long
ISO 4017 screw whose fine STL the INTERIM cap refuses is offered as `Download STL (preview)`, and the
fine-STL warning stays.

**Caps (D-21, D-22).** This paragraph supersedes L12's cap list. The measured quantity is the fine
raw STL plus its gzip level-1 copy over the INTERIM 64 MiB export budget, at the INTERIM fine preset
(0.01 mm, 0.1 rad), run `2026-10-08-a-grid`; the raw fine STL alone was under the budget at every
first over-budget row (at M8 right-hand L=68 it is 45,659,684 bytes), which is why L12's parenthesis
is corrected. The convention is unchanged: each cap is the longest measured length that fits, below
the first rod row over the budget. `FINE_STL_ROWS` is keyed by `(d, pitch, left_hand)` by hand, the
owner's WR-02 ruling of 2026-10-11, because the left-hand rods measured smaller files and the
right-hand caps applied to a left-hand part refused lengths L11 had measured inside. The right-hand
caps are unchanged: M8 67.5, M10 56, M12 60, M14 58, M16 52, M18 65, M20 64 mm. The left-hand caps
are M10 72, M12 77, M14 78, M16 75, M18 91, M20 91 mm, and there is no cap for M8 left-hand, because
no row measured over budget up to 80 mm (65,776,259 bytes at L=80, under 67,108,864). The debt
item's 73, 78, 79, 76, 92, 92 were the first over-budget lengths, not caps (D-21 clarification). The
values are proven against the run records, 3580 built rod rows of
`bench/results/thread-spike/2026-10-08-a-grid.jsonl`, by
`tests/test_thread_maths.py::test_every_cap_is_the_longest_measured_length_that_fits_in_the_grid_records`,
which also reproduces the seven right-hand caps; no cap is typed to match. **Both caps are on the
built thread** (D-22): the 250-turn cap compares `t / pitch` as exact decimals and its 422 names
`thread_length`, `length` and `pitch`, and the fine-STL rows compare `t`, with the refusal naming
`thread_length` and the hand. The head and the shank add bytes no run measured beyond the probe
above (1.1 to 26.3 KB, small next to the thread's), so the caps stand on the thread alone and the
interim-bounds debt item records it; Phase 7 re-sweeps on the finished bolt (OPER-02, OPER-03). The
catalogue makes 62 ISO 4017 presets, and no ISO 4014 preset, fine-STL refusals, each a long screw
whose built thread is past its right-hand cap (first `iso4017:M8x70`, last `iso4017:M20x200`); the
count is pinned as a literal in `tests/test_presets.py::test_the_fine_stl_refused_presets_are_counted`
so that Phase 7's re-sweep shows the change. The preview STL and the STEP of those presets work. The
preview STL a pick loads is as large as 22,320,784 bytes for M20 x 200 (446,414 triangles; fine
144,945,384 bytes), the probe's largest case.

**Head rule (D-23, D-26).** `s <= d` is a 422 `head_too_small` naming `s` and `d`, with the message
`s` must exceed `d`. This is product policy and not a kernel necessity: a research probe on
2026-10-11 (scratch, not recorded in `bench/RESULTS.md`; RESEARCH Alert 4) fused `s < d` and
`s == d` into one valid solid inside the gate with a volume error under 1.4e-7, and the head stacks
on the shank without overlap, so D-23's first stated reason ("would fail the gate with an
unhelpful kernel message") did not hold; the reason is that a head no wider than its shank is not a
hex head. Its cost is visible: with the frozen `s = 10.0`, a hand edit of `d` to 10 or more is a
422 until `s` is also set, and a preset sets `s`. No bound ties `k` or `s` to a table (contract 6; a
tall head is a valid custom part). `d` can never reach `INTERIM_MAX_MM` because `s` must exceed
it and is bounded by the same value.

**Open, filed.** `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` gains the rows this
phase adds: `MIN_TAIL_MM`'s new home, the hand-keyed `FINE_STL_ROWS` and the unmeasured head and
shank bytes, the refused-preset count, the bound on `s`, `k` and `thread_length`, and the M20 x 200
preview STL a pick loads (Phase 7, OPER-02).

Reason: the part a user asks for must be the part they get, and a number the tool prints must be one
they can cut metal to (L02). Making the millimetre fields the only truth, and presets only a way to
fill them from rows that cite their table and column and were read twice, keeps every shareable link
meaning one part with no table consulted, and keeps a row from reaching a user unverified. Deciding
the `thread_length` conflict at the request boundary is the only place the provenance of a value
exists. Gating the bare thread first keeps L11's tolerance meaningful once a head and a shank dilute
the whole-part volume. Keying the caps by hand and saying what was measured keeps every cap a value
a run produced.

Reversibility: one-way for the `s`, `k` and `thread_length` names and frozen defaults (every
shareable link that omits them depends on them forever), for the preset id grammar and for the
published shape of the info document. Costly for the info document's groups, notes and labels (a
published shape every consumer reads), the `/api/presets` route, the `thread_length` rule and its
request-boundary mechanism, and the geometry (a later head chamfer changes the part every existing
link means with no field change, acceptable while the standing warning says "not a product build",
a superseding entry after release). Reversible for the caps and `MIN_TAIL_MM`: constants that Phase 7
replaces with measured values (OPER-01, OPER-02, OPER-03).

## L14 — Phase 5 reads its table values from free GOST texts that adopt the ISO standards; buying the ISO texts is deferred debt (narrows TABL-04 and 05 D-14 to D-16)

Date: 2026-10-20. Decided by the owner after the web research of 2026-10-19. The owner's reply, verbatim:
"put this table description and sources into a document and choose second option. I don't want to
spend $400 for MVP so lets put ISO into a techdebt". Option 2 is GOST only: one source family, every
text free to read, every edition 2012 or older, so each one lags the ISO edition the plans name. The full
map, the URLs and the rejected alternatives are in `docs/requirements/standards-sources.md`. This
entry copies no standard value.

**The map.** GOST ISO 4032-2014 (IDT ISO 4032:2012) for the nut. GOST 24705-2004 (MOD ISO 724:1993)
for basic d2, D1, D2. GOST 16093-2004 (based on ISO 965-1:1998 and ISO 965-3:1998) for the 6g and 6H
deviations and tolerances. GOST 12414-94 (the ISO 4753-83 text plus two non-ISO ends, out of scope) for
the tip end. GOST ISO 4014-2014 (ISO 4014:2011) for a new ISO 4014 value, under the conditional rule in
the open question below. DIN 934 and GOST 5915-70 are never a source.

**What it narrows.** TABL-04 ("a table row ships only against a purchased copy of its standard"): for
the documents in the map, the free GOST text stands in for the purchased ISO copy. 05 D-14's
precondition (purchased copies of all four) reads: the owner has the free GOST text of each. D-15's
frozen-default source and D-16's ISO 965-2 rows read through this entry. The ROADMAP Phase 5
precondition and the REQUIREMENTS.md TABL-04 text are amended with the plan amendments (below), not in
this entry's commit. Phase 4's ISO 262:2023, ISO 4017:2022 and ISO 4014:2022 rows stay exactly as L13
records them.

**Double entry still applies (ruling B).** The owner copy is generated from the free GOST text (its text
layer or page text). The agent's independent read is from rendered images of the same pages. The
cell-by-cell diff runs in `make verify`, with one relation test per row, and UNVERIFIED rows are
refused, all as L13. L13's caveat carries over: both copies read the same reproduction, so the diff
cannot catch an error in it. The reproductions are not publisher copies, and their faithfulness is
UNVERIFIED.

**The 6g and 6H limits are derived.** Each limit is the GOST 24705-2004 basic dimension plus the
GOST 16093-2004 printed deviation or tolerance. Only printed values are added. A value given only as a
formula is a stop-and-ask at plan 05-08 (the ISO 965-1 formulas stay rejected, 05-CONTEXT). The Source
and the panel label say "derived" and name both designations, never "ISO 965-2:2024 Table". D-16's
relation tests still apply. R13 stands, with the "ISO 724 table" read as GOST 24705-2004.

**Citations.** Every row's Source and every panel label names the GOST designation and the ISO edition
that designation adopts. The exact strings are set by the plan amendments. The shipped
`NUT_NO_ROW_WARNING` in `src/screw/calc/__init__.py` names ISO 4032:2023; it is reworded when the nut
rows land (plan 05-07). This entry does not change code.

**Edition gaps and the M6 cross-check.** Whether any value Phase 5 uses differs between the five
edition pairs (ISO 4032 2012 and 2023, ISO 724 1993 and 2023, ISO 965 1998 and 2024, ISO 4753 1983 and
2011, ISO 4014 2011 and 2022) is UNVERIFIED, and nothing here claims it does not. The frozen nut
defaults s 10.0 and m 5.2 (`05-OWNER-READS.md`, from a GlobalFastener print of ISO 4032:2023,
permanent: accepted 2026-10-14, shipped by plan 05-04) are compared with the GOST ISO 4032-2014 M6
grade-A coarse row in the columns they took (s max, m max) before plan 05-06 lands. A match is
recorded in `05-OWNER-READS.md`. A mismatch is a stop-and-ask, because D-15 is one-way.

**Pending plans.** Plans 05-06 to 05-18 name ISO editions (counted 2026-10-20). They read each named
ISO document as its GOST equivalent from this entry. Their preconditions are amended when the phase
resumes, before 05-06 executes: 05-06's ISO 4032:2023 page render and its "never transcribe from any
other source" clause, 05-08's ISO 965-2 and ISO 724 owner copy, 05-11 and 05-12's ISO 4753 read and
ISO 4014 fillet copy. The pending reads 3 to 7 of `05-OWNER-READS.md` are read from the GOST texts.

**Open question.** The owner's purchase list names ISO 4014:2022. L13 records Phase 4's ISO 4014:2022
rows as read from the purchased copy, with the agent's second copy taken from preview pages under
ruling A-3 (`04-OWNER-READS.md`). Nothing records why ISO 4014:2022 is on the list. The rule for a new
ISO 4014 value (R1's fillet r,min, plan 05-12) is: read it from the owner's ISO 4014:2022 copy if that
copy holds it, else from GOST ISO 4014-2014. Which applies is asked at 05-12's precondition. Phase 4's
shipped rows are untouched.

Reason: the owner's call, not to spend about $400 (the owner's figure) on the MVP. GOST was chosen over
mixing national sources because it is one family, freely readable. The cost is edition age, which is why
every citation names the edition actually read and the purchase has a named trigger.

Reversibility: reversible for the source choice: buying the ISO texts re-reads and re-cites the rows,
and the double-entry diff shows every change. One-way for any frozen default a GOST row confirms
(D-15), hence the stop-and-ask on a mismatch. Costly for the published citation text on the panel.
Revisit: `docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md`.

**Amendment (2026-10-20, owner ruling at plan 05-12's precondition).** The open question is answered:
R1's fillet `r,min` is read from ГОСТ Р ИСО 4014-2013 (the Russian national adoption of ISO 4014:2011),
not from the owner's ISO 4014:2022 copy and not from GOST ISO 4014-2014. The copy the owner supplied is
the national text, not the interstate one this entry names; the owner accepted it (option a). Its Table 1
prints `r` min per size. It is a download-site copy, so its faithfulness is UNVERIFIED like the rest.
Every citation names it as read: `ГОСТ Р ИСО 4014-2013` in the record, in ASCII as the plans' `Source`
strings decide. Path and sha256: `05-OWNER-READS.md`, "Rendering route and the PDFs".

## L15 — Phase 5 ships the ISO 4032 nut with a required radial clearance, the kernel pair proof that cannot say proven when its control is empty, the modelled thread ends and a measured fine mesh

Date: 2026-10-20. Decided by the owner in the Phase 5 discussion (D-01 to D-26, 2026-10-14,
`05-CONTEXT.md`), by the opening read of 2026-10-14, the rulings R1 to R13 of the same day, the
2026-10-20 rulings and R14 and R15 (all in `05-OWNER-READS.md`, cited below by R-number). CONTEXT calls
this entry "L14" (D-08, D-12, D-21 to D-23); that number went to the owner's GOST source decision
on 2026-10-20, so this one is L15, and the standing warning on every info document already cites L15.
Every value names its run in `bench/RESULTS.md`, its `05-OWNER-READS.md` line, its probe, or the plan
summary that measured it. This entry copies no standard value beyond the two frozen defaults and the
tolerance arithmetic the rulings fixed. L14 is not edited here.

**The nut kind, fields and frozen defaults (D-15; 05-04, 05-06).** `nut` is the second registered kind.
`NutParams` adds `s` (title `Across flats`, group `Nut`), `m` (`Height`) and `clearance` (`Clearance
(radial)`, group `Pair`) to `d`, `pitch` and `left_hand`; flags `--s`, `--m`, `--clearance`. The frozen
defaults are `s = 10.0` and `m = 5.2`, the `s` (nominal = max) and `m` max columns of the M6 row. They were
first read on 2026-10-14 from a one-page print of a web page that transcribes ISO 4032:2023 (read by
Claude, not the standard; the owner approved that source and typed `permanent: accepted` the same day,
`05-OWNER-READS.md`, "ISO 4032:2023 M6 defaults" and the permanence line), and on 2026-10-20 they were
checked against GOST ISO 4032-2014 Table 1, M6 (`s` 10,00, `m` max 5,20): they match, so D-15's stop-and-ask
did not fire (`05-OWNER-READS.md`, "2026-10-20: GOST ISO 4032-2014 in hand, the M6 cross-check"). Pinned
by two tests in `tests/test_params.py`, one on the literals and one on the row (05-06). One-way, like L13's
bolt defaults: every link that omits `s` or `m` means these values forever.

**The required clearance and its bound (D-01, D-04; 05-04, 05-05).** `clearance` has no default, so an
omitted one is `422 missing` on the API and exit 2 on the CLI naming the field; it takes any finite
value up to `INTERIM_MAX_MM` with no lower bound. A default is Phase 6's, from the printed test
(PAIR-02). The model refuses, naming fields: `pitch_too_coarse` when the nut's void root `d/2 - 5H/8 + c`
is not above 0 (fields `d`, `pitch`, `clearance`; M2 x 2 is a valid nut at c = 0.5 and refused as a bolt);
`nut_too_thin` when `s <= d + 2c` (fields `s`, `d`, `clearance`; D-13), so the default nut refuses a
clearance of 2 mm or more; `turn_cap` when `m + 2 pitch` is past the 250-turn cap (fields `m`, `pitch`;
judged on the void the builder makes). A clearance of 0 or below builds and warns `clearance <c> is not
positive: the pair cannot be proven (PAIR-03)`, so the spike's c = 0 and c = -0.05 diagnostic rows
reproduce through the product. **No fine-STL cap for the nut (R12; 05-05).** R12 reuses `FINE_STL_ROWS` on
`m` only if the probe's nut bytes fit the 64 MiB budget at each cap and cap + 1 mm does not. The probe
(`bench/RESULTS.md`, "End-cut probe (Phase 5, D-10)", R12's table) shows it on none of the three sizes it
measured: M10 right (0.973 at cap + 1) and M20 right (0.936) still fit, and M20 left (1.003) is over at the
cap itself. So no nut cap exists and `download_refusal` serves every nut download; the owner's sign-off
on that interim is outstanding. Debt: `docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md`. Superseded by L16 (plan 05-19).

**The nut solid (D-10, D-12, D-13; 05-04, 05-13).** The hex prism (`polygon(6, s, circumscribed=True)`,
height `m`) less `helical.thread(d, pitch, m + 2 pitch, clearance=c)` shifted down one pitch. The void is
gated against its closed form first, then each of the four end cuts is judged by the volume it removed
(`T_PIECE`, below) and the finished nut against `nut_end_closed_volume` at `T_GATE`. Measured: every ISO
4032 row at c = 0, 0.1 and 0.2 builds as one valid solid, whole-gate error at most 3.3e-06 against
`T_GATE` 9e-05; the build rose from about 0.15 s to 1.0 to 1.5 s; all 28 catalogue ids (14 rows x 2 hands)
mesh watertight at the preview, and a countersink that ends on the root radius meshes open (8 open edges,
M6 right, c = 0.1) though every volume gate passes, which is why the cone is built to cross the root (05-13).

**The counterpart (D-02, D-03; 05-10).** `PartInfo.counterpart` is `{kind, fields}` or null, computed
kernel-free. A bolt on an exact GOST ISO 4032-2014 row carries `d`, `pitch`, `left_hand`, `s`, `m`; a nut
on an exact ISO 4017 row carries `d`, `pitch`, `left_hand`, `s`, `k`; `clearance`, `length` and
`thread_length` never travel. Off a row the document's last warning names what to set on the target
(`no GOST ISO 4032-2014 (ISO 4032:2012) row for d <d> pitch <P>; set s and m on the nut`, and the bolt-side
analogue); an ISO 4017 M7 bolt is off the nut rows. The page links it generically and holds no kind name.

**The pair proof (D-05 to D-07, D-24; 05-14, 05-15).** The verdict rule is the spike's `cell_verdict`
moved byte for byte into kernel-free `screw.calc.pair` (11 moved blocks, each an exact substring of the
originals at `269feb6`; the spike imports every name back and tests assert identity). The bodies are the
spike's (`rod_piece`, `blank`, `place`, `check_cover`, `common`) in `screw.solid.pair`. `prove(NutParams)
-> PairReport` reads the three screw-motion matched poses and their half-pitch controls; at c <= 0 it
reads nothing and returns `inconclusive` by definition (R8); a mixed-hand pair is read at the matched
poses only and is `violated` through the rule (R7: the internal keyword `rod_left_hand`, never on the CLI
or the model). `screw pair nut <flags>` prints the report as JSON and exits 0 `proven`, 1 `violated`, 2
`inconclusive`; flags are generated from the model, `--preset` is absent, and a nominal rod with no root
is refused before the kernel loads. It ends in `os._exit` after flushing (the real boolean parks its
operation and a normal exit dies with 139, RESEARCH F5). The contract "The serving process and its workers
never import the pair proof" (`screw.app`, `screw.pool` -> `screw.solid.pair`, no indirect imports) landed
with the module, shown to break when an import is planted, with a fresh-interpreter test as its runtime
half. The verify cell is M6, right hand, c = 0.10, in a child process: `proven`, as pre-registered. **The
ubuntu reading (05-15):** CI run 39431329111 on draft PR #18 (head `c374150`, `cadquery 2.8.0`,
`cadquery-ocp 7.9.3.1.1`) read `proven` in **167.50 s** on ubuntu-latest under four xdist workers, against
42.55 s alone locally; run 39428789949 read `proven` too (its log carried no durations). The required
`test (3.12)` job rose from 3 to 7.5 min to 12m26s and 16m28s; debt:
`docs/tech_debt/active/2026-10-20-ci-test-job-tripled-by-two-pair-tests.md`. The shipped bolt and nut are
intersected at the matched poses as an evidence row printed beside the verdict, never a verdict input
(D-05). **Shipped-nut start (R15, 05-14):** the evidence nut starts at the least whole-pitch `z` that clears
the tip cone by a pitch, 2P for every size, because both threads have phase `2 pi z / P` and a start at
`tip cone length + P` is half a thread out of phase (8.747 mm3 at all three poses on M6 at c = 0.10, a
false interference). Only the evidence row's numbers depend on it, not any verdict.

**Review fixes (plan 05-20, 05-REVIEW.md).** *WR-01*: the nut's face-chamfer cutter overshoots the face by
`min(0.5, (s / 2) tan 30 deg / 2)` mm, so its first profile radius stays at `s / 4` or more and a nut
narrower than `sqrt(3)` mm across flats builds; from `2 sqrt(3)` mm up (every GOST ISO 4032-2014 row) it
is the old 0.5 mm, and the default and M2 nuts' preview STLs are byte-identical across the change. The
model gained no floor on `s`. *WR-02*: the pair rule's two tolerance comparisons are negated `<=`, as the
written rule's "within `T_PASS`" and "within `PAIR_BAND`" require, so a NaN nut body or control is
`inconclusive`; `prove` refuses a non-finite kernel volume where it reads one (the blank, each boolean,
each evidence pose) as a failure, the boundary the spike's record parser `_num` holds. The rule's
clauses, their order and every recorded verdict are unchanged, and a planted matched NaN stays
`violated` as 02-SPIKE Rules is written (a NaN is not empty). *WR-03*: `cell_judgement` returns the rule's
verdict and reasons with the closed form it judged the controls against (`cell_verdict` returns the first
two); `PairReport.closed_control` is that form, present where the rule reached the controls and null
where it ended first. *WR-04*: at a clearance of d / 2 or more the radius-d proof body cannot hold the
void, `prove` reads nothing and is `inconclusive` by definition (the R8 shape), and its reason prints no
closed form (the nut-body form reads -39.6362 mm3 at d 6, pitch 1, c 3.5). The blank does not grow (D-05):
for any nut the CLI accepts, c >= d / 2 exceeds the thread depth 5H / 8, so the control's closed form is 0
and the rule would read `inconclusive` whatever the blank. *WR-05*: `engagement_turns` is
`turns_of(m, pitch)`, as the info document's. *WR-06*: off an ISO 4017 row the evidence bolt takes the
nut's own `s` (above d + 2c, so above d) and the bolt's frozen `k`; the head starts `tip - P / 3` above
the nut's top at the highest matched pose, so neither enters a reading, and on a row nothing changes.
"The unmodified `cell_verdict`" in the next paragraph describes 05-01's derivation; the 05-20
re-derivation of the 240-cell table by the amended rule is byte-identical.

**The expected table and the tiers (D-07; 05-01, 05-15, 05-16).** `tests/data/pair_expected.tsv` holds
the expected verdict of all 240 recorded K = 3 cells (88 `proven`, 92 `inconclusive`, 60 `violated`),
derived by `bench/pair_expected.py` from `2026-10-08-a-pair` with the unmodified `cell_verdict`, the
record pinned by sha256 (`1644650ed5b418fc2b43bfa8fd875d371f0fc4940018f67b5b3241df6c84d9f3`) and
re-derived by a test in `make verify`; it reached `main` in PR #17 (squash `5d90f3e`) before any Phase 5
kernel run. The `pair` marker holds the 240 cells (`make pair [SIZE=]`; `.github/workflows/pair.yml`,
`workflow_dispatch` plus Mondays 04:23 UTC, `contents: read`, no secrets, outside `ci.yml` and
`required-jobs.txt`). The one full run (`bench/RESULTS.md`, "Pair tier (Phase 5, D-07)", HEAD `22bcd50`,
macOS arm64, 8 workers, shared host): **240 of 240 equal their pre-registered verdict**, 88/60/92, 1054.04
s, slowest cell 150.2 s, no timeout. Product cells: the table's `m` equals the GOST ISO 4032-2014 row's
`m_max` and the pitch equals the row's at all 14 sizes that have a row, so **no cell differs and there are
no product cells** (M7 has no row; "Product pair cells (Phase 5, D-07)"). The ubuntu grid has not run
(`pair.yml` can be dispatched only once it is on `main`); debt:
`docs/tech_debt/active/2026-10-14-first-pair-yml-dispatch.md`.

**M18 (D-08; 05-01, 05-16).** `05-M18-DIAGNOSIS.md` (blob `9544d6f`, on `main` before the run) fixed 36
readings and five predictions; "M18 control diagnosis (Phase 5, D-08)" in `bench/RESULTS.md` is the one
run (59.6 s, 36 of 36 built, probe not void, jsonl sha256 `b301560c...ad8fbc`). The finding as recorded:
**the empty is reproducible** on this host and kernel (10 of 10 fresh processes, both hands as mirror
images, c = 0.10 and c = -0.05 alike, unaffected by a fuzzy value of 1e-4 mm or by swapping the operands),
and **it is not pose-local**: it is a band of at least 0.11 rad on each hand (14 of the 16 neighbouring
readings empty), with one edge between 0.01 and 0.1 rad on the side away from theta 0 and the other edge not
bracketed. H2 (pose-local) did not hold; H1, H3, H4 and the four harness controls held. **No rule, pose,
constant, body or label changed.** M18 stays `inconclusive` on both hands, the nut's note reads `kernel pair
proof inconclusive at K = 3 (2026-10-08-a-pair)` keyed on `(d, pitch) == (18.0, 2.5)` from the record and
never a kernel call (D-20), and `screw pair` reads `inconclusive` for it, and the grid reproduced that at
all 8 same-hand M18 cells. One run on macOS arm64 at a busy load; why the boolean returns nothing is not
established.

**The end models and their oracles (THRD-05, D-09 to D-13; 05-02, 05-11, 05-12, 05-13).** Each end is a
**cited** value, a **stated model**, or both, and a label says which. All are kernel-free in
`calc/thread.py` and pinned to identities that do not use them. *Tip* (R2, **stated model**): a cone at
45 degrees from the end face, starting at the minor diameter, read from `GOST 12414-94 (ISO 4753:1983)`,
whose figures mark `~45 degrees` and whose chamfered end prints no angle value or length; its note 3 prints
48 degrees, recorded as an unresolved misprint of the reproduction and not used (owner ruling
2026-10-20, option a). *Nut countersink* (R3 b, **stated model**): a 90 degree included angle (half-angle
45), the lower end of the band `GOST ISO 4032-2014 (ISO 4032:2012)` footnote c prints (90 to 120 degrees),
opening to a face radius of `1.16 d / 2`, the largest `da_max / d` of the 14 rows (M2,5; the smallest is
1.08 at M10 and M20), owner option A; where `1.16 d / 2 <= d/2 + c` or the radius passes the flats the cone
cannot cross and is left out with a warning naming `clearance` or `s`. Erratum (plan 05-20, review IN-01): the smallest `da_max / d` of the 14 rows is 1.079, at M14 (15.1 / 14), not 1.08 at M10 and M20; the factor is the largest ratio and does not depend on it. *Nut face chamfer* (R4 a, **stated
model**): 30 degrees from the inscribed circle `s / 2`, the upper end of the band footnote b prints (15 to 30
degrees). *Capping* (R5 a): the two cutters on a face are capped at `m / 2` with a warning naming `m`; no
catalogue row caps (smallest margin M2, 0.38 mm against 0.8). *Under-head fillet* (R1 a, **cited**): the
radius `r,min` per size from `GOST R ISO 4014-2013 (ISO 4014:2011)` Table 1 and Table 2 (the source the
owner ruled for on 2026-10-20, option a, in place of the GOST ISO 4014-2014 that L14 names; this answers
L14's open question), double-entered; neither table prints M7, so an M7 bolt gets no fillet. It is a
revolved ring fused under the head, never an OCCT fillet, and only where a plain shank at least `r` long
exists; an ISO 4017 screw gets none and carries the note `no under-head fillet: the thread runs to the head
(ISO 4017:2022)`. A thread no longer than the tip cone gets no cone and the warning that says so; the
kernel's intersect fails in a sliver of about 1e-9 mm above that length (debt:
`docs/tech_debt/active/2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md`). *The piece
tolerance* (R11): `T_PIECE = 0.03`, ten times the largest honest piece error the probe recorded (2.737e-03,
tip 45 degrees, M2 right) rounded up to one significant figure; each cut is judged by its own volume
at `T_PIECE` and the whole part at `T_GATE`, because the whole-part gate alone does not see every wrong
cut on a bolt: on M10 x 200 it misses the dropped ring (6.6e-05) and the 30 degree cone (8.1e-05) against
9e-05 (05-12), while on a nut it sees all four controls (05-13). The probe's own count is 54 honest rows
(`bench/RESULTS.md`); R11's text in `05-OWNER-READS.md` says 46, and the recorded maximum is the same.
The standing warning is now `ends modelled per L15: bolt tip chamfer, under-head fillet on an ISO 4014
plain shank, nut lead-in countersinks and face chamfers; nominal, not toleranced; not a product build`
(D-18); "not a product build" stays until Phase 6.

**The table rows read under L14 (D-14, D-16, D-17; 05-06 to 05-09, 05-12).** `NUTS`: 14 rows of `GOST ISO
4032-2014 (ISO 4032:2012)`, Table 1 (M2, M2,5, M3, M4, M5, M6, M8, M10, M12, M16, M20) and Table 2 (M3,5,
M14, M18), no M7, with the owner's 2026-10-20 ruling that there are no informative rows (the 2012 text has
no Annex A, so TYPE-03's label has nothing to label; each row's `Source` records its table) and the owner-copy
route of the same day (text layer by script, label fixes to keys only, the agent's page-image
transcription first, a cell-by-cell diff in `make verify`, one relation test per row). Product grade A to
M16 and B above, from the scope clause confirmed on the rendered page. `BASIC`: 15 coarse basic diameters
`d2 = D2`, `d1 = D1` from `GOST 24705-2004 (ISO 724:1993, MOD)` Table 1 (M7 included; the owner copy was
regenerated with M7 after the 05-08 diff found it missing, and for that one row it was generated after the
other copy was known: the caveat is in `05-OWNER-READS.md`). `TOLERANCES`: 72 printed deviations and
tolerances from `GOST 16093-2004` Tables 3 to 7 (es of g and EI of H, Td, TD1, Td2, TD2 at the 12 coarse
pitches). The 6g and 6H limits are **derived**, each the basic value plus a printed value by exact decimal
addition, 15 rows each, and the label and the source say derived and name both documents, never "ISO 965-2:2024
Table" (L14). R13 held: the panel's `d2`, `D1`, `D2` are the ISO 68-1:2023 basic profile (`d - 3H/4`,
`d - 5H/4`) and the table is only a test that they agree. All of it was transcribed from the owner-supplied
download-site reproductions, which are UNVERIFIED (L14 and the L13 caveat: both copies read the same
reproduction, so the diff cannot see an error in it). The designation is `Hexagon regular nut GOST ISO 4032 -
M6` (owner ruling 2026-10-20, option a), withheld for a left-hand nut because the clause gives no form.

**The panel (INFO-01, INFO-02, D-16, D-18 to D-20; 05-07, 05-09).** The nut document groups are `Thread`
(`d`, `pitch`, thread depth, `D2`, `D1`), the limits group when the size is an exact ISO 262 size, `Nut`,
`Pair` and `Part`. The limits heading is the single ASCII string `limits for a bought part; this model is
nominal and not toleranced` on an exact ISO 262 size only, never empty. The eight `Pair` rows in fixed order
are `clearance`, `clearance_diametral`, `flank_gap`, `axial_play`, the nut's major, pitch and minor diameters
and `engagement_turns`; the flank-normal gap is `c sin 30 degrees` and the axial play `2 c tan 30 degrees`,
each pinned against the numeric derivative of `section_radius`, not typed from the research (D-19). The
kernel verdict never appears on the API or the page.

**The deflection rule and the file name (D-21, D-22, FRNT-06; 05-17, 05-18).** The rule, committed with its
instrument (`c87aadf`) before any row ran: the fine preset is the largest linear deflection on the ladder
0.01, 0.0075, 0.005, 0.0025 mm (angular 0.1 rad, absolute) whose worst radial deviation over M2, M3, M6,
M10, M20, both hands, is at most 0.5 x the 0.05 mm proof clearance (R6 a, the owner's fraction), a bound of
0.025 mm. "Mesh deviation (Phase 5, D-21)" in `bench/RESULTS.md` (one run, 40.7 s): the worst row at 0.01
mm is **0.0161 mm** (M20, both hands), 64 % of the bound, so the rule selects `0.01 mm / 0.1 rad`, which
`TESSELLATION["fine"]` already was; no cap, refused-preset count or M20 x 200 figure moved. The preview
(0.08 mm, 0.5 rad) reads 0.0587 to 0.1299 mm on the same rods, every row over the bound, which is why a
preview STL is named. The instrument's first run aborted on its own vertex check (1.9e-04 mm at M20, the
shipped solid's departure from the model, not the mesh); the check's threshold was widened to 1e-3 mm
before the recorded run and the abort is in the entry. The deviation is stated on facet centroids of
8-pitch rods, not on the finished bolt or nut. The kernel's `ControlSurfaceDeflection` is pinned on and the
fine preset pinned to `(0.01, 0.1)` by `tests/test_mesh.py`, so a later change cannot ship without a recorded
caps run. **File name (D-22, R9):** `calc.download_name(p, fmt, quality)` is the one rule for the
`Content-Disposition` header of `app._serve` and for `screw export -o <directory>`: `<slug>_preview.stl`
for the preview STL, `<slug>.stl` for the fine STL and `<slug>.step` for the STEP (a STEP has no
tessellation, so quality does not rename it). A file path given to `-o` is written as given; the `wrote`
line names the quality of an STL. A parity test pins the API's header name equal to the name the CLI writes
for each kind, format and quality. The idea file moves to Done. A published header, costly to reverse.

**Owner rulings carried (R1 to R15).** R1 to R5, R11 and R13 above; R6 above; R7 and R8 with the pair proof;
R9 with the file name; R10: switching kind with an empty clearance drops the old mesh and shows nothing
until a valid nut, placed in `navigate()` so the Matching link reaches it too (05-10); R12 above; R14: the
local `make verify` measured 101.65 s after 05-12 (3144 passed), over the 90 s threshold, **accepted** with
the whole 60-id watertight bolt sweep kept in verify (ruled 2026-10-20; later runs on a loaded host read
128 to 200 s, 05-13 to 05-17, and were not separately ruled; CI time is the debt item above); R15 above.

**Open, filed.** `docs/tech_debt/active/2026-10-14-nut-interim-bounds.md` (the nut's interim ceilings);
`2026-10-14-nut-fine-stl-caps-unmeasured.md`; `2026-10-14-first-pair-yml-dispatch.md`;
`2026-10-20-ci-test-job-tripled-by-two-pair-tests.md`;
`2026-10-20-tip-cone-degenerate-boolean-at-the-cone-length.md`;
`2026-10-20-iso-standards-not-purchased.md`; `2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md`.

Reason: a pair proof is only worth printing if it can fail and say why, so the verdict is the spike's rule
unchanged on the spike's bodies, its expectations were written down before any run and on `main` first,
and the one cell the spike could not read (M18) is labelled from the record and diagnosed without moving
a rule. Ends that no standard prints as a number are stated models labelled as such, with the
band they come from, rather than a plausible figure (L02). Choosing the mesh by a rule committed before
its instrument ran, against the smallest clearance the printed test will use, keeps a download from
consuming the gap the proof is about.

Reversibility: one-way for the nut's field names, `s` and `m` defaults and the required `clearance` (every
nut link depends on them; a Phase 6 default adds one without changing a link). Costly for the pair proof's
bodies, the expected table and the tiers that stand on them, for the info document's `counterpart` and
`Pair` shapes, for the published CLI and report shape, for the end models (a later change alters every
part a link means with no field change, acceptable under the standing warning) and for the `_preview`
file name. Reversible for the fine preset and the sources: a constant with a cited run, and rows re-read
from the ISO texts when bought (`docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md`).

**Amendment (2026-10-21, owner ruling at 05-UAT.md test 3, gap G-05-3).** The bolt's `Matching nut` link opened
a nut with its clearance empty, so the nut did not render (the counterpart paragraph above, D-01, D-02). The
owner asked for the link to carry one ("Yes, I do want.") and ruled, option "last typed clearance": "The page
remembers the clearance last typed on a nut in this tab and carries it on the bolt's Matching nut link; with
none typed the link stays empty. No invented number." What changes is the page only. `app.js` keeps, per
kind, the value last typed (an `input` event) into each field that has no default; today that is only the
nut's `clearance`, because the page names no field or kind (D-10). `showCounterpart` adds it to the link
before the server's fields, so the server's fields win. A value a link, Reset or a kind change wrote is not
typed, typing the field empty forgets it, and a reload or a new tab forgets it, because nothing is persisted.
What does not change: `PartInfo.counterpart` still never carries `clearance` (D-02's shape; the API,
`screw info` and the parity test are unchanged); the value never enters the bolt's hash, a bolt request or a
download link; with nothing typed, the link and the nut are as before, the field empty and nothing built
(D-01, R10); no default is introduced (L02, PAIR-02), the value is the user's own. It amends the counterpart
paragraph's consequence that a bolt's link opens a nut with the clearance empty, for the case where one was
typed in this page. Plan 05-22 names the two new tests and the probe record in 05-22-SUMMARY.md.
Reversibility: reversible. It is page state; no published shape changed.

**Amendment (2026-10-21, plan 05-23, review findings WR-07 and WR-08, owner ruling "forget on Reset and on a link").**
Two corrections to the page memory of the typed clearance. WR-07: the amendment above says the value never
enters the bolt's hash, and that was false on one path. The memory was keyed by `currentKind`, which a kind
switch sets only after its catalogue fetch while the new form is already on screen, so a clearance typed in
that window was stored under the bolt, and the nut's `Matching bolt` link carried it and was refused
(`Unknown field "clearance" for kind "bolt"`) for the rest of the page session. It is now keyed by
`formKind`, set in `buildForm` with the controls and `defaults` and cleared with them. In the same window the
form's own update ran for the old kind: it wrote the hash `#clearance=0.1`, a bolt link, and requested
`bolt/info?clearance=0.1`. By the owner's choice (a) of 2026-10-21, `update()` now returns while `formKind`
differs from `currentKind`, so in that window only the schema request is sent and the hash stays
`#kind=nut`. With the guard alone, Back before the switch had loaded left the nut's form on screen under
the bolt the link names, because `navigate` rebuilt only on a changed kind: at HEAD that built the default
bolt under the nut's controls, and with the guard alone it built nothing and said nothing. By the owner's
choice "fix in navigate" of 2026-10-21, `navigate` also rebuilds when the form on screen is not the link's
kind (`kind !== currentKind || kind !== formKind`), so Back reopens the bolt, which builds. So on every path
neither the remembered value nor the form's value reaches the bolt's hash, a bolt request or a download
link. WR-08, the owner's ruling of 2026-10-21, "forget on Reset and on a link": Reset forgets the remembered
value of a field it empties; a navigation (a link, Back or the kind selector) that leaves such a field
holding a different value drops the entry (`forgetUntyped`), so the link never carries an empty or stale
number; a link that writes the same value back, as on the round trip from bolt to nut, keeps it. "Typed"
still means an input event, and only typing writes the memory. This amends the amendment above where that
one says only that a value a link, Reset or a kind change wrote is not typed: such a write now also forgets
the entry of the field it changed. What does not change: `PartInfo.counterpart` (D-02), the API,
`screw info`, no default (D-01, L02, PAIR-02), page memory only. Plan 05-23 names the two new tests and the
probe record in 05-23-SUMMARY.md.
Reversibility: reversible. It is page state; no published shape changed.

## L16 — The nut's fine STL is capped on m per (d, pitch, hand) from run 2026-10-21-nut-fine-caps-amended, measured at clearance 5.0 mm and s 1e5 mm; a clearance above 5.0 mm is refused

Date: 2026-10-21. Decided by the owner on 2026-10-20 (R16, `option-a`) and 2026-10-21 (R17), recorded in
`.planning/phases/05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md`. This entry supersedes L15's nut
fine-STL paragraph (R12; 05-05).

**Why clearance is part of the key.** The rod's cap is keyed on (d, pitch, hand) to a length, and only
the length moves a rod's fine bytes. A nut's fine bytes also move with its clearance, a required free
field. The planner's scratch probe of 2026-10-20 (plan 05-19, Task 1; not a record, evidence about the
key only) read M20 right m 20 s 30 at 17.1 MB (clearance 0.1) against 22.4 MB (2.0) and 34.2 MB (4.9),
and m 40 at clearance 4.9 over the budget (1.018 of 64 MiB) where clearance 0.1 was 37,986,035 bytes;
at clearance 50 and m 20 it read 1.84 of the budget. A cap keyed on (d, pitch, hand) alone at one small
clearance would pass a nut over budget. The owner chose a ceiling C = 5.0 mm, the largest clearance
any GOST ISO 4032-2014 row's own s admits ((30 - 20) / 2 at M20, since s > d + 2c), and a refusal above
it, which closes T-05-12 on both m and clearance. Not chosen: C = 1.0 mm (option b, larger m caps, a
loose fit on a catalogue nut refused) and a ceiling that serves above it uncapped (option c, leaves
clearance 50 at 1.84 of the budget).

**The rule, fixed before any row ran** (`bench/nut_fine_caps.py` docstring, committed in `0c349a7`):
for each of the 30 keys (the 15 ISO 262 coarse (d, pitch) by both hands), the nut `NutParams(d, pitch,
s = 1e5, m, clearance = 5.0, hand)` for m = 1, 2, 3, ... mm, built and meshed by the shipped
`screw.solid.export(p, "stl", "fine")` at the fine preset (0.01 mm, 0.1 rad); a row fits when its STL
plus its gzip level-1 copy is at most 64 MiB (`BUDGET_BYTES`, the rods' constant); the cap is the
largest m that fits below the first that does not. Five checks at each cap: s = 1e5 at clearances
-0.05, 0, 0.1 and 2.5, and clearance 5.0 at the slimmest s (d + 11). s = 1e5 is `INTERIM_MAX_MM`; s
adds a near-constant number of bytes that does not grow with m (the planner's probe), so a cap at the
largest s holds for every s.

**Two runs.** The first run, `2026-10-20-nut-fine-caps` (HEAD `0c349a7`), measured all 30 caps and
stopped on 46 check rows the shipped build refused with `BuildError: Geometry kernel produced the wrong
lead-in countersink` (s = 1e5 and clearance -0.05, 0 or 0.1). The owner ruled (R17) that a check the
build refuses is "not a file", recorded with its error and not a stop, every other stop condition
unchanged, under a new run id. The amended run, `2026-10-21-nut-fine-caps-amended` (HEAD `63c22a6`, the
instrument amended in `9b4fbb7` before any of its rows), met no stop condition and reproduced the
first run's 1236 rows with identical bytes: 1086 ladder rows built, 104 checks built and fit (largest
0.960 of 64 MiB), 46 refused. The refusal is filed:
`docs/tech_debt/active/2026-10-21-nut-lead-in-gate-refuses-a-valid-nut-at-huge-s.md`. Records:
`bench/results/phase-05/nut-fine-caps.jsonl` and `nut-fine-caps-amended.jsonl`; entries in
`bench/RESULTS.md`.

**Caps** (`NUT_FINE_STL_ROWS`, the largest whole mm that fits; each is 0.954 to 0.995 of the budget and
cap + 1 is over it). Right hand: M2 12, M2.5 13, M3 15, M3.5 18, M4 21, M5 24, M6 30, M7 30, M8 38,
M10 36, M12 41, M14 46, M16 45, M18 54, M20 36 mm. Left hand: M2 15, M2.5 17, M3 19, M3.5 22, M4 25,
M5 30, M6 38, M7 38, M8 47, M10 50, M12 56, M14 61, M16 59, M18 73, M20 47 mm. The smallest margin over
a GOST ISO 4032-2014 height is M20 right, 36 mm against 18 mm; every catalogue row is served at its
own s and m_max (a test). The values are proven against both runs' records by
`tests/test_thread_maths.py::test_nut_fine_stl_every_cap_is_recomputed_from_the_committed_records`,
which also compares each header's preset with `screw.solid.TESSELLATION["fine"]`, so a preset change
fails until the caps are re-measured; no cap is typed to match.

**Behaviour.** `calc.thread.nut_fine_stl_refusal(d, pitch, m, clearance, left_hand)` is called by the
nut branch of `download_refusal`, before the cache, the admission slot and the pool: API 422
`fine_stl_cap` (loc `["query"]`), CLI exit 2 with nothing written, and the same sentence on the info
document's stl/fine download entry and in its warnings. The clearance is judged first. A sentence
beginning `clearance: ` is returned for a clearance above 5.0 mm on a measured key; one beginning
`m: ` for an m past the key's cap. Both name the run and offer the preview STL and the STEP, which are
never refused. A nut off the 30 keys gets no cap: the rods' `FINE_STL_ROWS` is never applied to a nut
and no nearest row is used (D-03, L02). Nothing is trimmed (L02, D-02).

Reason: the cap is a number someone will cut metal against, so it comes from a recorded run whose rule
preceded its rows, per key, and a request outside what was measured is refused naming the field and
not served on a guess. The owner's choice of a refusal above C over serving uncapped is the
difference between closing T-05-12 and carrying it.

Reversibility: reversible. The caps and the ceiling are constants with a cited run; Phase 7 re-measures
on linux/amd64 (OPER-02), and the clearance ceiling can be raised by a new run.

## L17 — The nut's clearance default is 0.15 mm, read by the pre-registered D-07 rule from run 06-print-run-1 on the owner's print profile

Date: 2026-10-23. Decided by the rule D-07, fixed in PR A before the first print, and by the owner's
`permanent: accepted` on 2026-10-23, given to the question of shipping 0.15 mm as the nut's clearance
default, frozen forever (06-06 Task 1). This entry supersedes L15's no-default rule for `clearance` (05
D-01, PAIR-01) and nothing else of L15: the two refusals (the void's root radius, a void wider than the
flats) and the absence of a lower bound stand.

**Why.** PAIR-02 and L02: a default is a reading of the owner's printed test, never a forum or vendor
figure, and `clearance` stayed required until a record existed. The owner's 0.1 mm was the
pre-registered prediction (D-01) and never an input. The reading did not match it: M10 and M12 bind at
0.1 mm in 3 of 3 samples, so the larger pair sets the default and it is 0.15 mm, not 0.10 mm.

**The rule, as committed before the run.** `06-PRINT-PROTOCOL.md` ("Rules", D-05 to D-08) and
`bench/print_rules.py` (`read_matrix`, `default_from`), on `main` in PR A (#19), squash commit `16f7041`.
A sample passes or binds by the hand fit test (D-05); a cell (size, clearance) passes when all 3 samples
do; the default is the smallest ladder step from which every cell of every size passes, and no default is
returned when no step qualifies or a size is not monotone (D-08).

**The run.** Run `06-print-run-1`: the ladder 0.05, 0.10, 0.15, 0.20, 0.25 mm at M6, M8, M10 and M12,
3 samples per cell, 60 nuts and 12 bolts. The parts are the product's own fine exports (24 STL files),
and their manifest `bench/results/phase-06/manifest-run-1.tsv` (sha256
`b98c445f88c1b7d21e198deb5d2ef17a77b698310b969d0e2b90f1cb445edb0d`) was committed in `646b07d` before the
first print. The record `bench/results/phase-06/print-run-1.tsv` has sha256
`f76753ded41726daec0a11ec4c5eabc5f4d2afb094cbe258d5e9d915aa6db725`, pinned as `RUN_1_SHA256`, and the
run was recorded in `3273e51`. The owner reported the fit results and confirmed the 60-row table
("correct", 2026-10-23); the cells were transcribed from that report, not typed by the owner, and the
owner gave no print or test dates. The pass counts (every size 3/3 from 0.15 mm up; M6 and M8 also 3/3
at 0.10; 0 of 3 at 0.05 everywhere; 42 passes, 18 binds, no reprint) are in `bench/RESULTS.md`, "Printed
pair matrix (Phase 6, 06-print-run-1)". Two tests hold the value to the record:
`tests/test_print_rules.py::test_the_shipped_clearance_default_is_the_one_run_1_reads` and
`tests/test_params.py::test_the_clearance_default_is_the_frozen_value_l17_records`.

**The profile this default holds for (D-06).** Prusa MK4, 0.4 mm nozzle, Prusa PETG, 0.2 mm layers,
PrusaSlicer with the stock Prusa PETG system profile (no settings changed; slicer version not
recorded), nut on its face and bolt head-down. For any other printer, material, layer height, nozzle or
orientation the default is untested.

**One-way (D-07).** From this entry on, every shareable link that omits `clearance` means 0.15 mm
forever (L02). A later reading, from run 2 or a second run, is a new decision that supersedes this one;
it never edits the value in place. The default is one value for every size; the threshold for small
sizes is run 2's question and gets its own entry, L18, after run 2 (R7).

**Outside the measured range (D-09, R6).** The matrix spans d = 6 to 12 mm. A nut with `d < 6.0` or
`d > 12.0` will carry a warning that the default was not measured at its size; plan 06-07 wires it, and
it fires whether or not `clearance` was typed.

**Kernel verdicts at 0.15 mm.** The recorded K = 3 pair verdicts (`tests/data/pair_expected.tsv`) at
0.15 mm are `proven` for both same-hand pairs and `violated` for the mixed-hand pair at M6, M8, M10 and
M12, so no size of the matrix reads `inconclusive` here. Two sizes outside it do, for both same-hand
pairs: M3 and M18. That is a kernel scoping fact (L11) and not a print result, and the pair verdict was
never an input to D-07 (a kernel `proven` is necessary, not sufficient, PAIR-05). The ladder's top step
0.25 mm is not in the recorded grid, and `PAIR_CLEARANCES` (0.05 to 0.20 mm in `calc/pair.py`), which
its comment says brackets Phase 6's matrix, no longer brackets it.

**What it does not show.** One printer and profile. Four coarse sizes, M6 to M12, three samples each;
nothing between or beyond them, and nothing for fine pitch. A nominal bolt against a nut with a
clearance, not a toleranced pair. A hand judgement under D-05 with turns recorded as 0 for every bind, so
it says nothing about how far a tight cell is from passing. Whether 0.15 mm also suits a part printed
upright or on a finer layer is open.

Reason: the number someone cuts metal to comes from a recorded test whose rule preceded its rows, and
the owner accepted it as permanent before it shipped.

Reversibility: one-way. Changing it later changes parts people already linked, so it takes a
superseding decision and never a silent edit.

## L18 — The printability threshold is M4 (d_min 4.0 mm, P_min 0.7 mm), read by the pre-registered D-10 rule from run 06-print-run-2, which is weaker evidence than the pre-registered run

Date: 2026-10-23. Decided by the rule D-10 (with D-11), fixed in PR A before any part was printed, and by
owner ruling R7 (L18 for the threshold after run 2). The record it reads was accepted by owner ruling R10
(`.planning/phases/06-printed-pair-acceptance/06-OWNER-RULINGS.md`, 2026-10-23), and the evidence is
weaker than the pre-registered run would have given; the next section says how.

**Why.** INFO-04 and L02: a number the tool prints is a number someone will cut metal to, so the size
below which a part is warned about is a reading of the owner's printed test and never a forum or vendor
figure. `D_MIN_MM` and `P_MIN_MM` in `src/screw/calc/printability.py` are not typed from a guide: they are
M4's d and ISO 262 coarse pitch, the size `threshold_from` returns for the pinned record.

**The rule, as committed before the run.** `06-PRINT-PROTOCOL.md` ("Rules", D-10, D-11) and
`bench/print_rules.py` (`read_small`, `threshold_from`), on `main` in PR A (#19), squash commit `16f7041`.
The threshold is the smallest of M3, M4 and M5 that passes 3 of 3 together with every larger one of the
three, and M6 when none does (D-10); `d_min` and `P_min` are that size's d and coarse pitch (D-11). The
owner made no prediction for it.

**The run, and why its evidence is weaker (R10).** Run `06-print-run-2` is the owner's own earlier
prints, made informally before the default shipped, accepted as the run-2 record by owner ruling R10 over
Claude's recommendation to re-run it as pre-registered. It is therefore **not** the pre-registered run:

1. The parts did not come from `python -m bench.print_matrix export run-2`, and **no manifest was
   committed before printing** (`manifest-run-2.tsv` does not exist). Nothing in the repository ties the
   printed nuts to the shipped default's STL bytes; the link is the owner's word that the 0.15 mm result
   is the one recorded. The pre-registration's mitigation that every printed nut name carries the shipped
   default and every file its digest had nothing to check.
2. The owner tested a clearance ladder on M4 and M5, not only the default; only the 0.15 mm result
   (L17's default) is in the record, and the other observations are prose in `bench/RESULTS.md`.
3. The thread of M3 did not print, and the record has only pass and bind, so each M3 sample is recorded
   `bind` at 0 turns with the note `thread did not print`. M2 was printed too and is outside the record.
4. Three samples per size, each on its own bed (M3-1 to M5-3), and no print or test dates were reported.

The record `bench/results/phase-06/print-run-2.tsv` has sha256
`6c2d924006db1ccca860b665fdc2cbcd3c84137b0edefb417e6c31aab9dd923e`, pinned as `RUN_2_SHA256` and recorded in
`d51438a`. The owner reported the fit results; they were transcribed by Claude and confirmed by the owner
as correct (2026-10-23), so the cells are not the owner's typing. The result per size is in
`bench/RESULTS.md`, "Printability run (Phase 6, 06-print-run-2)": M3 passes 0 of 3, M4 and M5 pass 3 of 3.
`threshold_from` returns **M4**.

**The warning (D-13).** A bolt or a nut with `d < 4.0` mm or `pitch < 0.7` mm carries one printability
sentence in `warnings`, naming each edge crossed (d first, then pitch), the size, the run and this entry,
and saying the parameters are left as set (wording corrected after the phase-6 code review, WR-02).
It comes from `derive()` alone, so the page, the API and the CLI print the same sentence. The comparison is strict `<` on the stored floats with no rounding or tolerance:
exactly M4's d and pitch are not warned about. SC5 asks for cap-and-warn; it is a warning and no cap,
because nothing can be trimmed without changing a d or pitch the user set (L02), and it is never a 422
because the two numbers are not a conflict between two things the user asked for. M2 and M2.5 warn on
both edges by construction (D-12), and M12 x 0.5 warns on pitch only. These tests hold it:
`tests/test_print_rules.py::test_the_printability_threshold_is_the_one_run_2_reads` re-derives both
constants from the pinned record on every `make verify`, so editing either alone fails, and the calc and
parity tests assert the edges, the order, that the part still builds and that the CLI and the API agree.

**The profile it holds for (D-06).** Prusa MK4, 0.4 mm nozzle, Prusa PETG, 0.2 mm layers, PrusaSlicer
with the stock Prusa PETG system profile. For any other printer, material, layer height, nozzle or
orientation the threshold is untested.

**What it does not show.** Coarse pitches only: M3, M4 and M5 at their ISO 262 coarse pitch, three samples
each. A fine pitch at or above M4 is judged by `P_min` alone (a pitch below 0.7 mm warns), not by a print.
One profile. M3 failed because its thread did not print on a 0.4 mm nozzle at 0.2 mm layers; the record
cannot say whether a finer nozzle or layer would have printed it. A nominal bolt against a nut with a
clearance, not a toleranced pair. A hand judgement under D-05. And, per R10, nothing here ties the printed
nuts to the shipped default's export.

Reason: the threshold the tool warns at comes from a recorded printed test read by a rule that preceded
it, and the entry says plainly that the record is the owner's earlier prints and not the pre-registered
run.

Reversibility: costly. It moves only warnings, never a part, but a different `d_min` or `P_min` needs a
new pre-registered run and a superseding entry, never a silent edit of the constants.

## L19 — The bolt's hex head is chamfered on its top face by a head_chamfer angle, default 30 degrees, a cone from s / 2 cut no deeper than k / 2; this supersedes L13 D-01's sharp top

Date: 2026-10-24. Decided by the owner's ruling of 2026-10-24 (ROADMAP Phase 06.1: the field
`head_chamfer`, the default 30, 0 for the sharp head, the top face only, the cone from `s / 2`, the phase
inserted before Phase 7 so that the re-sweep measures the chamfered head), by the phase discussion
(D-01 to D-15) and by the plan-phase rulings (D-16 to D-19), all in `06.1-CONTEXT.md`. It supersedes
L13 D-01's "no top chamfer" and nothing else of L13: there is still no washer face, the bearing face is
unchanged, and `hex_prism_volume` and `bolt_closed_volume` stay sharp because `bench/` reads them. Every
figure below names a test, a file or the research measurement it comes from (`06.1-RESEARCH.md`, scratch
runs of 2026-10-24); nothing is measured again here.

**Why.** L13's own reversibility note allowed "a later head chamfer" while the standing warning says "not
a product build", and the owner ruled that the Phase 7 re-sweep should measure the head a user will
print. L02 decides each branch below: a number the tool prints is one someone cuts metal to, and a
parameter the user did not set must never silently change the part.

**The model (D-01 to D-03).** `head_chamfer` is an angle in degrees from the top face, `0 <= angle < 90`,
validated once at the model (`ge=0`, `lt=90`, finite; the schema carries `minimum 0` and `exclusiveMaximum
90`). 0 is today's sharp head: no cut and no volume term. Above 0 the cutter is a cone from the inscribed
circle `s / 2`, so it clips the six corners; its depth at a corner is `(s / 2 / cos 30 degrees - s / 2)
tan(angle)`, and the cut is no deeper than `k / 2`, which mirrors the nut's `m / 2` (L15), so the lower
half of the head keeps its corners and the bearing face is untouched. **The default 30 and the 15 to 30
degree band are a stated model.** The band is the one the R4 a read prints for the nut's corner chamfer
(GOST ISO 4032-2014 (ISO 4032:2012) Figure 1 footnote b, `05-OWNER-READS.md` read 3), applied to the
bolt head by the owner's ruling. No repo note records a read of the head figure of ISO 4014 or ISO 4017,
and those texts are not purchased (L14), so no edition of either is cited for the band. An angle in
`(0, 15)` or `(30, 90)` builds as asked and warns, naming `head_chamfer` and the band (D-02); 0 is not
off the band.

**Cap, warn or refuse (D-04 to D-06).** One predicate, `head_chamfer_depths(s, k, angle)`, gives the
model depth and the depth cut, and one threshold: the model depth above `k / 2`, strict, so an equal
depth builds uncapped. A defaulted angle over it is cut at `k / 2` and warned, naming `head_chamfer` and
`k`, in the style of the nut's `end_depths` warning. An **explicit** angle over it is a 422
`head_chamfer_conflict` with `ctx.fields` `["head_chamfer", "k"]` (CLI: exit 2, the same sentence),
decided at the request boundary by `calc._bolt_explicit_conflict`, which `app.refuse_explicit_conflict`
and `cli._params` both call, because FastAPI 0.142.2 copies every default into the query model and the
model cannot tell an explicit value from a default (L13 D-25). The rule needs only `head_chamfer`
explicit: `s` and `k` come from the request, or from the frozen `BoltParams` defaults when the query
does not name them (`?head_chamfer=80` alone is judged at `s` 10, `k` 4); a preset's `s` and `k`, filled
by the CLI before the check, count as given; `thread_length` is judged first. The page writes only the
fields that differ from their defaults, so a typed 30 is never explicit there. **The owner's D-25
exception is extended to this one rule and no other (D-06):** a direct `BoltParams(head_chamfer=80)` is
not refused, it is capped and warned. At the default part (`s` 10, `k` 4) the cap binds from
68.85595459078384 degrees; it binds at 30 degrees whenever `k < 0.0893 s`.

**The closed form (D-07, D-08).** `head_chamfer_volume(s, angle, depth)` in `calc/thread.py` is analytic,
pure `math`, no `cadquery`. Uncapped it is `tan(angle) (s / 2)^3` times `4/3 + pi/3 + ln 3 - 2 sqrt 3 =
0.015041558060286064`; capped it is the same integral cut at the depth, written with `depth / tan` formed
directly, `atan2` and `asinh`, and a series below `theta` 0.05, because the first form measured
`-49.5 mm3` at 89.99999999999999 degrees. It raises `ValueError` where it has no honest volume (angle 0,
90, negative or not finite, a tangent that underflows), so `derive` prints no number for that part. It
agreed with an independent Gauss-Legendre reference to 3.4e-14 over 600 rows and with both shipped numeric
oracles (`face_chamfer_volume`, and the polar integral in `tests/test_end_oracles.py`) to 4.3e-10 over 108
rows, which is the midpoint rule's own error. The default part's term is 1.0855309493921927 mm3, 0.135 %
of its volume, and `bolt_end_closed_volume` takes `head_chamfer` as a required argument and subtracts it.
The two numeric forms stay as test oracles; the nut keeps its numeric oracle (moving it is a deferred
idea).

**The cut and its gate (D-09).** `_build_bolt` cuts the cone on the head prism before the fuse and judges
the volume it removed against `head_chamfer_volume` at `T_PIECE` (R11, named "head chamfer") before the
whole bolt is judged at `T_GATE`. The measurement that placed it: on the prism the piece error is 6.7e-5
at 0.01 degrees and at most 1.4e-6 from 0.5 degrees up; after the fuse a constant +5.5e-5 mm3 bias of the
thread-bearing solid false-refused M6 at 0.01 degrees (+1.7e-1) and M2 at 0.1 degrees (+1.4e-1) against
`T_PIECE` 0.03. About 0.03 s per build; 18 whole-bolt, 100 head-only and 60 watertight cases passed
(macOS arm64, single runs, host loaded for the timings). Phase 7 measures the added cost. Positive
controls by test name: `test_a_skipped_or_wrong_head_chamfer_is_refused_naming_the_piece` (a skipped cut
reads -1, a 45 degree cut, and a skipped 1 degree cut that the whole-part gate alone passes).

**The info document (D-10 to D-12, D-19).** With `head_chamfer` above 0 the Head group gains four rows,
`head_chamfer` (labelled a stated model), `chamfer_depth` (as cut, so `k / 2` on a capped head),
`chamfer_circle_diameter` and `corner_edge_left`, each with its formula; the volume row's formula names
the term. At 0 none of them appear and the note `SHARP_HEAD_NOTE` is on **every** such part, whether or
not it matches a catalogue row (D-19), with the `PartInfo.notes` description reworded to say so. The
band and cap warnings follow the thread warnings and precede the no-row warning. The standing warning
is now `ends modelled per L15 and L19: bolt tip chamfer, hex head chamfer, under-head fillet on an ISO
4014 plain shank, nut lead-in countersinks and face chamfers; nominal, not toleranced; not a product
build` (`STANDING_WARNING`, verbatim on the page, the API and the CLI). L13's and L15's quotations of the
earlier standing warnings stay as history.

**Presets, the pair and tiny angles (D-13, D-17, D-18).** A preset never sets the angle and `match`
ignores it: no row prints an angle, because the figure is a band, so a sharp and a chamfered M6 x 20 are
both `iso4017:M6x20`. **D-14 is corrected (D-17):** the kernel pair proof's shipped evidence bolt
(`solid/pair.py`, built from a real `BoltParams`) now carries the default chamfer; `pair.py` is
unchanged, the chamfer lies on the head's top face, above the nut, so no reading changes, and
`tests/test_pair.py::test_the_evidence_bolt_carries_the_default_head_chamfer_and_still_builds` documents
it. There is no angle floor (D-18): a tiny or near-right angle builds inside both gates or is refused as
a `BuildError` (API 422 `build_error`), never a 500 or a wrong number. Measured: 0.5, 89.9, 1e-4 and
89.99999999999999 degrees build; 1e-6 and 5e-324 are refused by name; `derive` reports no volume for a
value with no honest one (`tests/test_solid.py::test_a_tiny_or_near_right_head_chamfer_builds_inside_its_gates_or_is_refused_by_name`,
`tests/test_calc.py::test_derive_never_raises_on_a_tiny_or_near_right_head_chamfer`).

**Published shapes (D-16).** The field is declared last in `BoltParams`, so the old slug is the prefix of
the new one and every default download name gains `_head_chamfer30`
(`bolt_d6_pitch1_left_hand0_length20_s10_k4_thread_length20_head_chamfer30`). The generic kernel-failure
text names `head_chamfer` last, the schema gains the property, and the CLI gains `--head-chamfer`.

**What it does not cover.** The nut: its angle stays `CHAMFER_ANGLE_DEG` 30 and a nut field is not asked
for. The fine-STL caps and the build timeouts, which L13 and L16 measured on the sharp head; Phase 7
(OPER-01, OPER-02) re-measures them on the chamfered one. The printed runs of L17 and L18 had sharp heads;
the chamfer is on the head's top face, away from the thread the nut engages, so nothing those runs read
changes. A bare `L19` in the gzip text of `bench/RESULTS.md`, `bench/README.md` and `Makefile` means
spur L19, the gzip level rule; in `src/` and `docs/` outside those, a bare L19 is this entry.

**Tests that hold it.** Closed form: `tests/test_end_oracles.py::test_the_head_chamfer_matches_both_oracles_capped_and_uncapped`,
`::test_the_head_chamfer_of_the_default_part_is_the_pinned_closed_form`. Field:
`tests/test_params.py::test_the_head_chamfer_is_an_angle_field_in_the_head_group_declared_last`,
`::test_a_head_chamfer_from_0_to_below_90_is_accepted_and_any_other_value_is_refused_naming_it`. Cut and
gates: `tests/test_solid.py::test_a_head_chamfer_of_zero_builds_todays_sharp_head`,
`::test_a_direct_head_chamfer_deeper_than_half_k_is_capped_and_builds_through_both_gates`. Info document
and warnings: `tests/test_calc.py::test_a_chamfered_head_reports_its_angle_depth_as_cut_circle_and_edge_left`,
`::test_a_sharp_head_has_no_chamfer_rows_and_carries_the_sharp_head_note`,
`::test_an_off_band_head_chamfer_builds_as_asked_and_warns_naming_the_band`,
`::test_the_standing_warning_is_first_and_verbatim`. Request boundary:
`tests/test_calc.py::test_the_bolt_rule_refuses_an_explicit_head_chamfer_deeper_than_half_k_reading_defaults`,
`tests/test_api.py::test_an_explicit_head_chamfer_exactly_at_half_k_builds_uncapped_and_one_float_less_k_is_refused`,
`tests/test_cli.py::test_an_explicit_head_chamfer_deeper_than_half_k_exits_2_and_writes_nothing`,
`tests/test_parity.py::test_a_head_chamfer_conflict_is_the_same_words_on_the_api_and_the_cli`. Presets:
`tests/test_presets.py::test_a_preset_never_sets_the_head_chamfer`.

Reason: the head a user prints has chamfered corners, and the part a user asks for must be the part they
get (L02). The owner ruled the default, the closed form stays exact for the part as cut, the cut is
judged on its own volume where its error is measurable, and a conflict between two things the user asked
for is refused by name where the provenance of a value exists, the request boundary.

Reversibility: one-way for the name `head_chamfer`, the default 30 and the slug suffix
`_head_chamfer30` (every shareable link and file name that omits the field depends on them, so changing
any of them changes parts people already linked). Costly for the 422 type, its `ctx.fields` and the CLI
exit code (D-06: every client and the parity test read them) and for the warning texts, the note and the
row labels (D-12, the published shape of the info document, L13). Reversible for where the cut runs in
the pipeline and for its piece gate: both are internal.
