"""`make pr.land PR=N`: the sanctioned path onto `main` (D-05, L22).

Why this exists: PR #2 merged five minutes after `test (3.10)` failed on run
35993984796 -- nothing stopped a human or tool from clicking "merge" on a PR whose
checks were red or absent. The wall is a ruleset on `main` (D-12, supersedes D-06;
applied and read back in Plan 05-03): GitHub refuses to merge a head without green
required checks or behind `main`. This module is the sanctioned tool through that
wall, not the wall itself -- "a tool, not a wall" (docs/HOW_TO_DEVELOP.md section 8).

Which of its checks the ruleset duplicates, and why they stay anyway (flagged
assumption 8, 05-02-PLAN.md): the ruleset enforces `behind_by > 0` (its strict
up-to-date policy) and the required job set (its required status checks). This
module keeps both. Step 5 below proves a run *appeared* for the squash commit, and
`check_head` refuses a head it *saw* behind `main`; the window between that read and
`gh pr merge` rests on the ruleset's strict up-to-date policy (D-12, no bypass
actors) -- `--match-head-commit` pins the head, not the base (cli/cli
`pkg/cmd/pr/merge/merge.go`). And `required-jobs.txt` is held equal to `ci.yml` by a
test in this repository, while
the ruleset's own copy of the required-check names is not in git. The checks only
this module can make at all: the PR is open and based on `main` (a PR to another
base sits outside the ruleset, and step 5's evidence only ever exists for `main`);
a clean working tree (the local follow-up switches branches); no GitHub Actions
skip token in the squash subject or body (after D-03 that text is `main`'s commit
message, and the leak happens after the wall); the run for the squash commit
appearing at all; and the local follow-up.

Steps, in order: (1) read and parse the PR, refuse on its state/base; (2) refuse a
dirty working tree; (3) `check_head` -- refuse a behind, run-less, unfinished or
non-green head, and refuse a skip token in the checked subject/body
(`message_refusals`); (4) squash-merge with the exact subject and body just
checked; (5) poll for a run on the squash commit (~60 s,
`POLL_ATTEMPTS * POLL_INTERVAL_S`) and print its URL, or, when none is observed,
what was observed (`no_run_report`); (6) the local follow-up --
switch to the PR's base, pull, delete the local branch only when its tip equals
the merged head.

Needs network and an authenticated `gh`. Runs only as `make pr.land`; never part
of `make verify` or `make check` (like `bench`, D-16).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from scripts.skip_tokens import find_skip_tokens

# The one workflow this repository has (RESEARCH.md "Verified Live State": confirmed
# live there is no second workflow whose runs could be confused with this one's).
WORKFLOW = "ci.yml"

# Next to ci.yml (D-05): GitHub treats only .yml/.yaml files in that directory as
# workflows, so this .txt is never mistaken for one. Resolved from this module's own
# location, not the cwd -- `make pr.land` always runs from the repo root today, but
# this must not silently depend on that.
_WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"
REQUIRED_JOBS_FILE = _WORKFLOWS_DIR / "required-jobs.txt"

# D-05's own "~60 s". The observation behind the number (flagged assumption 6,
# 05-02-PLAN.md): the recent runs read via `gh api .../actions/workflows/ci.yml/runs`
# each showed the workflow run created 34-51 s after its head commit's own timestamp --
# an upper bound on GitHub's lag, because that timestamp precedes the ~42 s pre-commit
# hook and the push. The real lag from merge to run is measured at this phase's own
# merge and recorded in STATE.md.
POLL_ATTEMPTS = 12
POLL_INTERVAL_S = 5.0

# The callable every gh/git invocation goes through -- a real runner in main(), a fake
# one (a small class keyed on argv substrings) in tests/test_pr_land.py. Keeping every
# call behind one seam is what lets the decision logic (head_refusals, pr_refusals,
# message_refusals) be tested against recorded gh JSON with no network at all --
# bench/memory.py's pure-core/thin-shell split, applied to the GitHub API instead of
# Docker.
Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


@dataclass(frozen=True)
class PullRequest:
    number: int
    state: str
    base: str
    head_sha: str
    head_branch: str
    title: str
    body: str


@dataclass(frozen=True)
class WorkflowRun:
    id: int
    status: str
    conclusion: str | None
    html_url: str


# Every parser below narrows `object` with `isinstance` once, here at the boundary
# (RESEARCH.md's own pattern) -- these four small helpers raise `TypeError`, caught
# once by each parser's own `except` and re-raised as `ValueError` naming the field.
# A mismatch is always a refusal, never a default (prohibition 1).


def _as_object(value: object, what: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{what} is not a JSON object: {value!r}")
    return value


def _as_array(value: object, what: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{what} is not a JSON array: {value!r}")
    return value


def _as_int(value: object, what: str) -> int:
    """`bool` is a subtype of `int` in Python, so it is excluded explicitly rather
    than accepted by accident."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{what} is not an int: {value!r}")
    return value


