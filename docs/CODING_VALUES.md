# screw — Coding Values

What code this project welcomes and rejects. Agents read this before writing; reviewers
judge against it. `AGENTS.md` carries the short version loaded every turn — this is the
full reference, read on demand.

The owner can override any value — when they do, log it as a decision (`Lxx` in
`docs/architecture/decision_log.md`) and update this file. An agent that disagrees with a
value raises it; it does not quietly ignore it.

screw is spur's sibling and inherits its coding values wholesale; spur's
`docs/CODING_VALUES.md` is the worked version of this file, with real modules behind every
example. Where this file names a module role ("the maths module", "the solid module") the
file name is gsd's to fix when the module lands; spur's are `calc.py` and `model.py`.

Sections the template ships that are **deliberately absent**: there is no database, no
queue, no cache server, no external service client, no migrations and no authentication.
Do not add a section back speculatively — add it when the thing exists.

## Vision

Code reads like the architecture says it works. Open a file and see its responsibility,
its data and its failure path. Stable beats fast.

The one asset easy to destroy and hard to rebuild: **comments carry the measurement or
the constraint that forced the choice.** spur's read "1578 MiB resident without this, 360
MiB with it" and "~50x slower on a many-toothed outline". Match that standard or do not
add a comment. A comment that restates the code is worse than none; a comment that records
the number that settled an argument is the most valuable line in the file.

## Stack

Pointers only; the *why* is in `decision_log.md`.

- **Core + API:** Python 3.12, FastAPI, Pydantic v2, uvicorn. Why → `L01`.
- **Geometry:** CadQuery over OpenCascade. Why → `L01`.
- **Viewer:** vanilla JS + a vendored three.js bundle, when it arrives. Why → spur L11.
- **Delivery:** Docker, GitHub Actions. Closure pinning → `L06`.

## Code values

- **A wrong number is worse than no number.** This is the first rule, not a nicety. If a
  value cannot be computed honestly, return `None` and say why in `warnings` (`L02`).
  Never return a plausible one.
- **Never change the part the user did not ask to change.** Defaults are frozen; a
  dimension may be capped only when capping contradicts nothing the user set, and the
  cap must appear in `warnings` (`L02`).
- **Measure before you claim.** Performance, memory and size statements ship with the
  number and the workload that produced it. "Faster" without a figure does not go in a
  comment, a commit message or a reply.
- Explicit types at every boundary. Vendor types stop at their boundary — no CadQuery
  object escapes the solid module.
- `Any` is not written here (`L04`), and the type checker enforces it
  (`disallow_any_explicit`). A genuinely untyped value is `object`, narrowed where it is
  used; a value a library already names keeps the library's own alias.
- Self-documenting names. Domain names over pattern names — thread vocabulary in its
  standard form (`pitch`, `major_diameter`, `thread_angle`, `lead`), not `Manager`,
  `Processor`, `handle`.
- One operation per routine. A build pipeline is one product decision per step; keep it
  that way when adding a feature.
- Simplest thing that works. Three similar lines beat a premature abstraction.
- Limits live in code with an env var and a check, not only in infra.

## Coupling

The module graph is a designed object, not an accident, and it is enforced — see the
import-linter contracts in `pyproject.toml`. `make verify` fails on a violation.

- The maths module (and the parameter model) must never import the CAD kernel. It runs
  on every keystroke; the moment it can reach OpenCascade that property is gone silently.
- The CLI must never import the web layer (`fastapi`, `starlette`, the app module).
  Web-serving policy — admission control, queue depth — is not the CLI's to inherit
  (spur L04).
- The solid module is the only doorway to `cadquery`/`OCP`.
- Adding a module means deciding where it sits in that graph, and usually adding a
  contract in the same commit. A new contract is cheap; discovering an accidental cycle
  six months later is not.

## File and function boundaries

No line-count rules — they invite gaming. Surface a boundary problem to the human when:

- A function cannot be named in one sentence.
- A file mixes concerns — transport with geometry, policy with mechanics.
- A change needs editing three unrelated places.
- A parameter list passes ~5 raw arguments; group them into a typed object.
- Nesting passes ~3 deep.
- A function both decides and acts. The maths module decides; the solid module acts.

