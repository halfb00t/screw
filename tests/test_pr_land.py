"""Tests for `scripts.pr_land` -- the whole `make pr.land PR=N` path, offline, against
recorded `gh` JSON.

Run as `.venv/bin/python -m pytest tests/test_pr_land.py -q` **from the repository
root** -- the `-m` form puts the repo root on `sys.path`, the same constraint
`tests/test_bench.py` and `tests/test_skip_tokens.py` document for `bench` and
`scripts`.

Every literal fixture below traces to a real, read-only `gh`/`gh api` call made against
this repository on 2026-09-25 (RESEARCH.md's "Verified Live State", or a call made
directly during this plan's own execution) -- a comment above each names the call.
Per-case variants change **values** (state, a PR number, conclusions, ids), never
**shape**. Every test except the drift test (`test_required_jobs_file_matches_ci_yml_job_names`)
is independent of `.github/workflows/required-jobs.txt`'s current contents: pure tests
pass `required`/`REQUIRED` explicitly, and `land()` tests see `required_jobs()` return
`REQUIRED` (`test (3.12)`, `vendor-bundle` and `image`), the jobs the recorded runs carry.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts.pr_land import (
    FULL_TIER_PATHS,
    FULL_TIER_RUN_NAME,
    FULL_TIER_WORKFLOW,
    GATE_FLAG,
    GATE_PATHS,
    WORKFLOW,
    PullRequest,
    WorkflowRun,
    check_full_tier,
    check_head,
    full_tier_path,
    full_tier_refusals,
    gate_refusals,
    head_refusals,
    land,
    message_refusals,
    newest_run,
    no_run_report,
    parse_changed_files,
    parse_compare,
    parse_jobs,
    parse_pull_request,
    parse_runs,
    pr_refusals,
    required_jobs,
    squash_subject,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def cp(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    """A `subprocess.CompletedProcess` stand-in, `args` unused by anything under test."""
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class FakeRunner:
    """Answers `gh`/`git` calls from handlers registered with `.on(substring, ...)`,
    matched by substring against the joined argv, first-registered-first-matched.
    Records every argv it was called with. A handler may carry more than one response
    -- each call pops the next one, and the last response repeats once the queue is
    exhausted (the poll test's "no run, then a run" shape)."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self._handlers: list[tuple[str, list[subprocess.CompletedProcess[str]]]] = []

    def on(self, substring: str, *responses: subprocess.CompletedProcess[str]) -> FakeRunner:
        self._handlers.append((substring, list(responses)))
        return self

    def replace(self, substring: str, *responses: subprocess.CompletedProcess[str]) -> FakeRunner:
        """Swap the queue for every handler whose registered substring starts with
        `substring` -- used by the poll-timeout/local-follow-up variant tests to
        override one leg of `_happy_runner()` without rebuilding the whole thing."""
        self._handlers = [
            (sub, list(responses)) if sub.startswith(substring) else (sub, resp)
            for sub, resp in self._handlers
        ]
        return self

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        joined = " ".join(argv)
        for substring, responses in self._handlers:
            if substring in joined:
                if len(responses) > 1:
                    return responses.pop(0)
                return responses[0]
        raise AssertionError(f"FakeRunner: no handler registered for {argv!r}")


# --- recorded shapes -----------------------------------------------------------------
# `gh pr view 3 --json number,state,baseRefName,headRefOid,headRefName,title,body`
# (2026-09-25). PR #3's real state is MERGED; the OPEN variants below change only
# `state` and `number` for the happy-path/refusal tests -- same shape, not literally
# recorded as OPEN (PR #3 itself was already merged by the time this plan ran).
PR3_HEAD_SHA = "2c4b544c63ff2f4b27e7554efa380fdebfbeb6ae"
PR3_VIEW_JSON = (
    '{"number":3,"state":"MERGED","baseRefName":"main",'
    f'"headRefOid":"{PR3_HEAD_SHA}",'
    '"headRefName":"gsd/phase-04-typed-derived-dimensions-contract",'
    '"title":"Phase 4: Typed Derived-Dimensions Contract",'
    '"body":"## Summary\\n\\nTyped DerivedDimensions contract.\\n"}'
)

# `gh api repos/halfb00t/spur/actions/workflows/ci.yml/runs?head_sha=2c4b544...`
# (2026-09-25): one completed, successful run.
PR3_RUNS_JSON = (
    '[{"id":36088409707,"status":"completed","conclusion":"success",'
    '"html_url":"https://github.com/halfb00t/spur/actions/runs/36088409707"}]'
)

# `gh api repos/halfb00t/spur/actions/runs/36088409707/jobs` (2026-09-25): all four
# jobs, all `success`.
PR3_JOBS_JSON = (
    '[{"name":"vendor-bundle","status":"completed","conclusion":"success"},'
    '{"name":"image","status":"completed","conclusion":"success"},'
    '{"name":"test (3.12)","status":"completed","conclusion":"success"},'
    '{"name":"test (3.10)","status":"completed","conclusion":"success"}]'
)

# `gh api repos/halfb00t/spur/compare/main...2c4b544...` (2026-09-25, this plan's own
# execution): PR #3's real head sits one commit behind main (`ahead_by: 32,
# behind_by: 1`) -- the live probe in this plan's `<verify>` block re-reads this.
PR3_COMPARE_JSON = '{"ahead_by":32,"behind_by":1}'

# A synthetic "current, ahead" compare, used only for the happy-path fixtures below
# (a synthetic OPEN PR, not literally PR #3's real state) -- same shape as
# PR3_COMPARE_JSON, different values.
CURRENT_COMPARE_JSON = '{"ahead_by":3,"behind_by":0}'

# `gh api repos/halfb00t/spur/actions/runs/35993984796/jobs` (RESEARCH.md, PR #2's
# last real run): `test (3.10)` failed, the other three succeeded.
RED_RUN_JOBS_JSON = (
    '[{"name":"vendor-bundle","status":"completed","conclusion":"success"},'
    '{"name":"image","status":"completed","conclusion":"success"},'
    '{"name":"test (3.10)","status":"completed","conclusion":"failure"},'
    '{"name":"test (3.12)","status":"completed","conclusion":"success"}]'
)

# `gh api repos/halfb00t/spur/actions/workflows/ci.yml/runs?head_sha=73535a2...`
# (2026-09-25, this plan's own execution): a completed run whose own conclusion is
# `failure` -- `test (3.12)` failed, `vendor-bundle` and `image` green (a Phase 5 PR
# head, D-04's live case: a run can fail on a job `required-jobs.txt` names, even
# while every job the run *itself* names is a separate question from that list).
RUN_36116930241_HEAD_SHA = "73535a24ce57258f23049d72e8c99eb1d5c0ba90"
RUN_36116930241_RUNS_JSON = (
    '[{"conclusion":"failure",'
    '"html_url":"https://github.com/halfb00t/spur/actions/runs/36116930241",'
    '"id":36116930241,"status":"completed"}]'
)

# `gh api repos/halfb00t/spur/actions/runs/36116930241/jobs?per_page=100`
# (2026-09-25, this plan's own execution).
RUN_36116930241_JOBS_JSON = (
    '[{"conclusion":"failure","name":"test (3.12)","status":"completed"},'
    '{"conclusion":"success","name":"vendor-bundle","status":"completed"},'
    '{"conclusion":"success","name":"image","status":"completed"}]'
)

# `gh pr view 2 --json ...statusCheckRollup...` (RESEARCH.md "Verified Live State"):
# a MERGED PR whose head carried a skip token -- zero recorded checks, not a red run.
PR2_HEAD_SHA = "20b63e453a3cd0c72e5d0f995a107a238c652a90"
PR2_VIEW_JSON = (
    '{"number":2,"state":"MERGED","baseRefName":"main",'
    f'"headRefOid":"{PR2_HEAD_SHA}",'
    '"headRefName":"gsd/phase-03-structured-logging",'
    '"title":"Phase 3: Structured Logging","body":"ship phase 3 [ci skip]"}'
)

# `gh api repos/halfb00t/spur/actions/workflows/ci.yml/runs?head_sha=20b63e4...`
# (2026-09-25, this plan's own execution): zero runs -- the skip token on PR #2's own
# head suppressed the run entirely, not a red run (RESEARCH.md's own "PR #2's own
# recorded shape" -- `statusCheckRollup: []`).
PR2_RUNS_JSON = "[]"

# `gh api repos/{owner}/{repo}/commits/b72b0e1f1e31e06b9dd8bef964725b11f30e0c51
# --jq '.html_url, .commit.message'` (2026-09-25, this plan's own execution) --
# values changed to `deadbeef1234` and PR #3's own recorded title/body, shape kept:
# the first line is the commit's `html_url`, then its message (subject, blank line,
# body) verbatim.
SQUASH_COMMIT_READ = (
    "https://github.com/halfb00t/spur/commit/deadbeef1234\n"
    "Phase 4: Typed Derived-Dimensions Contract (#3)\n"
    "\n"
    "## Summary\n"
    "\n"
    "Typed DerivedDimensions contract.\n"
)

# `gh api 'repos/{owner}/{repo}/pulls/22/files' --paginate --jq '.[].filename'` (2026-10-31,
# plan 07-19): PR A, the phase 7 harness and pre-registration, which touched no FULL_TIER_PATHS
# path. The variants below change the paths, never the shape: one path per line.
PR_A_FILES = (
    ".github/workflows/operability.yml\n"
    ".planning/phases/07-operability-re-sweep/07-SWEEP-PROTOCOL.md\n"
    "Makefile\n"
    "bench/__init__.py\n"
    "bench/oper.py\n"
    "bench/oper_child.py\n"
    "bench/oper_lift.py\n"
    "bench/oper_sets.py\n"
    "bench/points/controls.json\n"
    "bench/points/explore.json\n"
    "bench/points/spread.json\n"
    "bench/points/tracer.json\n"
    "bench/points/walls.json\n"
    "docs/tech_debt/active/2026-10-10-spike-protocol-amendments-before-next-campaign.md\n"
    "docs/tech_debt/active/2026-10-14-m18-probe-one-entry-has-no-deadline-during-a-run.md\n"
    "pyproject.toml\n"
    "tests/test_oper.py\n"
)
# PR A's paths less the GATE_PATHS files it touched, which the L28 rule now refuses on their own:
# the fixture for every test that is about something else.
PR_A_FILES_NO_GATE = "".join(line for line in PR_A_FILES.splitlines(keepends=True)
                             if line.strip() not in GATE_PATHS)

# `gh api 'repos/{owner}/{repo}/actions/workflows/operability.yml/runs?head_sha=<sha>&per_page=100'
# --jq '[.workflow_runs[] | select(.display_title == "operability: full") | {id, status,
# conclusion, html_url}]'` (2026-10-31, plan 07-19). For a142c27, the 07-05 tracer's head, it
# is `[]`: that head's one operability run (40645463872, success) is "operability: tracer",
# not the full tier. For b0186b9 it is the first full run, still queued when read.
TRACER_HEAD_SHA = "a142c278f8bba48df8a2405ec7e092d42b725421"
TRACER_FULL_RUNS_JSON = "[]"
FULL_QUEUED_RUNS_JSON = (
    '[{"conclusion":null,"html_url":"https://github.com/halfb00t/screw/actions/runs/41155746591",'
    '"id":41155746591,"status":"queued"}]'
)

REQUIRED = frozenset({"test (3.12)", "vendor-bundle", "image"})
# The required tier's shard jobs (07-18, G34), as GitHub reports a matrix job: 4 since the
# fine-pitch wall dropped the points it refuses (G36).
BOUNDS_SHARDS = ("bounds (1)", "bounds (2)", "bounds (3)", "bounds (4)")


@pytest.fixture(autouse=True)
def _land_requires_the_recorded_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """`land()` reads `required_jobs()` itself, so it is held to REQUIRED, the jobs the recorded
    runs carry: the required list has grown since (07-18's `bounds`), and a recorded run cannot.
    The tests that read the file import `required_jobs` by name and are not affected."""
    monkeypatch.setattr("scripts.pr_land.required_jobs", lambda: REQUIRED)

# A compare result that is neither behind nor identical -- the neutral value the Task 1
# tests use for `head_refusals`, which now requires a `compare` argument as of Task 2.
NOT_BEHIND = (1, 0)

# The verifier's reproduction (05-VERIFICATION.md "Independent Assessment of Code Review
# CR-01"): a clean description, then a line identical to git's `commit -v` cut line, then
# a skip token. GitHub writes a PR body into the squash commit verbatim -- there is no
# git cleanup step to discard anything below this line for `pr.land`'s text, unlike a
# real `git commit -v` buffer (05-06-PLAN.md Decision (a)).
CUT_LINE_BODY = (
    "A normal PR description.\n"
    "\n"
    "# ------------------------ >8 ------------------------\n"
    "[skip ci]\n"
)


# --- required_jobs() -------------------------------------------------------------


def test_required_jobs_reads_non_comment_non_blank_lines(tmp_path: Path) -> None:
    """`#` lines, blank lines and names with spaces (`test (3.12)`) -- the exact
    shape `.github/workflows/required-jobs.txt` uses."""
    path = tmp_path / "required-jobs.txt"
    path.write_text(
        "# a header comment\n\ntest (3.12)\nvendor-bundle\n\n# another comment\nimage\n",
        encoding="utf-8",
    )
    assert required_jobs(path) == frozenset({"test (3.12)", "vendor-bundle", "image"})


def _effective_job_names(ci_yml: str) -> set[str]:
    """The job names GitHub actually reports (D-05): `jobs.<id>.name` when a job sets
    one, else the id -- a rename under `image:` moves this set even though the id
    stays `image`. Job ids are the two-space-indented keys directly under `jobs:`,
    found with their match positions so each job's own block can be scoped: from the
    end of its id line to the start of the next id line (or the end of the section).
    Only a `^    name:` line -- exactly four spaces, one level under the id -- inside
    that block gives the effective name; step `name:` keys sit at six-or-more spaces
    under `steps:` and are never read (`ci.yml`'s own two, `bundle matches web/` and
    `the packaged entrypoint serves a gear`, confirm the depth). A job with a one-key
    matrix list -- `test`'s `python: [...]`, `bounds`' `shard: [...]` -- expands to
    `f"{name} ({v})"` for each value, using its own effective name: `test (3.12)` while
    `test` carries no `name:`."""
    jobs_section = ci_yml.split("\njobs:\n", 1)[1]
    id_matches = list(re.finditer(r"^  ([a-zA-Z][\w-]*):\s*$", jobs_section, re.MULTILINE))
    job_ids = [m.group(1) for m in id_matches]
    assert "test" in job_ids


    effective: dict[str, str] = {}
    for i, match in enumerate(id_matches):
        job_id = match.group(1)
        block_start = match.end()
        block_end = id_matches[i + 1].start() if i + 1 < len(id_matches) else len(jobs_section)
        block = jobs_section[block_start:block_end]
        name_match = re.search(r"^    name:\s*(.+?)\s*$", block, re.MULTILINE)
        if name_match is None:
            effective[job_id] = job_id
            continue
        value = name_match.group(1)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        effective[job_id] = value

    names: set[str] = set()
    for i, name in enumerate(effective.values()):
        block_end = id_matches[i + 1].start() if i + 1 < len(id_matches) else len(jobs_section)
        block = jobs_section[id_matches[i].end():block_end]
        # GitHub reports a one-key matrix job as `<name> (<value>)` per value: `test`'s python
        # list and `bounds`' shard list (07-18, G34).
        matrix = re.search(r"^      matrix:\n        \w+:\s*\[([^\]]*)\]", block, re.MULTILINE)
        if matrix is None:
            names.add(name)
            continue
        values = [v.strip().strip('"') for v in matrix.group(1).split(",")]
        names.update(f"{name} ({v})" for v in values)
    return names


def test_required_jobs_file_matches_ci_yml_job_names() -> None:
    """D-05: `required_jobs()` must equal the job names GitHub actually reports --
    `jobs.<id>.name` when set, else the id -- or a PR could be judged green on a job
    GitHub never runs (or judged red on a name it no longer reports)."""
    ci_yml = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert required_jobs() == frozenset(_effective_job_names(ci_yml))


def test_a_job_name_override_moves_the_derived_required_set() -> None:
    """The rename the debt file describes
    (2026-09-25-required-jobs-drift-test-ignores-job-name-overrides.md), which the
    id-based test passed: a `name:` override under `image:` moves the derived set
    even though `required-jobs.txt` still says `image`, and the step `name:` keys
    are never mistaken for it."""
    ci_yml = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    renamed = ci_yml.replace("  image:\n", "  image:\n    name: renamed-image\n", 1)
    assert renamed != ci_yml
    names = _effective_job_names(renamed)
    assert names == {"test (3.12)", "vendor-bundle", "renamed-image", *BOUNDS_SHARDS}
    assert "bundle matches web/" not in names
    assert "the packaged entrypoint serves a gear" not in names

    quoted = ci_yml.replace("  image:\n", '  image:\n    name: "renamed image"\n', 1)
    assert quoted != ci_yml
    assert _effective_job_names(quoted) == {"test (3.12)", "vendor-bundle", "renamed image",
                                            *BOUNDS_SHARDS}


# --- pure decisions ----------------------------------------------------------------


def test_squash_subject_is_title_and_pr_number() -> None:
    pr = parse_pull_request(PR3_VIEW_JSON)
    assert squash_subject(pr) == "Phase 4: Typed Derived-Dimensions Contract (#3)"


def test_pr_refusals_empty_for_an_open_pr_based_on_main() -> None:
    pr = PullRequest(
        number=99, state="OPEN", base="main", head_sha="abc123",
        head_branch="gsd/phase-99", title="t", body="b",
    )
    assert pr_refusals(pr) == []


def test_pr_refusals_names_the_state_for_a_merged_pr() -> None:
    pr = parse_pull_request(PR2_VIEW_JSON)
    refusals = pr_refusals(pr)
    assert len(refusals) == 1
    assert "MERGED" in refusals[0]


def test_pr_refusals_names_the_base_for_a_pr_not_targeting_main() -> None:
    pr = PullRequest(
        number=5, state="OPEN", base="develop", head_sha="abc",
        head_branch="feature/x", title="t", body="b",
    )
    refusals = pr_refusals(pr)
    assert len(refusals) == 1
    assert "develop" in refusals[0]


def test_newest_run_picks_the_highest_id_regardless_of_order() -> None:
    older = WorkflowRun(id=1, status="completed", conclusion="failure", html_url="u1")
    newer = WorkflowRun(id=2, status="completed", conclusion="success", html_url="u2")
    assert newest_run([older, newer]) is newer
    assert newest_run([newer, older]) is newer


def test_newest_run_of_empty_list_is_none() -> None:
    assert newest_run([]) is None


def test_head_refusals_empty_when_every_required_job_succeeded() -> None:
    run = newest_run(parse_runs(PR3_RUNS_JSON))
    jobs = parse_jobs(PR3_JOBS_JSON)
    assert head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, jobs, REQUIRED) == []