def _as_str(value: object, what: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{what} is not a string: {value!r}")
    return value


def parse_pull_request(text: str) -> PullRequest:
    """Parse `gh pr view N --json number,state,baseRefName,headRefOid,headRefName,
    title,body`'s stdout."""
    try:
        data = _as_object(json.loads(text), "pr view output")
        pr = PullRequest(
            number=_as_int(data["number"], "number"),
            state=_as_str(data["state"], "state"),
            base=_as_str(data["baseRefName"], "baseRefName"),
            head_sha=_as_str(data["headRefOid"], "headRefOid"),
            head_branch=_as_str(data["headRefName"], "headRefName"),
            title=_as_str(data["title"], "title"),
            body=_as_str(data["body"], "body"),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"pr view output does not parse: {exc}") from exc
    return pr


def parse_runs(text: str) -> list[WorkflowRun]:
    """Parse the `--jq '[.workflow_runs[] | {id, status, conclusion, html_url}]'`
    array."""
    try:
        items = _as_array(json.loads(text), "runs output")
        runs: list[WorkflowRun] = []
        for entry in items:
            item = _as_object(entry, "run entry")
            conclusion = item["conclusion"]
            runs.append(
                WorkflowRun(
                    id=_as_int(item["id"], "id"),
                    status=_as_str(item["status"], "status"),
                    conclusion=None if conclusion is None else _as_str(conclusion, "conclusion"),
                    html_url=_as_str(item["html_url"], "html_url"),
                )
            )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"runs output does not parse: {exc}") from exc
    return runs


def parse_compare(text: str) -> tuple[int, int]:
    """Parse `gh api repos/{owner}/{repo}/compare/main...<sha> --jq '{ahead_by,
    behind_by}'`'s stdout into `(ahead_by, behind_by)`."""
    try:
        data = _as_object(json.loads(text), "compare output")
        result = (
            _as_int(data["ahead_by"], "ahead_by"),
            _as_int(data["behind_by"], "behind_by"),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"compare output does not parse: {exc}") from exc
    return result


def parse_jobs(text: str) -> list[dict[str, str]]:
    """Parse the `--jq '[.jobs[] | {name, status, conclusion}]'` array. Kept as plain
    dicts, not a dataclass -- only `name` and `conclusion` are read, by
    `head_refusals`."""
    try:
        items = _as_array(json.loads(text), "jobs output")
        jobs: list[dict[str, str]] = []
        for entry in items:
            item = _as_object(entry, "job entry")
            conclusion = item["conclusion"]
            jobs.append(
                {
                    "name": _as_str(item["name"], "name"),
                    "conclusion": "" if conclusion is None else _as_str(conclusion, "conclusion"),
                }
            )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"jobs output does not parse: {exc}") from exc
    return jobs


def required_jobs(path: Path = REQUIRED_JOBS_FILE) -> frozenset[str]:
    """The non-comment, non-blank lines of `path`, as a `frozenset`. A line-based
    read, not a word split -- job names carry spaces (`test (3.12)`)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    stripped = (line.strip() for line in lines)
    return frozenset(line for line in stripped if line and not line.startswith("#"))


def newest_run(runs: list[WorkflowRun]) -> WorkflowRun | None:
    """The run with the highest `id`, or `None` -- whatever order the API returns,
    the newest run decides (the ordering rule, must_haves truth 5)."""
    if not runs:
        return None
    return max(runs, key=lambda run: run.id)


def squash_subject(pr: PullRequest) -> str:
    """GitHub's own `PR_TITLE` default shape (D-03): `{title} (#{number})`."""
    return f"{pr.title} (#{pr.number})"


