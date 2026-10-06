# How to develop screw (the human's guide)

The loop this repository is worked in with AI agents, and your role at each step. screw is
spur's sibling and runs the same loop. `main` is walled the way spur's is (`L08`): the code
is in the repo, the ruleset is applied once after the Phase 1 merge (§9).

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
  places. The same install adds a commit-msg hook that refuses GitHub Actions skip tokens
  in a commit message (`L08`); a clone that installed before it re-runs
  `.venv/bin/pre-commit install` once to pick it up.
- `make pr.land PR=N` — the sanctioned way onto `main`: squash-merges a PR only if its
  head is green and current with `main` (§9, `L08`).
- `requirements.txt` — the runtime closure the image installs, resolved in linux/amd64
  by `make lock` (Docker); every install is constrained to it (`L07`). The dev tools (ruff,
  mypy, pytest, ...) float (`L08`).
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

The ship-note commit carries a GitHub Actions skip token in its subject, and the
`no-skip-token` hook refuses it: `gsd-ship` prints a warning and leaves
`.planning/STATE.md` modified but uncommitted. Commit it by hand, without the token —
`docs(NN): ship phase N — PR #M` — then `git push`. The push starts one more CI run on
the new PR head, the one `make pr.land` requires. The global
`~/.claude/gsd-core/workflows/ship.md` is not patched: the edit would be lost at the next
gsd update and is invisible to this repository.

The hook reads the message whole, together with the diff that `git commit -v` appends
below the cut line: if that diff names a skip token, the commit is refused — commit
without `-v` or rephrase.

## 8. Code review by the *other* CLI

Claude wrote it → **Codex** reviews; Codex wrote it → **Claude** reviews. Both CLIs read
the same `AGENTS.md`, so the rules are shared and the eyes are different. The object of
review is the PR (`gh pr diff N`, or `gh pr checkout N` for the second CLI).

Real findings become commits on the phase branch, `make verify`, `git push`; the PR
updates itself.

## 9. Land

A phase reaches `main` through `make pr.land PR=N` (`L08`), from an up-to-date `main`:

```sh
git switch main && git pull --ff-only
make pr.land PR=N
```

Run it from an up-to-date checkout: the list of required jobs is read from the local
`.github/workflows/required-jobs.txt`, and the tool leaves you on `main` at the end anyway.

In order, it: reads the PR's current head; refuses if the PR is not `OPEN` or is not based
on `main`; refuses on a dirty tree; refuses if the head is behind `main` (then rebase,
push, wait for the CI run on the real tree and retry) or equal to it; refuses if the head
has no completed green `ci.yml` run for every job in `required-jobs.txt`, or if the run
itself did not finish `success`; refuses if the PR title or body carries a skip token
(that text becomes `main`'s commit message). Then it squash-merges exactly the verified
head with exactly the verified title and body, waits up to a minute for the CI run on the
new `main` commit and prints its URL, switches to `main`, pulls, and deletes the local
phase branch only if its tip is the landed commit. Any refusal means nothing was landed.

`make pr.land` is a tool, not a wall: it checks the job list and the lag behind `main` at
the moment of its read, and the window between that read and the merge is closed by the
ruleset's strict up-to-date policy. The button on GitHub merges only what the ruleset
accepts but skips the tool's other checks, so it is not the way.

Red CI or open review findings — no merge. Work landed by hand that skipped review and
verify is exactly the hole all of this exists to close.

**Phase 1 lands before the wall.** The ruleset requires `vendor-bundle` and `image`, which
exist only on the phase branch until it merges, so Phase 1 itself merges the old way, with
green CI and the review findings closed:

```sh
gh pr merge N --squash --delete-branch
```

### Put up the wall (once, after the Phase 1 merge)

Repository settings are not in git; this section is their only record. The first command
makes the squash commit carry the PR title and body (the curated text `gsd-ship`
assembles) instead of the branch's concatenated commit subjects, which is how a skip token
reached spur's `main` twice. The second creates the ruleset `default` on `main`: no bypass
actors, no deletion, no force push, a pull request for every change, and the three jobs of
`required-jobs.txt` green from GitHub Actions on a head not behind `main`. The third reads
the wall back; its check names must equal `required-jobs.txt`.

```sh
gh api -X PATCH repos/halfb00t/screw -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY

gh api -X POST repos/halfb00t/screw/rulesets --input - <<'JSON'
{"name":"default","target":"branch","enforcement":"active","bypass_actors":[],
 "conditions":{"ref_name":{"include":["refs/heads/main"],"exclude":[]}},
 "rules":[{"type":"deletion"},{"type":"non_fast_forward"},
  {"type":"pull_request","parameters":{"required_approving_review_count":0,"dismiss_stale_reviews_on_push":false,
   "required_reviewers":[],"require_code_owner_review":false,"require_last_push_approval":false,
   "required_review_thread_resolution":false,"require_extra_approval_for_unattributed_changes":true,
   "allowed_merge_methods":["merge","squash","rebase"]}},
  {"type":"required_status_checks","parameters":{"strict_required_status_checks_policy":true,"do_not_enforce_on_create":false,
   "required_status_checks":[{"context":"test (3.12)","integration_id":15368},{"context":"vendor-bundle","integration_id":15368},{"context":"image","integration_id":15368}]}}]}
JSON

gh api repos/halfb00t/screw/rules/branches/main
```

`integration_id` 15368 is GitHub Actions, so a same-named status from anywhere else cannot
satisfy the rule. The POST body is copied from spur's live ruleset and has not been run
against screw: if GitHub rejects it, or the read-back differs, fix this block. Plan 01-10
records the ruleset id here and swaps the POST for a PUT by id, which is how a later change
to `required-jobs.txt` is applied (the PUT replaces the required-checks rule whole). The
names in the list are the ones GitHub shows — `jobs.<id>.name` if set, otherwise the id,
plus the matrix value (`test (3.12)`); the drift test in `tests/test_pr_land.py` derives
them from `ci.yml` and compares.

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