def test_head_refusals_no_run_names_the_sha() -> None:
    refusals = head_refusals(PR3_HEAD_SHA, NOT_BEHIND, None, [], REQUIRED)
    assert len(refusals) == 1
    assert PR3_HEAD_SHA in refusals[0]


def test_head_refusals_run_in_progress_names_still_running_and_url() -> None:
    run = WorkflowRun(id=1, status="in_progress", conclusion=None, html_url="https://x/1")
    refusals = head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, [], REQUIRED)
    assert len(refusals) == 1
    assert "still running" in refusals[0]
    assert "https://x/1" in refusals[0]


def test_head_refusals_empty_jobs_list_reports_every_required_job_missing() -> None:
    """PR #2's own recorded shape: `statusCheckRollup: []` -- zero jobs at all, not
    one failing -- must refuse the same as a red job."""
    run = WorkflowRun(id=1, status="completed", conclusion="success", html_url="u")
    refusals = head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, [], REQUIRED)
    assert len(refusals) == len(REQUIRED)
    assert all("missing" in r for r in refusals)


def test_head_refusals_one_red_job_names_it_and_its_conclusion() -> None:
    """Run 35993984796's own recorded shape: `test (3.10)` failed. `test (3.12)` is
    the job in `REQUIRED` here, so put the failure there instead -- same shape. The
    run's own conclusion is refused too now (D-04), in addition to the job -- the
    count rises by one, and exactly one line names it (`concluded`)."""
    run = WorkflowRun(id=1, status="completed", conclusion="failure", html_url="u")
    jobs = [
        {"name": "test (3.12)", "conclusion": "failure"},
        {"name": "vendor-bundle", "conclusion": "success"},
        {"name": "image", "conclusion": "success"},
    ]
    refusals = head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, jobs, REQUIRED)
    assert len(refusals) == 2
    assert any("test (3.12)" in r and "failure" in r for r in refusals)
    assert sum("concluded" in r for r in refusals) == 1