## Validation

Types are the primary contract, and validation happens exactly once.

- The parameter model is the inbound boundary for all three front ends. Range checks are
  field metadata; cross-field feasibility is one check called from the model validator.
- After that boundary, trust the types. Do not re-validate parameters downstream.
- An invariant a type cannot express is asserted positively, not assumed — a build checks
  that exactly one valid solid came out.
- Positive boolean names (`is_left_handed`, `has_chamfer`); negated forms are banned.

## Naming

English throughout: identifiers, files, comments, commits, PR titles. Domain terms in
their standard form. Single-letter names are acceptable only where they are the standard
symbol for the quantity inside a short mathematical routine (`P` for pitch, `d` for major
diameter, `H` for the fundamental triangle height), and the file must define them once.
Anything that escapes such a routine gets a real name.

## State

There is almost none, and it should stay that way.

- Nothing is persisted. Every answer is derived from the parameters on demand.
- Any cache is a speed optimisation and must remain safe to lose at any moment. Nothing
  may become correct only because something was cached.
- Process-level state (a kernel lock, a build semaphore) is module-level by necessity and
  documented where it lives.
- If this project ever needs durable state, that is a decision (`Lxx`) and a phase, not a
  module-level dict.

## Failure handling

Three responses, and picking the right one is the design work (`L02`):

- **Refuse** — a conflict between two things the user set explicitly. Name the fields.
- **Cap and warn** — a requested dimension that can be trimmed without contradicting an
  explicit choice. Never silent.
- **Report nothing** — a value that does not exist. A warning, not a number.

Beyond user input: fail loud, once, with an actionable message. There is no retry tier —
a kernel failure is deterministic for the same parameters, so retrying only burns seconds.
One exception type leaves the solid module, and it says what to try instead.

## Logging

None yet. When the service exists: one JSON-lines logger on stderr, configured at the
composition boundary, with one small intent-named function per event — callers never
assemble a log record by hand and never call `logging` directly (spur L20). The maths
module needs no logging ever — it is pure, and `warnings` is its diagnostic. No `print()`
for diagnostics in `src/`; a CLI printing to stderr is user-facing output, which is
different.

## Testing

Tests verify behaviour from the user's perspective. Asserting private calls or internal
call counts is banned.

- **Unit** — the maths module. Pure, fast, exhaustive on the rules. Test names read as
  requirements.
- **Integration** — the solid module against the real kernel. Do not mock OpenCascade; a
  mock would test the mock. Assert geometry (volume, topology, watertightness), not
  snapshots.
- **Contract** — the app through `TestClient`, including the error shapes the UI parses.
- **The README's own commands are tests.** A documented example that does not run is a
  bug with a test.
- New behaviour ships with its tests in the same change.
- A regression gets the test that would have caught it, named after the property, not the
  bug number.

## Tech debt and refactoring

- Refactoring for taste: no. Refactoring because a boundary broke: yes, as its own scoped
  task, surfaced first.
- Debt found during normal work becomes a `docs/tech_debt/active/` item — location, smell,
  suggested fix, and a trigger. Not a silent fix in an unrelated change.
- "Good enough for now" is not a reason to drop error handling or validation the contract
  implies. A deliberate cut is a logged item with the owner's sign-off, never silent.

## Dependencies

- A new dependency is a decision — ask first. The closure already carries ~1.4 GB of
  OpenCascade and VTK.
- `pyproject.toml` keeps loose ranges; `requirements.txt` is the generated, fully-pinned
  closure every install is constrained to (`L06`). Regenerate with `make lock`; never
  hand-edit a line.
- Prefer the standard library. `argparse`, not a CLI framework; `struct` to parse an STL,
  not a mesh library.

## Project-specific

- **Python 3.12 only** (`L01`). `cadquery-ocp` publishes no wheels past 3.12. `make venv`
  picks the interpreter itself. Do not lower the floor without a real interpreter for the
  new floor in CI, and do not raise the ceiling without checking wheels.
- **No automatic formatter** (`L05`). Line length and whitespace are linted; the
  arrangement within that is a human decision here.
