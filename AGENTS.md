# screw — AGENTS.md

Standing brief for every AI agent working in this repo. Read it first. All agents
(Claude Code, Codex, Cursor, ...) read this one file; `CLAUDE.md` is a symlink to it.

Keep this file short. It is loaded on every interaction. Project detail lives in `docs/`
and is read on demand.

## What we're building

A parametric thread and fastener generator — screws, bolts, nuts, threaded rods. Set the
parameters, get a live 3D preview, the numbers you would measure on the real part, and an
STL or STEP download — from a web UI, an HTTP API or a CLI, all driven by one parameter
model. The sibling of `spur` (github.com/halfb00t/spur, gears), built to the same rules.

**Nothing is built yet** (2026-10-05): this tree is the foundation. Full intent and the
owner's decisions: `.planning/PROJECT.md`; scoped requirements: `.planning/REQUIREMENTS.md`;
phases: `.planning/ROADMAP.md`; research: `.planning/research/SUMMARY.md`. System map:
`docs/architecture/overview.md`. Global requirements: `docs/requirements/`. How the human
drives this: `docs/HOW_TO_DEVELOP.md`.

## Stack

Python 3.12 only (`cadquery-ocp` publishes wheels for nothing newer, L01), CadQuery /
OpenCascade for the solid, FastAPI + Pydantic v2 + uvicorn for the API, argparse for the
CLI, pytest for tests, Docker + GitHub Actions for delivery. A viewer, when it arrives, is
vanilla JS plus a vendored three.js bundle.

Why this stack and every other locked choice: `docs/architecture/decision_log.md` (cite
decisions by id, e.g. L01). Decisions inherited from spur are cited there as `spur Lxx`;
a spur checkout at `../spur` is the house-style reference, not code to copy blindly.

## How to verify (the gate)

Nothing is "done", "fixed", or "working" until checks pass. The one command:

```
make verify
```

It runs ruff, mypy `--strict`, the import-boundary contracts, an unfinished-work scan and
pytest. It needs no Docker. The same command runs in the pre-commit hook, in CI and
inside `make worktree.land`.

State the command you ran and the result line in your reply. Predicting that tests pass is
not the same as running them.

## Stop and ask first

Surface to the human and wait for a decision when:

- An architectural claim isn't in the decision log.
- A locked decision (Lxx) looks wrong — propose superseding it, don't just ignore it.
- A plan's acceptance criterion cannot be met as written. Build to the spec exactly, or
  stop and surface options — never a quiet approximation.
- A library/API behavior is unverified after a real check.
- Evidence conflicts (doc vs code vs prior decision vs what the human said).
- A destructive operation is involved (`git reset --hard`, force push, `rm -rf`, dropping
  data, deleting branches, overwriting uncommitted work).
- A choice trades stability for speed — pick stability and surface it.

Ask format: the trigger, 2-3 options, your recommendation, then wait.

## Decisions

- `docs/architecture/decision_log.md` is the single source of locked decisions.
- New non-trivial choice: give 2-3 options + tradeoffs + a recommendation, let the human
  pick, then log it as a new `Lxx`. Don't re-litigate logged decisions.
- Ground claims in evidence: a cited decision, a file you read, a command you ran, docs you
  fetched, or the human's confirmation. Flag guesses as `ASSUMPTION:` and surface them
  before acting.

## This project's standing rules (L02)

They are easy to break by accident and expensive to notice later:

- **A number the tool prints is a number someone will cut metal to.** If a value cannot be
  computed honestly, report a warning and no number — never a plausible one.
- **A parameter the user did not set must never silently change the part.** Defaults are
  absolute millimetres and stay put, because every shareable link that omits a field
  depends on them. A dimension that can be trimmed without contradicting an explicit
  choice is capped and warned about; a direct conflict between two things the user asked
  for is a `422` naming the fields, not a guess.

## Keep it simple, keep it small

- Simplest solution that actually works. Three similar lines beat a premature abstraction.
  Don't add speculative features or flexibility nobody asked for.
- Default to surgical edits. Don't refactor or rename adjacent code unless asked; note the
  tangent and raise it after.
- One concern per commit. Commits are semantic checkpoints — one logical unit of work, not
  micro-commits. Mixed-concern diffs hide regressions.
- New code follows the repo's naming, structure, error model and file layout. Consistency
  with what exists beats a locally better idea; if the existing shape is wrong, that is a
  decision to raise, not a precedent to break quietly.

## Finishing work properly

New behavior ships with its tests in the same change. Claims about performance or memory
are measured and the numbers recorded, not estimated. Don't leave `TODO`, `pass` or
unreachable branches as if they were finished; `make verify` fails on the markers. A
deliberate corner cut is a `docs/tech_debt/` item with the owner's sign-off, never silent.

## Capturing ideas and debt (don't lose them)

Non-blocking work survives in files, not just in a reply. One file per item,
`YYYY-MM-DD-short-slug.md`, from `docs/<dir>/TEMPLATE.md`; add a row to that dir's
`INDEX.md` in the same commit.

- Good idea that isn't for now → `docs/ideas/`.
- Known-bad code, missing test, risky shortcut, deferred fix → `docs/tech_debt/active/`.
  Tag `Severity:` — **blocker** (corruption / silent partial success / source-of-truth /
  paid-API drain) | **must** (correctness/maintainability, or deferred with a named
  trigger) | **nice**.
- Blocker → fix it now or stop and ask; never just file it and move on.
- On fixing debt: flip `Status: resolved`, add the commit sha, `git mv` into
  `docs/tech_debt/resolved/`, move the INDEX row — in the same commit as the fix.
- Before your final reply, state whether you filed any item and its path.

## Tools and skills

- Reuse the project's command surface (`make`) instead of ad-hoc shell. `make` on its own
  lists every target. Check for an existing one before inventing a command.
- Planning and execution: gsd skill suite. Start file-changing work through a gsd entry
  point so `.planning/` and the execution context stay in sync — `/gsd-fast` for a trivial
  inline task, `/gsd-quick` for small fixes and doc updates, `/gsd-debug` for
  investigation, `/gsd-execute-phase` for planned phase work. No direct repo edits outside
  a gsd workflow unless the human explicitly asks to bypass it. There is no
  `.claude/CLAUDE.md`: this file is the only instruction file, as in spur.
- User-facing text (explanations, reviews): caveman — terse, no filler.
- Commit messages: Conventional Commits, normal prose — NOT caveman.
- Writing code: ponytail — simplest thing that works, no speculative abstractions.
- Project-specific skills live in `.ai_skills/` (see its `README.md`). When a project
  workflow repeats, add a skill there (use `skill-creator`) instead of re-deriving it each
  session.
- Cross-CLI review: this repo is set up for both Claude Code and Codex. Whoever wrote the
  diff does not review it.

## Code style

Full coding standard: `docs/CODING_VALUES.md` — read it before writing code. The
essentials:

- Comments explain *why*, and carry the measurement or the constraint that forced the
  choice. spur's comments set the standard ("1578 MiB resident without this, 360 MiB with
  it"); match it or don't add one.
- Pure maths stays out of the CAD kernel's way: the thread-maths module runs on every
  keystroke and must never import `cadquery`. Its import-boundary contract lands in the
  same commit as the module.
- Vendor types stop at their boundary. `cadquery` objects do not escape the solid module.
- A parameter is validated once, at the parameter-model boundary, and trusted afterwards.
- `Any` is not written here (L04). A genuinely untyped value is `object`, narrowed where
  it is used.
- English throughout: identifiers, comments, commits, PR titles.