def test_head_refusals_a_failed_run_is_refused_even_when_every_listed_job_is_green() -> None:
    """The debt file's own case
    (2026-09-25-pr-land-admits-a-run-with-a-failing-unlisted-job.md): a run can fail
    on a job the local `required-jobs.txt` does not know yet -- a PR that grows the
    job set, landed from a checkout that predates it. The run's own verdict catches
    it (D-04), even with every listed job green."""
    run = WorkflowRun(
        id=36116930241,
        status="completed",
        conclusion="failure",
        html_url="https://github.com/halfb00t/spur/actions/runs/36116930241",
    )
    jobs = [{"name": name, "conclusion": "success"} for name in sorted(REQUIRED)] + [
        {"name": "lint", "conclusion": "failure"}
    ]
    refusals = head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, jobs, REQUIRED)
    assert len(refusals) == 1
    assert "failure" in refusals[0]
    assert "actions/runs/36116930241" in refusals[0]


def test_head_refusals_matches_the_recorded_red_run_verbatim() -> None:
    """The literal shape run 35993984796 returned, unmodified -- a required set that
    includes `test (3.10)` (this task's pre-D-09 set) catches the one red job. The
    run's own conclusion is refused too now (D-04) -- the count rises by one."""
    jobs = parse_jobs(RED_RUN_JOBS_JSON)
    run = WorkflowRun(id=35993984796, status="completed", conclusion="failure", html_url="u")
    refusals = head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, jobs, REQUIRED | {"test (3.10)"})
    assert len(refusals) == 2
    assert any("test (3.10)" in r and "failure" in r for r in refusals)
    assert sum("concluded" in r for r in refusals) == 1


def test_check_head_names_the_run_conclusion_of_recorded_run_36116930241() -> None:
    """The real failed run 36116930241, through `check_head`: two refusals -- the
    run's own conclusion (with its URL) and the one listed job that failed on it."""
    runner = (
        FakeRunner()
        .on(f"compare/main...{RUN_36116930241_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        .on(f"runs?head_sha={RUN_36116930241_HEAD_SHA}", cp(0, RUN_36116930241_RUNS_JSON))
        .on("runs/36116930241/jobs", cp(0, RUN_36116930241_JOBS_JSON))
    )
    refusals = check_head(RUN_36116930241_HEAD_SHA, runner, REQUIRED)
    assert len(refusals) == 2
    assert any("actions/runs/36116930241" in r and "failure" in r for r in refusals)
    assert any("test (3.12)" in r for r in refusals)


def test_head_refusals_a_required_job_cancelled_or_skipped_is_refused() -> None:
    run = WorkflowRun(id=1, status="completed", conclusion="failure", html_url="u")
    for bad_conclusion in ("cancelled", "skipped"):
        jobs = [
            {"name": "test (3.12)", "conclusion": bad_conclusion},
            {"name": "vendor-bundle", "conclusion": "success"},
            {"name": "image", "conclusion": "success"},
        ]
        refusals = head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, jobs, REQUIRED)
        assert len(refusals) == 2
        assert any(bad_conclusion in r for r in refusals)
        assert sum("concluded" in r for r in refusals) == 1


# --- compare: behind / identical / ahead --------------------------------------------