def pr_refusals(pr: PullRequest) -> list[str]:
    """A refusal when the PR is not OPEN (name the state) or its base is not `main`
    (name the base) -- step 5's evidence only ever exists for `main`."""
    refusals: list[str] = []
    if pr.state != "OPEN":
        refusals.append(f"pr.land: PR #{pr.number} is {pr.state}, not OPEN.")
    if pr.base != "main":
        refusals.append(f"pr.land: PR #{pr.number}'s base is {pr.base!r}, not main.")
    return refusals


def message_refusals(subject: str, body: str) -> list[str]:
    """One refusal per GitHub Actions skip token `find_skip_tokens` finds in the
    squash subject and body -- the same function the commit-msg hook uses
    (`scripts.skip_tokens`), so the two checks cannot drift apart (flagged
    assumption 2). This checks the text that becomes `main`'s commit message (D-03);
    no commit-msg hook ever sees a squash commit. Searches the whole subject and body,
    with no cut: GitHub writes them into the squash commit verbatim, with no git cleanup
    mode applied at all, so git's `commit -v` cut line means nothing here -- a body
    hiding a token below a line identical to that cut line used to pass unrefused
    (CR-01, 05-VERIFICATION.md)."""
    tokens = find_skip_tokens(subject + "\n\n" + body)
    return [
        f"pr.land: the squash message carries a GitHub Actions skip token: {token!r}. "
        "Edit the PR title or body to describe it in words instead."
        for token in tokens
    ]


def head_refusals(
    sha: str,
    compare: tuple[int, int],
    run: WorkflowRun | None,
    jobs: list[dict[str, str]],
    required: frozenset[str],
) -> list[str]:
    """The read-only decision core `check_head` calls. `compare` is
    `(ahead_by, behind_by)`: `behind_by > 0` is refused (D-05 step 2 -- rebase,
    push, let CI run on the real tree, retry); identical to `main`
    (`ahead_by == 0 and behind_by == 0`) is refused as nothing to merge. Then: no run
    for `sha` -- refused, naming the sha; a run not `completed` -- refused as still
    running, with its URL; a completed run whose own `conclusion` is not `success` --
    refused, naming the conclusion and the run's URL (D-04: `required-jobs.txt` is
    read from the local checkout, so a job a PR adds is known to the run before it is
    known to the list -- the run's own verdict catches it even when every *listed*
    job is green); each required job missing from `jobs` or not `success` -- refused,
    naming the job and its conclusion (kept alongside the run-conclusion check: it is
    what names a *missing* job, which a green run conclusion cannot). Return a list;
    empty means go."""
    ahead_by, behind_by = compare
    refusals: list[str] = []
    if behind_by > 0:
        refusals.append(
            f"pr.land: head {sha} is {behind_by} commit(s) behind main. "
            "Rebase onto main, push, let CI run on the real tree, retry."
        )
    elif ahead_by == 0:
        refusals.append(f"pr.land: head {sha} is identical to main -- nothing to merge.")

    if run is None:
        refusals.append(f"pr.land: no {WORKFLOW} run for head {sha}.")
        return refusals
    if run.status != "completed":
        refusals.append(f"pr.land: the newest run for {sha} is still running: {run.html_url}")
        return refusals
    if run.conclusion != "success":
        refusals.append(
            f"pr.land: the newest run for {sha} concluded {run.conclusion!r}, not success: "
            f"{run.html_url}"
        )
    by_name = {job["name"]: job["conclusion"] for job in jobs}
    for name in sorted(required):
        conclusion = by_name.get(name)
        if conclusion is None:
            refusals.append(f"pr.land: required job {name!r} is missing from the run.")
        elif conclusion != "success":
            refusals.append(f"pr.land: required job {name!r} is {conclusion}, not success.")
    return refusals


