# How to develop screw (the human's guide)

The loop this repository is worked in with AI agents, and your role at each step. screw is
spur's sibling and runs the same loop. The wall around `main` (a ruleset plus
`make pr.land`, as in spur) is deliberately not up yet —
`docs/ideas/2026-10-05-wall-main-like-spur.md`.

```
discuss -> plan -> review the plan -> execute (phase branch) -> acceptance -> PR -> review by the other CLI -> merge
 you set    AI      you approve      AI builds on gsd/phase-NN      you check   CI    cross-check                 squash
 the goal  writes
```

One pass = one phase = one branch = one PR = one squash commit on `main`. Keep phases
small.

## 0. What is already guaranteed

- `make verify` — the one gate (L03): ruff, mypy `--strict` with `Any` forbidden (L04),
  the import-boundary contracts, the unfinished-work scan (`TODO`/`FIXME`/
  `NotImplementedError`), pytest. No Docker needed.
- The same `make verify` runs in the pre-commit hook (install once per clone:
  `.venv/bin/pre-commit install`), in CI (every push to `main` and every PR, Python 3.12)
  and inside `make worktree.land` before a merge. One definition of "passing" in three
  places.
- `requirements.txt` — the pinned closure (L06). CI and `make venv` install exactly it;
  `make lock` regenerates it from scratch.
- `AGENTS.md` — the rules an agent reads first; `docs/architecture/` — the system map and
  the `Lxx` decision log; `docs/CODING_VALUES.md` — what code is welcome here.

The first `make verify` after `make clean` builds `.venv` (~1.4 GB of OpenCascade) and
takes a couple of minutes — that is the install, not the tests.

## 1. Project start

`gsd-new-project` ran on 2026-10-05: `.planning/PROJECT.md` (intent and the owner's
decisions), `.planning/REQUIREMENTS.md` (39 v1 requirements), `.planning/research/`
(four research files and `SUMMARY.md`) and `.planning/ROADMAP.md`. The L02 rules (a
number or a warning, frozen defaults, cap-and-warn or `422`) were fixed before the spec;
the spec is built on them, not the other way round.

`.planning/config.json` has `git.branching_strategy: "phase"` (as in spur), so
`gsd-execute-phase` cuts the `gsd/phase-NN-<slug>` branch from `origin/main` itself.

## 2. Discuss a phase

`gsd-discuss-phase N`. Discuss what comes next. Your role: state the goal and the
constraints, not the solution.

## 3. Plan

`gsd-plan-phase N`. The agent writes a step-by-step plan into `.planning/`. Your role:
wait.

Cut the phase branch before the discussion —
`git switch -c gsd/phase-NN-<slug> origin/main` — so the discussion and plan commits do
not land on `main`. `gsd-execute-phase` reuses that branch.

## 4. Review and amend the plan

`gsd-review --phase N` — the other CLI reads the plan before anything is written.

**Never approve a plan you do not understand — ask until you do.** A mistake costs
minutes here and hours after the build.

Three things to check on every plan in this project:

- Does it change a part the user did not ask to change? Defaults are frozen (L02); every
  model link depends on them.
- Does a number appear that could be untrue? A warning without a number beats a plausible
  number (L02).
- Is there a measurement under every claim about speed or memory? Comments here carry the
  figure and the load it was taken under.

## 5. Execute on the phase branch

`gsd-execute-phase N`. `make verify` stays green throughout.

**A trap inherited from spur.** No worktree — an agent's or one made with
`make worktree.new` — has its own `.venv`. The temptation is to share the main checkout's.
Do not: the editable install in `.venv` points at the main checkout's `src/`, so
`import screw` from a worktree resolves back there and the tests silently check unmodified
code. Either `make venv` inside the worktree (the first `make verify` there does it — a
couple of minutes), or, once an image exists, `make test-image`.

## 6. Acceptance

`gsd-verify-work N` — on the phase branch, before the PR. Use the feature as a user: build
a part, read the warnings, and if geometry or numbers changed, measure. For a mating pair
that means printing the bolt and the nut and threading them by hand (PAIR-05) — a kernel
`proven` is necessary, not sufficient. If it does not add up, go back to the discussion;
do not patch blind.

Also before the PR: `gsd-secure-phase N` (writes `SECURITY.md`; ship refuses without it)
and `gsd-validate-phase N`.

## 7. PR

```sh
/gsd-ship N
```

Checks the verification, a clean tree and that you are not on `main`; pushes the phase
branch; opens the "Phase N: …" PR into `main`. CI runs on the PR itself — green CI before
the merge, not after.

## 8. Code review by the *other* CLI

Claude wrote it → **Codex** reviews; Codex wrote it → **Claude** reviews. Both CLIs read
the same `AGENTS.md`, so the rules are shared and the eyes are different. The object of
review is the PR (`gh pr diff N`, or `gh pr checkout N` for the second CLI).

Real findings become commits on the phase branch, `make verify`, `git push`; the PR
updates itself.

## 9. Land

Squash only, only with green CI and the review findings closed:

```sh
gh pr merge N --squash --delete-branch
```

Red CI or open findings — no merge. Work merged by hand that skipped review and verify is
exactly the hole all of this exists to close. Once there are a few phases on `main`, put
up the wall from `docs/ideas/2026-10-05-wall-main-like-spur.md`.

## Parallel loops

gsd phases go one at a time: each is cut from the already-merged `main`. What parallelises
is work outside phases — `gsd-quick`, point fixes: `make worktree.new SLUG=<slug>` (branch
`agent/<slug>` in `.claude/worktrees/<slug>`) and
`make worktree.land SLUG=<slug> MSG="<commit>"`, which checks cleanliness, squash-merges,
runs `make verify` once more on the merged result and only then commits — into the
worktree's base branch.

Judge dependencies honestly — two loops editing the same module will collide at landing.
Not sure two tasks are independent? Ask the agent before starting both.

## Working rules

- Never approve a plan or a result you do not understand. Ask.
- `make verify` and review by the other CLI are insurance, not ceremony. Skipping either
  is exactly how slop gets in.
- Small phases beat big ones. One at a time.
- Found a good idea or cut a corner — write the file in `docs/ideas/` or
  `docs/tech_debt/`, or it disappears with the session.
- When an agent claims something got faster or leaner, demand the number and the load.