def test_head_refusals_behind_main_names_behind_and_says_rebase() -> None:
    run = newest_run(parse_runs(PR3_RUNS_JSON))
    jobs = parse_jobs(PR3_JOBS_JSON)
    refusals = head_refusals(PR3_HEAD_SHA, (5, 2), run, jobs, REQUIRED)
    assert len(refusals) == 1
    assert "behind" in refusals[0]
    assert "rebase onto main" in refusals[0].lower()


def test_head_refusals_identical_to_main_refused_as_nothing_to_merge() -> None:
    run = newest_run(parse_runs(PR3_RUNS_JSON))
    jobs = parse_jobs(PR3_JOBS_JSON)
    refusals = head_refusals(PR3_HEAD_SHA, (0, 0), run, jobs, REQUIRED)
    assert len(refusals) == 1
    assert "nothing to merge" in refusals[0]


def test_head_refusals_ahead_not_behind_no_compare_refusal() -> None:
    run = newest_run(parse_runs(PR3_RUNS_JSON))
    jobs = parse_jobs(PR3_JOBS_JSON)
    assert head_refusals(PR3_HEAD_SHA, (3, 0), run, jobs, REQUIRED) == []


def test_head_refusals_several_problems_at_once_prints_every_line() -> None:
    """Behind, the run's own conclusion (D-04), and one red job, together -- all
    three refusal lines present (a fourth possible line, a skip token, is
    `message_refusals`' own concern -- tested combined at the `land()` level
    below)."""
    run = WorkflowRun(id=1, status="completed", conclusion="failure", html_url="u")
    jobs = [
        {"name": "test (3.12)", "conclusion": "failure"},
        {"name": "vendor-bundle", "conclusion": "success"},
        {"name": "image", "conclusion": "success"},
    ]
    refusals = head_refusals(PR3_HEAD_SHA, (5, 2), run, jobs, REQUIRED)
    assert len(refusals) == 3
    assert any("behind" in r for r in refusals)
    assert any("test (3.12)" in r for r in refusals)
    assert sum("concluded" in r for r in refusals) == 1


# --- ordering: several runs for one sha ----------------------------------------------


def test_ordering_newer_failed_run_refuses_even_with_an_older_green_run() -> None:
    older_green = WorkflowRun(id=1, status="completed", conclusion="success", html_url="u1")
    newer_red = WorkflowRun(id=2, status="completed", conclusion="failure", html_url="u2")
    jobs = [{"name": name, "conclusion": "failure"} for name in REQUIRED]
    picked = newest_run([older_green, newer_red])
    assert head_refusals(PR3_HEAD_SHA, NOT_BEHIND, picked, jobs, REQUIRED) != []


def test_ordering_older_failed_run_does_not_block_a_newer_green_one() -> None:
    older_red = WorkflowRun(id=1, status="completed", conclusion="failure", html_url="u1")
    newer_green = WorkflowRun(id=2, status="completed", conclusion="success", html_url="u2")
    jobs = [{"name": name, "conclusion": "success"} for name in REQUIRED]
    picked = newest_run([older_red, newer_green])
    assert head_refusals(PR3_HEAD_SHA, NOT_BEHIND, picked, jobs, REQUIRED) == []


def test_ordering_shuffled_run_order_never_changes_the_verdict() -> None:
    older_red = WorkflowRun(id=1, status="completed", conclusion="failure", html_url="u1")
    newer_green = WorkflowRun(id=2, status="completed", conclusion="success", html_url="u2")
    jobs = [{"name": name, "conclusion": "success"} for name in REQUIRED]
    for run_list in ([older_red, newer_green], [newer_green, older_red]):
        picked = newest_run(run_list)
        assert head_refusals(PR3_HEAD_SHA, NOT_BEHIND, picked, jobs, REQUIRED) == []


def test_head_refusals_shuffled_job_order_never_changes_the_verdict() -> None:
    run = WorkflowRun(id=1, status="completed", conclusion="success", html_url="u")
    jobs = [{"name": name, "conclusion": "success"} for name in sorted(REQUIRED)]
    reversed_jobs = list(reversed(jobs))
    assert head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, jobs, REQUIRED) == []
    assert head_refusals(PR3_HEAD_SHA, NOT_BEHIND, run, reversed_jobs, REQUIRED) == []


# --- message_refusals() (the squash subject/body skip-token check) -------------------


def test_message_refusals_empty_for_a_clean_subject_and_body() -> None:
    assert message_refusals("feat(05-02): add the merge gate", "A clean PR body.\n") == []


def test_message_refusals_empty_body_is_no_refusal() -> None:
    assert message_refusals("feat(05-02): add the merge gate", "") == []


def test_message_refusals_token_in_the_title_is_found_naming_it() -> None:
    refusals = message_refusals("fix: bug [skip ci]", "clean body")
    assert len(refusals) == 1
    assert "[skip ci]" in refusals[0]
    assert "edit the pr title or body" in refusals[0].lower()


def test_message_refusals_token_in_a_later_paragraph_of_the_body_is_found() -> None:
    """The `6fce500` shape (tests/test_skip_tokens.py's own fixture): a clean
    subject, a token mentioned in prose two paragraphs down."""
    body = (
        "This commit changes nothing about the pipeline.\n\n"
        "No [ci skip] on purpose -- this one should run.\n"
    )
    refusals = message_refusals("docs(04): note on CI behaviour", body)
    assert len(refusals) == 1
    assert "[ci skip]" in refusals[0]


def test_message_refusals_checks_the_whole_body_even_below_a_git_cut_line() -> None:
    """CR-01 / 05-VERIFICATION.md: git's `commit -v` cut line means nothing for this
    text -- the hook no longer cuts either (D-02) -- so this body passed
    `message_refusals` with zero refusals before this plan."""
    refusals = message_refusals("safe subject", CUT_LINE_BODY)
    assert len(refusals) == 1
    assert "[skip ci]" in refusals[0]


# --- parsers ------------------------------------------------------------------------


def test_parse_pull_request_reads_the_recorded_shape() -> None:
    pr = parse_pull_request(PR3_VIEW_JSON)
    assert pr == PullRequest(
        number=3, state="MERGED", base="main", head_sha=PR3_HEAD_SHA,
        head_branch="gsd/phase-04-typed-derived-dimensions-contract",
        title="Phase 4: Typed Derived-Dimensions Contract",
        body="## Summary\n\nTyped DerivedDimensions contract.\n",
    )


def test_parse_pull_request_raises_on_unparseable_output() -> None:
    with pytest.raises(ValueError, match="does not parse"):
        parse_pull_request("not json")


def test_parse_pull_request_raises_on_missing_field() -> None:
    with pytest.raises(ValueError, match="does not parse"):
        parse_pull_request('{"number": 3}')


def test_parse_runs_reads_the_recorded_shape() -> None:
    runs = parse_runs(PR3_RUNS_JSON)
    assert runs == [
        WorkflowRun(
            id=36088409707, status="completed", conclusion="success",
            html_url="https://github.com/halfb00t/spur/actions/runs/36088409707",
        )
    ]


def test_parse_runs_empty_array() -> None:
    assert parse_runs("[]") == []


def test_parse_jobs_reads_the_recorded_shape() -> None:
    jobs = parse_jobs(PR3_JOBS_JSON)
    assert {"name": "test (3.12)", "conclusion": "success"} in jobs
    assert len(jobs) == 4


def test_parse_compare_reads_the_recorded_shape() -> None:
    assert parse_compare(PR3_COMPARE_JSON) == (32, 1)


def test_parse_compare_raises_on_unparseable_output() -> None:
    with pytest.raises(ValueError, match="does not parse"):
        parse_compare("not json")


# --- check_head (the read-only network shell, faked) --------------------------------