def check_head(sha: str, run: Runner, required: frozenset[str]) -> list[str]:
    """The read-only half: fetch the compare against `main`, the runs for `sha`,
    pick the newest, fetch its jobs, then decide via `head_refusals`. A failed or
    unparseable read is itself a refusal, never a default value (prohibition 1)."""
    compare_result = run(
        [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/compare/main...{sha}",
            "--jq",
            "{ahead_by, behind_by}",
        ]
    )
    if compare_result.returncode != 0:
        return [f"pr.land: reading compare for {sha} failed: {compare_result.stderr.strip()}"]
    try:
        compare = parse_compare(compare_result.stdout)
    except ValueError as exc:
        return [f"pr.land: {exc}"]

    runs_result = run(
        [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/actions/workflows/{WORKFLOW}/runs"
            f"?head_sha={sha}&per_page=100",
            "--jq",
            "[.workflow_runs[] | {id, status, conclusion, html_url}]",
        ]
    )
    if runs_result.returncode != 0:
        return [f"pr.land: reading runs for {sha} failed: {runs_result.stderr.strip()}"]
    try:
        runs = parse_runs(runs_result.stdout)
    except ValueError as exc:
        return [f"pr.land: {exc}"]

    newest = newest_run(runs)
    jobs: list[dict[str, str]] = []
    if newest is not None and newest.status == "completed":
        jobs_result = run(
            [
                "gh",
                "api",
                f"repos/{{owner}}/{{repo}}/actions/runs/{newest.id}/jobs?per_page=100",
                "--jq",
                "[.jobs[] | {name, status, conclusion}]",
            ]
        )
        if jobs_result.returncode != 0:
            return [
                f"pr.land: reading jobs for run {newest.id} failed: "
                f"{jobs_result.stderr.strip()}"
            ]
        try:
            jobs = parse_jobs(jobs_result.stdout)
        except ValueError as exc:
            return [f"pr.land: {exc}"]

    return head_refusals(sha, compare, newest, jobs, required)


def no_run_report(
    pr_number: int,
    squash_sha: str,
    waited_s: float,
    last_error: str | None,
    run: Runner,
) -> str:
    """What `land`'s step 5 prints when no {WORKFLOW} run appeared for the squash
    commit within the poll window (D-06): one read of the squash commit's own
    message, then exactly one of three endings -- never a cause this function did
    not itself read. Precedence (flagged assumption 1, 06-04-PLAN.md): a token found
    in the message is reported first -- it is the one cause the tool can establish,
    and a token means GitHub will never start a run whatever the polls saw.
    Otherwise, a failed commit read or the poll's own last error gives the
    last-error report (`last_error` already holds the most recent failed poll read,
    cleared by a successful one -- see `land`'s poll loop). Otherwise, the
    nothing-appeared report naming the Actions link, derived from the commit's own
    `html_url` (`.../commit/<sha>` -> `.../actions/workflows/<workflow>`) so no
    repository name is hard-coded here."""
    prefix = (
        f"pr.land: PR #{pr_number} IS merged as {squash_sha}, but no {WORKFLOW} run "
        f"observed within {waited_s:.0f} s"
    )
    commit_result = run(
        [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/commits/{squash_sha}",
            "--jq",
            ".html_url, .commit.message",
        ]
    )
    if commit_result.returncode != 0:
        error = f"reading the squash commit failed: {commit_result.stderr.strip()}"
        return f"{prefix}; last error: {error}"

    first_line, _, message = commit_result.stdout.partition("\n")
    tokens = find_skip_tokens(message)
    if tokens:
        named = ", ".join(repr(token) for token in tokens)
        return f"{prefix}: {named} in the squash commit's message -- a regression of L22."
    if last_error is not None:
        return f"{prefix}; last error: {last_error}"
    repo = first_line.split("/commit/", 1)[0]
    return f"{prefix}. Check {repo}/actions/workflows/{WORKFLOW}."


