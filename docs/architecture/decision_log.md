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