def test_check_head_green_returns_no_refusals() -> None:
    runner = (
        FakeRunner()
        .on(f"compare/main...{PR3_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        .on(f"runs?head_sha={PR3_HEAD_SHA}", cp(0, PR3_RUNS_JSON))
        .on("runs/36088409707/jobs", cp(0, PR3_JOBS_JSON))
    )
    assert check_head(PR3_HEAD_SHA, runner, REQUIRED) == []


def test_check_head_a_failed_runs_read_is_a_refusal_showing_stderr() -> None:
    runner = (
        FakeRunner()
        .on(f"compare/main...{PR3_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        .on(f"runs?head_sha={PR3_HEAD_SHA}", cp(1, "", "gh: rate limited"))
    )
    refusals = check_head(PR3_HEAD_SHA, runner, REQUIRED)
    assert len(refusals) == 1
    assert "rate limited" in refusals[0]


def test_check_head_unparseable_runs_output_is_a_refusal() -> None:
    runner = (
        FakeRunner()
        .on(f"compare/main...{PR3_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        .on(f"runs?head_sha={PR3_HEAD_SHA}", cp(0, "not json"))
    )
    refusals = check_head(PR3_HEAD_SHA, runner, REQUIRED)
    assert len(refusals) == 1


def test_check_head_a_failed_compare_read_is_a_refusal_showing_stderr() -> None:
    runner = FakeRunner().on(f"compare/main...{PR3_HEAD_SHA}", cp(1, "", "gh: not found"))
    refusals = check_head(PR3_HEAD_SHA, runner, REQUIRED)
    assert len(refusals) == 1
    assert "not found" in refusals[0]


def test_check_head_unparseable_compare_output_is_a_refusal() -> None:
    runner = FakeRunner().on(f"compare/main...{PR3_HEAD_SHA}", cp(0, "not json"))
    refusals = check_head(PR3_HEAD_SHA, runner, REQUIRED)
    assert len(refusals) == 1


def test_check_head_zero_runs_refuses_naming_no_ci_yml_run_and_the_sha() -> None:
    """PR #2's own live shape (this plan's own execution, 2026-09-25): zero `ci.yml`
    runs for a head sha -- a skip token on the head commit suppressed the run
    entirely, the same shape a never-triggered workflow would leave."""
    runner = (
        FakeRunner()
        .on(f"compare/main...{PR2_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        .on(f"runs?head_sha={PR2_HEAD_SHA}", cp(0, PR2_RUNS_JSON))
    )
    refusals = check_head(PR2_HEAD_SHA, runner, REQUIRED)
    assert len(refusals) == 1
    assert "no ci.yml run" in refusals[0]
    assert PR2_HEAD_SHA in refusals[0]


# The live, read-only check that `check_head` on PR #3's real head returns exactly one
# `behind` refusal (must_haves truth 8) is deliberately NOT a pytest test here -- it
# needs network and an authenticated `gh`, which `make verify`/`make test` must never
# require. It is this plan's own `<verify>` block, run once as a standalone command
# (05-02-PLAN.md Task 2 `<verify>`), not part of the offline suite.


# --- land(): the whole path, offline -------------------------------------------------


def _happy_runner(pr_json: str = PR3_VIEW_JSON.replace('"MERGED"', '"OPEN"')) -> FakeRunner:
    """An OPEN PR based on main, a clean tree, a current (not behind) compare, one
    green completed run, a successful merge, the squash commit's oid, and -- for the
    squash sha -- no run on the first poll, one on the second (the poll-success
    shape)."""
    return (
        FakeRunner()
        .on("pr view 3 --json number", cp(0, pr_json))
        .on("pulls/3/files", cp(0, PR_A_FILES_NO_GATE))
        .on("git diff --quiet", cp(0))
        .on("git diff --cached --quiet", cp(0))
        .on(f"compare/main...{PR3_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        # Read only for a PR that touches a FULL_TIER_PATHS path, which PR A's files do not;
        # ahead of the ci.yml runs handler, whose substring the operability query also holds.
        .on(f"{FULL_TIER_WORKFLOW}/runs", cp(0, TRACER_FULL_RUNS_JSON))
        .on(f"runs?head_sha={PR3_HEAD_SHA}", cp(0, PR3_RUNS_JSON))
        .on("runs/36088409707/jobs", cp(0, PR3_JOBS_JSON))
        .on("pr merge 3 --squash", cp(0))
        .on("pr view 3 --json mergeCommit", cp(0, "deadbeef1234"))
        .on(
            "runs?head_sha=deadbeef1234",
            cp(0, "[]"),
            cp(
                0,
                '[{"id":1,"status":"completed","conclusion":"success",'
                '"html_url":"https://github.com/halfb00t/spur/actions/runs/1"}]',
            ),
        )
        .on("commits/deadbeef1234", cp(0, SQUASH_COMMIT_READ))
        .on("git switch main", cp(0))
        .on("git pull --ff-only origin main", cp(0))
        .on(
            "rev-parse --verify --quiet refs/heads/gsd/phase-04",
            cp(0, PR3_HEAD_SHA),
        )
        .on("git branch -D gsd/phase-04", cp(0))
    )


def test_land_happy_path_returns_0_and_prints_the_run_url() -> None:
    runner = _happy_runner()
    sleeps: list[float] = []
    assert land(3, runner, sleep=sleeps.append) == 0
    assert sleeps == [5.0]  # exactly one sleep before the second poll finds the run
    merge_calls = [c for c in runner.calls if c[:3] == ["gh", "pr", "merge"]]
    assert merge_calls == [
        [
            "gh", "pr", "merge", "3", "--squash", "--match-head-commit", PR3_HEAD_SHA,
            "--subject", "Phase 4: Typed Derived-Dimensions Contract (#3)",
            "--body", "## Summary\n\nTyped DerivedDimensions contract.\n",
        ]
    ]
    assert not any("--delete-branch" in c for c in runner.calls)
    assert ["git", "switch", "main"] in runner.calls
    assert ["git", "pull", "--ff-only", "origin", "main"] in runner.calls
    assert ["git", "branch", "-D", "gsd/phase-04-typed-derived-dimensions-contract"] in runner.calls
    assert not any("commits/" in " ".join(c) for c in runner.calls)


def test_land_reports_the_last_read_error_when_every_poll_failed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """D-06, branch 1: every poll read fails -- the Codex review's own reproduction,
    `gh api` returning HTTP 403 on every attempt -- and the squash commit's message
    is clean. `land` reports the last read error it actually saw, never a skip token
    it never found."""
    runner = _happy_runner().replace(
        "runs?head_sha=deadbeef", cp(1, "", "gh: HTTP 403: API rate limit exceeded")
    )
    sleeps: list[float] = []
    result = land(3, runner, attempts=3, interval_s=1.0, sleep=sleeps.append)
    assert result == 1
    assert sleeps == [1.0, 1.0]  # attempts - 1
    out = capsys.readouterr().out
    assert "IS merged" in out
    assert "deadbeef1234" in out
    assert "no ci.yml run observed within 3 s" in out
    assert "last error: gh: HTTP 403" in out
    assert "skip token" not in out


def test_land_reports_no_run_observed_with_the_actions_url_when_reads_succeeded(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """D-06, branch 2: every poll read succeeds and returns nothing, and the squash
    commit's message is clean. `land` reports the Actions link to check by hand --
    no last error (the reads worked), no token (there is none)."""
    runner = _happy_runner().replace("runs?head_sha=deadbeef", cp(0, "[]"))
    sleeps: list[float] = []
    result = land(3, runner, attempts=3, interval_s=1.0, sleep=sleeps.append)
    assert result == 1
    assert sleeps == [1.0, 1.0]  # attempts - 1
    out = capsys.readouterr().out
    assert "IS merged" in out
    assert "deadbeef1234" in out
    assert "no ci.yml run observed within 3 s" in out
    assert "https://github.com/halfb00t/spur/actions/workflows/ci.yml" in out
    assert "last error" not in out
    assert "skip token" not in out


def test_land_names_a_skip_token_only_after_reading_it_from_the_squash_commit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """D-06, branch 3: every poll read succeeds and returns nothing -- same silence
    as branch 2 -- but this time the squash commit's own message, read only now that
    the poll gave up, carries a token. `land` names it: the one cause it could
    actually establish, read after the fact, never assumed up front."""
    runner = (
        _happy_runner()
        .replace("runs?head_sha=deadbeef", cp(0, "[]"))
        .replace(
            "commits/deadbeef1234",
            cp(
                0,
                "https://github.com/halfb00t/spur/commit/deadbeef1234\n"
                "chore: ship [skip ci]\n",
            ),
        )
    )
    sleeps: list[float] = []
    result = land(3, runner, attempts=3, interval_s=1.0, sleep=sleeps.append)
    assert result == 1
    out = capsys.readouterr().out
    assert "IS merged" in out
    assert "'[skip ci]'" in out
    assert "last error" not in out
    commit_calls = [
        c
        for c in runner.calls
        if c[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/deadbeef1234"]
    ]
    assert commit_calls == [
        [
            "gh",
            "api",
            "repos/{owner}/{repo}/commits/deadbeef1234",
            "--jq",
            ".html_url, .commit.message",
        ]
    ]


def test_no_run_report_a_failed_commit_read_is_the_last_error() -> None:
    """`no_run_report` in isolation: the squash commit read itself fails -- reported
    as the last error (there is no message to search for a token, and no commit URL
    to derive an Actions link from)."""
    runner = FakeRunner().on("commits/abc", cp(1, "", "gh: HTTP 404: Not Found"))
    report = no_run_report(3, "abc", 60.0, None, runner)
    assert "last error" in report
    assert "HTTP 404" in report
    assert "actions/workflows" not in report


def test_land_local_tip_differs_keeps_the_branch(capsys: pytest.CaptureFixture[str]) -> None:
    runner = _happy_runner().replace(
        "rev-parse --verify", cp(0, "0123456789abcdef0123456789abcdef01234567")
    )
    assert land(3, runner, sleep=lambda _: None) == 0
    assert not any(c[:3] == ["git", "branch", "-D"] for c in runner.calls)
    out = capsys.readouterr().out
    assert "differs from the merged head" in out


def test_land_local_branch_absent_no_delete_no_error() -> None:
    runner = _happy_runner().replace("rev-parse --verify", cp(1))
    assert land(3, runner, sleep=lambda _: None) == 0
    assert not any(c[:3] == ["git", "branch", "-D"] for c in runner.calls)


def test_land_pr_not_open_refuses_before_any_other_call(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = FakeRunner().on("pr view 2 --json number", cp(0, PR2_VIEW_JSON))
    result = land(2, runner, sleep=lambda _: None)
    assert result == 1
    assert len(runner.calls) == 1  # nothing else was ever called
    out = capsys.readouterr().out
    assert "MERGED" in out
    assert "nothing was merged" in out


def test_land_dirty_tree_refuses_no_merge_call(capsys: pytest.CaptureFixture[str]) -> None:
    runner = (
        FakeRunner()
        .on("pr view 3 --json number", cp(0, PR3_VIEW_JSON.replace('"MERGED"', '"OPEN"')))
        .on("git diff --quiet", cp(1))
    )
    result = land(3, runner, sleep=lambda _: None)
    assert result == 1
    assert not any(c[:3] == ["gh", "pr", "merge"] for c in runner.calls)
    out = capsys.readouterr().out
    assert "nothing was merged" in out


def test_land_unparseable_pr_read_refuses_no_merge_call(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = FakeRunner().on("pr view 3 --json number", cp(0, "not json"))
    result = land(3, runner, sleep=lambda _: None)
    assert result == 1
    assert not any(c[:3] == ["gh", "pr", "merge"] for c in runner.calls)
    out = capsys.readouterr().out
    assert "nothing was merged" in out


def test_land_refuses_a_token_hidden_below_a_git_cut_line_in_the_pr_body(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The whole path: a green, current head is not enough when the squash text carries
    a token behind a forged git cut line (CR-01 / 05-VERIFICATION.md's reproduction)."""
    pr_json = json.dumps(
        {
            "number": 3, "state": "OPEN", "baseRefName": "main",
            "headRefOid": PR3_HEAD_SHA,
            "headRefName": "gsd/phase-04-typed-derived-dimensions-contract",
            "title": "Phase 4: Typed Derived-Dimensions Contract",
            "body": CUT_LINE_BODY,
        }
    )
    runner = (
        FakeRunner()
        .on("pr view 3 --json number", cp(0, pr_json))
        .on("pulls/3/files", cp(0, PR_A_FILES_NO_GATE))
        .on("git diff --quiet", cp(0))
        .on("git diff --cached --quiet", cp(0))
        .on(f"compare/main...{PR3_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        .on(f"runs?head_sha={PR3_HEAD_SHA}", cp(0, PR3_RUNS_JSON))
        .on("runs/36088409707/jobs", cp(0, PR3_JOBS_JSON))
    )
    result = land(3, runner, sleep=lambda _: None)
    assert result == 1
    out = capsys.readouterr().out
    assert "[skip ci]" in out
    assert "nothing was merged" in out
    assert not any(c[:3] == ["gh", "pr", "merge"] for c in runner.calls)


def test_land_gh_pr_merge_failure_returns_1_no_poll_no_follow_up(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = (
        FakeRunner()
        .on("pr view 3 --json number", cp(0, PR3_VIEW_JSON.replace('"MERGED"', '"OPEN"')))
        .on("pulls/3/files", cp(0, PR_A_FILES_NO_GATE))
        .on("git diff --quiet", cp(0))
        .on("git diff --cached --quiet", cp(0))
        .on(f"compare/main...{PR3_HEAD_SHA}", cp(0, CURRENT_COMPARE_JSON))
        .on(f"runs?head_sha={PR3_HEAD_SHA}", cp(0, PR3_RUNS_JSON))
        .on("runs/36088409707/jobs", cp(0, PR3_JOBS_JSON))
        .on("pr merge 3 --squash", cp(1, "", "gh: PR is not mergeable"))
    )
    result = land(3, runner, sleep=lambda _: None)
    assert result == 1
    assert not any(c[:2] == ["git", "switch"] for c in runner.calls)
    out = capsys.readouterr().out
    assert "gh pr view 3" in out


def test_land_several_problems_at_once_prints_all_then_one_nothing_was_merged_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Behind, one red job, and a skip token in the body -- all three refusal lines
    printed together, then a single trailing `nothing was merged` line; no merge call."""
    pr_json = json.dumps(
        {
            "number": 3, "state": "OPEN", "baseRefName": "main",
            "headRefOid": PR3_HEAD_SHA,
            "headRefName": "gsd/phase-04-typed-derived-dimensions-contract",
            "title": "Phase 4: Typed Derived-Dimensions Contract",
            "body": "clean intro\n\nDon't add [ci skip] here.\n",
        }
    )
    behind_compare = '{"ahead_by":5,"behind_by":2}'
    red_jobs = json.dumps(
        [
            {"name": "test (3.12)", "status": "completed", "conclusion": "failure"},
            {"name": "vendor-bundle", "status": "completed", "conclusion": "success"},
            {"name": "image", "status": "completed", "conclusion": "success"},
        ]
    )
    runner = (
        FakeRunner()
        .on("pr view 3 --json number", cp(0, pr_json))
        .on("pulls/3/files", cp(0, PR_A_FILES_NO_GATE))
        .on("git diff --quiet", cp(0))
        .on("git diff --cached --quiet", cp(0))
        .on(f"compare/main...{PR3_HEAD_SHA}", cp(0, behind_compare))
        .on(f"runs?head_sha={PR3_HEAD_SHA}", cp(0, PR3_RUNS_JSON))
        .on("runs/36088409707/jobs", cp(0, red_jobs))
    )
    result = land(3, runner, sleep=lambda _: None)
    assert result == 1
    out = capsys.readouterr().out
    assert "behind" in out
    assert "test (3.12)" in out
    assert "[ci skip]" in out
    assert out.count("nothing was merged") == 1
    assert not any(c[:3] == ["gh", "pr", "merge"] for c in runner.calls)


# --- the full-tier rule (07 D-13, L27) ---------------------------------------------------------

FULL_RUN = WorkflowRun(41155746591, "completed", "success",
                       "https://github.com/halfb00t/screw/actions/runs/41155746591")


def test_parse_changed_files_reads_the_recorded_shape() -> None:
    paths = parse_changed_files(PR_A_FILES)
    assert len(paths) == 17
    assert paths[0] == ".github/workflows/operability.yml"
    assert parse_changed_files("") == []


@pytest.mark.parametrize("text", ["a.py\n\nb.py\n", "a.py\n \n", b"a.py\n", None])
def test_parse_changed_files_refuses_a_blank_line_or_output_that_is_not_text(
        text: object) -> None:
    with pytest.raises(ValueError, match="changed files output"):
        parse_changed_files(text)


@pytest.mark.parametrize(("path", "listed"), [
    ("src/screw/calc/cost.py", True), ("src/screw/calc/thread.py", True),
    ("src/screw/params.py", True), ("src/screw/solid/bolt.py", True),
    ("src/screw/solid/__init__.py", True), ("README.md", False),
    ("src/screw/solidx.py", False), ("src/screw/calc/__init__.py", False),
    ("src/screw/pool.py", False), ("src/screw/app.py", False),
    (".github/workflows/operability.yml", False)])
def test_full_tier_paths_match_the_cost_models_files_and_the_solid_package_only(
        path: str, listed: bool) -> None:
    """calc/__init__.py and pool.py / app.py are L27's exclusions: no tier run observes them."""
    assert full_tier_path(path) is listed


def test_full_tier_refusals_without_a_run_names_the_path_the_workflow_and_the_sha() -> None:
    (line,) = full_tier_refusals(["README.md", "src/screw/calc/cost.py"], None, PR3_HEAD_SHA)
    assert "src/screw/calc/cost.py" in line
    assert "README.md" not in line
    assert FULL_TIER_WORKFLOW in line
    assert PR3_HEAD_SHA in line


def test_full_tier_refusals_passes_a_completed_green_run() -> None:
    assert full_tier_refusals(["src/screw/solid/nut.py"], FULL_RUN, PR3_HEAD_SHA) == []


@pytest.mark.parametrize("run", [
    WorkflowRun(41155746591, "queued", None, FULL_RUN.html_url),
    WorkflowRun(41155746591, "in_progress", None, FULL_RUN.html_url),
    WorkflowRun(41155746591, "completed", "failure", FULL_RUN.html_url),
    WorkflowRun(41155746591, "completed", "cancelled", FULL_RUN.html_url)])
def test_full_tier_refusals_refuses_an_unfinished_or_red_run_with_its_url(
        run: WorkflowRun) -> None:
    (line,) = full_tier_refusals(["src/screw/params.py"], run, PR3_HEAD_SHA)
    assert run.html_url in line
    assert "src/screw/params.py" in line


def test_full_tier_refusals_is_empty_for_a_pr_that_touches_no_listed_path() -> None:
    assert full_tier_refusals(parse_changed_files(PR_A_FILES), None, PR3_HEAD_SHA) == []


def test_check_full_tier_reads_no_runs_for_a_pr_that_touches_no_listed_path() -> None:
    """The empty edge: such a PR lands exactly as before, the files read its only new call."""
    runner = FakeRunner().on("pulls/3/files", cp(0, PR_A_FILES_NO_GATE))
    assert check_full_tier(3, PR3_HEAD_SHA, runner) == []
    assert [" ".join(call) for call in runner.calls] == [
        "gh api repos/{owner}/{repo}/pulls/3/files --paginate --jq .[].filename"]


def test_check_full_tier_reads_only_full_runs_of_the_full_tier_workflow_for_the_head() -> None:
    """The recorded tracer head has a green operability run, but not a full one: refused."""
    files = PR_A_FILES_NO_GATE + "src/screw/solid/bolt.py\n"
    runner = (FakeRunner().on("pulls/3/files", cp(0, files))
              .on(f"{FULL_TIER_WORKFLOW}/runs?head_sha={TRACER_HEAD_SHA}",
                  cp(0, TRACER_FULL_RUNS_JSON)))
    (line,) = check_full_tier(3, TRACER_HEAD_SHA, runner)
    assert "src/screw/solid/bolt.py" in line
    assert "there is none" in line
    runs_call = runner.calls[1]
    assert f'select(.display_title == "{FULL_TIER_RUN_NAME}")' in runs_call[-1]
    assert WORKFLOW not in " ".join(runs_call)


def test_check_full_tier_refuses_the_recorded_queued_full_run_with_its_url() -> None:
    runner = (FakeRunner().on("pulls/3/files", cp(0, "src/screw/calc/cost.py\n"))
              .on("operability.yml/runs", cp(0, FULL_QUEUED_RUNS_JSON)))
    (line,) = check_full_tier(3, PR3_HEAD_SHA, runner)
    assert "still running" in line
    assert "actions/runs/41155746591" in line


def test_check_full_tier_a_failed_files_read_is_a_refusal_showing_stderr() -> None:
    runner = FakeRunner().on("pulls/3/files", cp(1, "", "HTTP 502: Bad Gateway"))
    (line,) = check_full_tier(3, PR3_HEAD_SHA, runner)
    assert "HTTP 502: Bad Gateway" in line
    assert len(runner.calls) == 1


def test_check_full_tier_unparseable_files_or_a_failed_runs_read_is_a_refusal() -> None:
    blank = FakeRunner().on("pulls/3/files", cp(0, "src/screw/params.py\n\nREADME.md\n"))
    assert len(check_full_tier(3, PR3_HEAD_SHA, blank)) == 1
    runs = (FakeRunner().on("pulls/3/files", cp(0, "src/screw/params.py\n"))
            .on("operability.yml/runs", cp(0, "not json")))
    (line,) = check_full_tier(3, PR3_HEAD_SHA, runs)
    assert "does not parse" in line
    failed = (FakeRunner().on("pulls/3/files", cp(0, "src/screw/params.py\n"))
              .on("operability.yml/runs", cp(1, "", "HTTP 403")))
    (line,) = check_full_tier(3, PR3_HEAD_SHA, failed)
    assert "HTTP 403" in line


def test_land_refuses_a_pr_that_touches_the_solid_package_with_no_full_run(
        capsys: pytest.CaptureFixture[str]) -> None:
    runner = (_happy_runner()
              .replace("pulls/3/files", cp(0, PR_A_FILES_NO_GATE + "src/screw/solid/bolt.py\n")))
    assert land(3, runner, sleep=lambda _: None) == 1
    out = capsys.readouterr().out
    assert "src/screw/solid/bolt.py" in out
    assert f"head {PR3_HEAD_SHA} needs a green full {FULL_TIER_WORKFLOW} run" in out
    assert out.strip().endswith("pr.land: nothing was merged.")
    assert not [call for call in runner.calls if call[:3] == ["gh", "pr", "merge"]]


def test_land_merges_a_pr_that_touches_a_listed_path_once_its_full_run_is_green() -> None:
    green = FULL_QUEUED_RUNS_JSON.replace('"conclusion":null', '"conclusion":"success"').replace(
        '"status":"queued"', '"status":"completed"')
    runner = (_happy_runner().replace("pulls/3/files", cp(0, "src/screw/calc/cost.py\n"))
              .replace(f"{FULL_TIER_WORKFLOW}/runs", cp(0, green)))
    assert land(3, runner, sleep=lambda _: None) == 0


# --- the gate-change rule (L28) ----------------------------------------------------------------


def test_pr_land_refuses_a_pr_that_edits_its_own_full_tier_judge_without_the_flag() -> None:
    """PR A (#22) is the recorded case: it touched the workflow and the bench judge at once."""
    (line,) = gate_refusals(22, parse_changed_files(PR_A_FILES), owner_approves=False)
    for path in (".github/workflows/operability.yml", "bench/__init__.py", "bench/oper.py",
                 "bench/oper_child.py", "bench/oper_lift.py"):
        assert path in line
    assert "bench/oper_sets.py" not in line
    assert f"make pr.land PR=22 PR_LAND_FLAGS={GATE_FLAG}" in line


@pytest.mark.parametrize("path", GATE_PATHS)
def test_pr_land_refuses_each_gate_file_on_its_own(path: str) -> None:
    (line,) = gate_refusals(3, ["README.md", path], owner_approves=False)
    assert path in line
    assert "README.md" not in line


def test_pr_land_allows_a_gate_change_the_owner_approves_with_the_flag() -> None:
    assert gate_refusals(22, parse_changed_files(PR_A_FILES), owner_approves=True) == []


def test_pr_land_gate_rule_is_unaffected_by_a_diff_that_touches_no_gate_file() -> None:
    changed = [*parse_changed_files(PR_A_FILES_NO_GATE), "bench/oper_sets.py",
               "bench/oper_bound.py", "bench/points/tracer.json"]
    assert gate_refusals(3, changed, owner_approves=False) == []


def test_pr_land_check_full_tier_keeps_the_full_run_refusal_beside_the_gate_refusal() -> None:
    """The flag lifts only the gate rule: a PR touching both still needs its green full run."""
    runner = (FakeRunner().on("pulls/3/files", cp(0, "bench/oper.py\nsrc/screw/params.py\n"))
              .on("operability.yml/runs", cp(0, TRACER_FULL_RUNS_JSON)))
    gate, full = check_full_tier(3, PR3_HEAD_SHA, runner)
    assert GATE_FLAG in gate
    assert "there is none" in full
    (line,) = check_full_tier(3, PR3_HEAD_SHA, runner, owner_approves_gate_change=True)
    assert "there is none" in line


def test_pr_land_land_refuses_a_gate_change_with_no_merge_call(
        capsys: pytest.CaptureFixture[str]) -> None:
    runner = _happy_runner().replace("pulls/3/files", cp(0, PR_A_FILES))
    assert land(3, runner, sleep=lambda _: None) == 1
    out = capsys.readouterr().out
    assert f"PR_LAND_FLAGS={GATE_FLAG}" in out
    assert out.strip().endswith("pr.land: nothing was merged.")
    assert not [call for call in runner.calls if call[:3] == ["gh", "pr", "merge"]]


def test_pr_land_land_merges_a_gate_change_the_owner_approves() -> None:
    runner = _happy_runner().replace("pulls/3/files", cp(0, PR_A_FILES))
    assert land(3, runner, sleep=lambda _: None, owner_approves_gate_change=True) == 0


BENCH = REPO_ROOT / "bench"
# Modules the full tier never runs, because full.json has no point of their kind: bound points
# run `bench.oper_bound`, load points `bench.oper_load` and probe points `bench.thread_spike`.
_KIND_ONLY = ("bench.oper_bound", "bench.oper_load", "bench.thread_spike")


def full_tier_judge_files(workflow: str) -> set[str]:
    """The files that decide a full-tier verdict, derived from the workflow text: the workflow,
    the point set its `--set` names, and the `bench` import closure (`ast`, function-level
    imports included, every enclosing package's `__init__.py` counted) of the modules its
    `python -m` lines run plus `bench.oper_child`, which `bench.oper run` starts in each
    container by name (`reading_argv`), less `_KIND_ONLY`."""
    sets = set(re.findall(r"--set ([a-z0-9-]+)", workflow))
    found = {f".github/workflows/{FULL_TIER_WORKFLOW}"} | {f"bench/points/{s}.json" for s in sets}
    todo = [*re.findall(r"python -m (bench[.\w]*)", workflow), "bench.oper_child"]
    seen: set[str] = set()
    while todo:
        name = todo.pop()
        if name in seen or name.startswith(_KIND_ONLY):
            continue
        seen.add(name)
        parts = name.split(".")
        for depth in range(1, len(parts) + 1):
            package = REPO_ROOT.joinpath(*parts[:depth], "__init__.py")
            if package.is_file():
                found.add(package.relative_to(REPO_ROOT).as_posix())
        module = REPO_ROOT.joinpath(*parts).with_suffix(".py")
        if not module.is_file():
            continue
        found.add(module.relative_to(REPO_ROOT).as_posix())
        for node in ast.walk(ast.parse(module.read_text())):
            if isinstance(node, ast.Import):
                todo += [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                todo += [node.module, *(f"{node.module}.{alias.name}" for alias in node.names)]
        todo = [n for n in todo if n.split(".")[0] == "bench"]
    return found


def test_gate_paths_are_what_the_workflow_runs_and_the_set_its_verdict_reads() -> None:
    """T-07 audit, L28: a bench module the full tier starts to import, or a new point set the
    workflow reads, fails here until it is on GATE_PATHS."""
    workflow = (REPO_ROOT / ".github" / "workflows" / FULL_TIER_WORKFLOW).read_text()
    assert "python -m bench.oper verdict --set full --from records" in workflow
    assert full_tier_judge_files(workflow) == set(GATE_PATHS)


def test_the_full_set_has_no_point_of_a_kind_the_gate_leaves_out() -> None:
    """The reason `_KIND_ONLY` is not on GATE_PATHS: a bound, load or probe point added to
    full.json would run one of them, and this fails first."""
    from bench.oper import BOUND_KINDS, LOAD_KIND, PROBE_KIND

    points = json.loads((BENCH / "points" / "full.json").read_text())["points"]
    kinds = {point["kind"] for point in points}
    assert kinds
    assert not kinds & (BOUND_KINDS | {LOAD_KIND, PROBE_KIND})


def _workflow_paths() -> list[str]:
    text = (REPO_ROOT / ".github" / "workflows" / FULL_TIER_WORKFLOW).read_text()
    block = text[text.index("  pull_request:\n    paths:\n"):]
    return re.findall(r'^      - "([^"]+)"$', block.split("\n\n", 1)[0], re.MULTILINE)


def test_full_tier_paths_equal_the_workflows_paths_filter() -> None:
    """T-07-50: the list decides and the filter only saves runs, so the two are held together on
    main, as required-jobs.txt is held to ci.yml."""
    paths = _workflow_paths()
    assert paths
    assert tuple(p[:-2] if p.endswith("/**") else p for p in paths) == FULL_TIER_PATHS


def test_the_full_tier_run_name_is_the_workflows_run_name_with_no_set() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / FULL_TIER_WORKFLOW).read_text()
    assert "run-name: \"operability: ${{ inputs.set || 'full' }}\"" in text
    assert FULL_TIER_RUN_NAME == "operability: full"


SRC = REPO_ROOT / "src"


def _module_file(name: str) -> Path | None:
    """The file of module `name` under src/, a package's `__init__.py` not counted: importing
    `screw.calc.thread` runs `screw/calc/__init__.py`, which L27 leaves off the list on purpose."""
    path = SRC.joinpath(*name.split(".")).with_suffix(".py")
    return path if path.is_file() else None


def cost_model_files() -> set[str]:
    """`src/screw/calc/cost.py` and every `src/screw` module it imports, directly or through
    another, found with `ast`: absolute and relative imports, function-level ones included, and
    `from P import n` as module `P.n` when that is a module."""
    found: set[Path] = set()
    todo = [SRC / "screw" / "calc" / "cost.py"]
    while todo:
        path = todo.pop()
        if path in found:
            continue
        found.add(path)
        package = path.relative_to(SRC).with_suffix("").parts[:-1]
        for node in ast.walk(ast.parse(path.read_text())):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                parts = list(package[:len(package) - node.level + 1]) if node.level else []
                base = ".".join([*parts, *([node.module] if node.module else [])])
                names = [base, *(f"{base}.{alias.name}" for alias in node.names)]
            for name in names:
                module = _module_file(name) if name.split(".")[0] == "screw" else None
                if module is not None:
                    todo.append(module)
    return {path.relative_to(REPO_ROOT).as_posix() for path in found}


def test_cost_model_files_follows_relative_and_function_level_imports(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calc = tmp_path / "src" / "screw" / "calc"
    calc.mkdir(parents=True)
    (calc / "cost.py").write_text("from .thread import x\nfrom screw import params\n")
    (calc / "thread.py").write_text("def f():\n    from screw.calc import extra\n")
    (calc / "extra.py").write_text("import math\n")
    (tmp_path / "src" / "screw" / "params.py").write_text("")
    monkeypatch.setattr(f"{__name__}.SRC", tmp_path / "src")
    monkeypatch.setattr(f"{__name__}.REPO_ROOT", tmp_path)
    assert cost_model_files() == {"src/screw/calc/cost.py", "src/screw/calc/thread.py",
                                  "src/screw/calc/extra.py", "src/screw/params.py"}


def test_every_module_the_cost_model_imports_is_on_the_full_tier_paths() -> None:
    """T-07-55: a prediction-moving module cost.py reaches and the list misses fails here."""
    files = cost_model_files()
    assert files == {"src/screw/calc/cost.py", "src/screw/calc/thread.py",
                     "src/screw/params.py"}
    assert all(full_tier_path(path) for path in files)