def land(
    pr_number: int,
    run: Runner,
    *,
    attempts: int = POLL_ATTEMPTS,
    interval_s: float = POLL_INTERVAL_S,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Land PR `pr_number`, in the order the module docstring lists. Every gh/git
    call goes through `run`. Titles, bodies and branch names travel only as separate
    argv elements, never through a shell (T-05-08)."""
    pr_result = run(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "number,state,baseRefName,headRefOid,headRefName,title,body",
        ]
    )
    if pr_result.returncode != 0:
        print(f"pr.land: reading PR #{pr_number} failed: {pr_result.stderr.strip()}")
        print("pr.land: nothing was merged.")
        return 1
    try:
        pr = parse_pull_request(pr_result.stdout)
    except ValueError as exc:
        print(f"pr.land: {exc}")
        print("pr.land: nothing was merged.")
        return 1

    refusals = pr_refusals(pr)
    if refusals:
        for line in refusals:
            print(line)
        print("pr.land: nothing was merged.")
        return 1

    for dirty_check in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        dirty_result = run(dirty_check)
        if dirty_result.returncode != 0:
            print("pr.land: the working tree has uncommitted changes.")
            print("pr.land: nothing was merged.")
            return 1

    subject = squash_subject(pr)
    refusals = check_head(pr.head_sha, run, required_jobs())
    refusals += message_refusals(subject, pr.body)
    if refusals:
        for line in refusals:
            print(line)
        print("pr.land: nothing was merged.")
        return 1

    merge_result = run(
        [
            "gh",
            "pr",
            "merge",
            str(pr_number),
            "--squash",
            "--match-head-commit",
            pr.head_sha,
            "--subject",
            subject,
            "--body",
            pr.body,
        ]
    )
    if merge_result.returncode != 0:
        print(f"pr.land: gh pr merge failed: {merge_result.stderr.strip()}")
        print(f"pr.land: check `gh pr view {pr_number}` before retrying.")
        return 1

    squash_sha_result = run(
        ["gh", "pr", "view", str(pr_number), "--json", "mergeCommit", "--jq", ".mergeCommit.oid"]
    )
    if squash_sha_result.returncode != 0:
        print(
            f"pr.land: PR #{pr_number} IS merged, but reading the squash commit "
            f"failed: {squash_sha_result.stderr.strip()}"
        )
        return 1
    squash_sha = squash_sha_result.stdout.strip()

    found_run: WorkflowRun | None = None
    last_error: str | None = None
    for attempt in range(attempts):
        poll_result = run(
            [
                "gh",
                "api",
                f"repos/{{owner}}/{{repo}}/actions/workflows/{WORKFLOW}/runs"
                f"?head_sha={squash_sha}&per_page=100",
                "--jq",
                "[.workflow_runs[] | {id, status, conclusion, html_url}]",
            ]
        )
        if poll_result.returncode != 0:
            last_error = poll_result.stderr.strip()
        else:
            try:
                found_run = newest_run(parse_runs(poll_result.stdout))
            except ValueError as exc:
                last_error = str(exc)
            else:
                last_error = None
                if found_run is not None:
                    print(found_run.html_url)
                    break
        if attempt < attempts - 1:
            sleep(interval_s)

    step6_failed = False
    switch_result = run(["git", "switch", pr.base])
    if switch_result.returncode != 0:
        print(f"pr.land: git switch {pr.base} failed: {switch_result.stderr.strip()}")
        step6_failed = True
    else:
        pull_result = run(["git", "pull", "--ff-only", "origin", pr.base])
        if pull_result.returncode != 0:
            print(
                f"pr.land: git pull --ff-only origin {pr.base} failed: "
                f"{pull_result.stderr.strip()}"
            )
            step6_failed = True
        else:
            verify_result = run(
                ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{pr.head_branch}"]
            )
            if verify_result.returncode == 0:
                local_tip = verify_result.stdout.strip()
                if local_tip == pr.head_sha:
                    branch_result = run(["git", "branch", "-D", pr.head_branch])
                    if branch_result.returncode != 0:
                        print(
                            f"pr.land: git branch -D {pr.head_branch} failed: "
                            f"{branch_result.stderr.strip()}"
                        )
                        step6_failed = True
                else:
                    print(
                        f"pr.land: local branch {pr.head_branch} tip {local_tip} "
                        f"differs from the merged head {pr.head_sha}; keeping it."
                    )
            # An absent local branch (verify_result.returncode != 0) is skipped
            # quietly -- nothing to clean up, and it is not an error.

    if found_run is not None and not step6_failed:
        return 0
    if found_run is None:
        print(no_run_report(pr_number, squash_sha, attempts * interval_s, last_error, run))
    return 1


def _real_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, check=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts.pr_land",
        description="Squash-merge a PR only if its head is green and current with main.",
    )
    parser.add_argument("pr", type=int, help="PR number")
    args = parser.parse_args(argv)
    return land(args.pr, _real_runner)


if __name__ == "__main__":
    raise SystemExit(main())
