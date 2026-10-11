---
phase: quick-261011-fzb
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/test_bench.py
  - bench/thread_spike/pair.py
  - docs/tech_debt/INDEX.md
  - docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md
  - docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md
autonomous: true
requirements: [INFR-03]

estimate:
  tokens: 40000
  raw_tokens: 40000
  tasks: 2
  confidence: low

must_haves:
  truths:
    - "A serial run of the pair block (`-k \"common or pair or place or nut or rod_piece\" -n0`, under `-X faulthandler`) exits 0 and prints no `Fatal Python error` line. Before the change it exits 139"
    - "A serial run of the whole of tests/test_bench.py (`-n0 --no-cov`) exits 0. This is the debt item's own reproduction. The measured pass count and rc are quoted in the resolved item and in the SUMMARY"
    - "No test calls `pair.common` in the pytest process. The in-process overlap/disjoint test is gone, and its name appears nowhere in tests/test_bench.py"
    - "`test_a_child_that_read_a_pose_comes_back_with_exit_0_the_way_the_worker_ends` still has the child's exit code 0 as the behaviour under test. In the parent it now parses the child's printed overlap tuple and asserts volume == pytest.approx(1.0), solids == 1, errors is False, warnings is False and seconds > 0. It keeps the disjoint pair's `(0.0, 0)`. Its docstring says, with the crash frame and date, why the in-process test is gone"
    - "`pair.common` and bench/thread_spike/worker.py are byte-identical to 66d9393. pair.py gains at most one comment line next to `_KEEP`"
    - "The debt item is at docs/tech_debt/resolved/ with `Status: resolved` and `Resolved in: <sha> — <fix subject>`. The captured crash frame replaces its guess about the cause, and it has a dated Resolution section. Its INDEX row moved from Active to Resolved in the fix commit. A follow-up docs commit names the sha (repo precedent: ef37f23 then b537528, 0e2f437 then e079ef2)"
    - "`make verify` passes after both commits. The result line is quoted in the SUMMARY"
  artifacts:
    - path: "tests/test_bench.py"
      provides: "the child-process `common` test carrying every check of the deleted in-process test"
    - path: "bench/thread_spike/pair.py"
      provides: "one comment line by `_KEEP`: tests call `common` only in a child process"
    - path: "docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md"
      provides: "the resolved debt item, with the captured frame and the fix commit's sha"
    - path: "docs/tech_debt/INDEX.md"
      provides: "the row moved from Active to Resolved, as `<sha> — <subject>`"
  key_links:
    - from: "tests/test_bench.py test_a_child_that_read_a_pose_comes_back_with_exit_0_the_way_the_worker_ends"
      to: "bench/thread_spike/pair.py common / _KEEP"
      via: "the child prints the full `common` tuple. The parent parses it with `ast.literal_eval`, so the boolean is only ever parked in `_KEEP` inside a process that ends with `os._exit(0)`"
      pattern: "ast\\.literal_eval\\(overlap\\)"
    - from: "docs/tech_debt/INDEX.md Resolved table"
      to: "docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md"
      via: "a markdown link plus the same `<sha> — <subject>` string as the item's `Resolved in:` line"
      pattern: "resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially\\.md"
---

<objective>
Stop the pytest worker from dying with SIGSEGV at interpreter exit after a green run. Move the
last in-process `pair.common` test into the existing child-process test, then resolve the debt
item that recorded the crash.

Purpose: when a process exits non-zero after a green run, a real exit failure looks the same as
this crash. Under `make verify` (`-n 4`) the xdist worker crashes after it has reported, so the
gate stays green, but the owner gets a macOS crash report on every run. A serial `-n0` run (the
documented `-x` / `--pdb` form) exits 139.

Root cause, from the evidence: tests/test_bench.py:4147-4155 calls `pair.common` in the pytest
process. Each call appends a `(BRepAlgoAPI_Common, DSFiller)` tuple to `pair._KEEP`. At
`Py_FinalizeEx`, `_PyModule_ClearDict` frees that list, and the process faults in
`BRepAlgoAPI_BuilderAlgo::~BRepAlgoAPI_BuilderAlgo` (macOS crash report, 2026-10-11). The other
51 tests of the pair block exit 0 without it. The production worker never meets this, because
it ends with `os._exit(0)` (bench/thread_spike/worker.py:271).

Output: two commits on branch `fix/bench-pair-test-exit-139`.
(1) `test(bench): read pair.common only in a child so the pytest worker exits clean`: the test
change, a one-line comment in pair.py, and the debt item resolved and moved, all in one commit
(CLAUDE.md: "same commit as the fix").
(2) `docs(tech-debt): name the fix commit in the resolved pair-test segfault item`: writes
commit 1's sha into the item and its INDEX row.

Why two commits and not `--amend`: this is the repo's own pattern. ef37f23 then b537528 in PR #7,
0e2f437 then e079ef2, and 909dec3 whose sha a later commit named. A commit cannot contain its
own sha. A follow-up commit names it without rewriting history, so the sha it records stays
valid. Do not use `git commit --amend`.

Source coverage: GOAL (the quick description) is covered by Tasks 1 and 2. REQ INFR-03 (the
spike harness's tests stay trustworthy) is covered by Task 1. There is no RESEARCH or CONTEXT
artifact for this quick task.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@docs/CODING_VALUES.md
@bench/thread_spike/pair.py
@docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md
@docs/tech_debt/INDEX.md
@docs/tech_debt/resolved/2026-10-06-test-pool-dying-worker-flake.md

Read only these ranges of the large files:
- tests/test_bench.py lines 4147-4185: the in-process test, the subprocess test, `_m2_request`
- tests/test_bench.py lines 4187-4243: the other `run_pair` callers. None of them leaks into
  `_KEEP`. One stubs `common` with monkeypatch, one fails at the pad check, one fails in the
  build, and one runs in a `Worker()` child
- bench/thread_spike/worker.py lines 266-271: the `os._exit(0)` and its comment
- `ast` is already imported at tests/test_bench.py:23, and `subprocess`, `sys`, `Path` and
  `pytest` are imported too. Add no import

Branch state: `fix/bench-pair-test-exit-139` was cut from main at 66d9393 and has not been
pushed. Two untracked paths must never be staged: `.planning/ui-reviews/` and `web/.DS_Store`.
Stage by explicit path only, never `git add -A` or `git add .`.

Tooling facts:
- The pre-commit hook runs `make verify` on every commit, which takes about 4 min.
- The commit-msg hook rejects GitHub Actions skip tokens.
- Coverage is measured over `src/screw` only, so deleting a bench test cannot move the floor.
</context>

<!-- planner-discipline-allow: test_common_reads_the_volume_of_an_overlap -->
<!-- planner-discipline-allow: bench-pair-tests-segfault -->

<tasks>

<task type="tracer">
  <name>Task 1: Read pair.common only in a child process, and resolve the debt item in the same commit</name>
  <files>tests/test_bench.py, bench/thread_spike/pair.py, docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md, docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md, docs/tech_debt/INDEX.md</files>
  <action>
Step 0, RED reading (record it, change nothing). From the checkout root, run the decisive serial
check from this task's verify block on its own:
`.venv/bin/python -X faulthandler -m pytest tests/test_bench.py -k "common or pair or place or nut or rod_piece" -q -n0 --no-cov -p no:cacheprovider; echo "rc=$?"`.
Expected: `52 passed`, then `Fatal Python error: Segmentation fault`, then `rc=139`. Keep the
pass line and the rc for the SUMMARY. If it already exits 0, stop and report: the reproduction
has changed and this plan's premise no longer holds.

Step 1, the test (tests/test_bench.py). Delete the in-process test, lines 4147-4155: the
function test_common_reads_the_volume_of_an_overlap_and_zero_solids_for_a_disjoint_pair and the
two blank lines after it. Its name must not appear anywhere in tests/test_bench.py afterwards,
in a docstring or a comment too. Then change
`test_a_child_that_read_a_pose_comes_back_with_exit_0_the_way_the_worker_ends`:
- Child code: the first `print` prints the full `pair.common(box, <overlap box>)` tuple, so drop
  its `[:2]`. Leave the second `print` (the disjoint pair, `[:2]`), `gc.collect()` and
  `os._exit(0)` as they are.
- Parent: keep `assert done.returncode == 0, done.stderr` first, so the exit code stays the
  behaviour under test. Keep `overlap, apart = done.stdout.splitlines()`.
- Replace the two string checks on `overlap` (the `(1.0` prefix and the `, 1)` suffix) with:
  unpack `volume, solids, errors, warnings, seconds = ast.literal_eval(overlap)`, then assert
  `volume == pytest.approx(1.0)`, `solids == 1`, `errors is False`, `warnings is False` and
  `seconds > 0`, each as its own `assert`.
- Keep `assert apart == "(0.0, 0)"`.
- No `Any` annotation (L04). `ast.literal_eval` is already used untyped at tests/test_bench.py:4846,
  and mypy --strict accepts the unpack.
- Docstring: keep its four lines and append one sentence (lines up to 100 chars, ruff). Use this
  wording or a close equivalent, and do not name the deleted test: "The overlap's whole reading is
  checked here because nothing reads `common` in the pytest process any more: a call there parks
  its boolean in `pair._KEEP`, and freeing that at interpreter exit killed the xdist worker with
  SIGSEGV after it had reported green (crash frame `~BRepAlgoAPI_BuilderAlgo` under
  `_PyModule_ClearDict`, 2026-10-11)."

Step 2, pair.py. Insert exactly one comment line between the existing three-line `_KEEP`
comment and `_KEEP: list[object] = []`:
"# For the same reason tests call `common` only in a child process, never in pytest's own."
Change nothing else in pair.py, and nothing in bench/thread_spike/worker.py. `common` and the
hold stay, because freeing the hold is the crash.

Step 3, measure the fix. Run the verify block's first two commands. Then run the debt item's
own reproduction over the whole file:
`.venv/bin/python -X faulthandler -m pytest tests/test_bench.py -q -n0 --no-cov -p no:cacheprovider; echo "rc=$?"`.
It takes several minutes, so use `run_in_background` if it would pass the 10-min foreground
limit. Record its pass line and rc. If it does not end `rc=0` with no `Fatal Python error`
line, stop and report the rc and the faulthandler output. Do not resolve the debt item: another
in-process OCP hold exists, and the item must stay open with that evidence added.

Step 4, the debt item. Run `git mv docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md docs/tech_debt/resolved/`. Then edit the moved file:
- `Status: active` becomes `Status: resolved`.
- Add a line right after `Date: 2026-10-10`, following the pool item's order:
  `Resolved in: test(bench): read pair.common only in a child so the pytest worker exits clean (this commit; the next commit names its sha)`.
- In Context, replace only its last sentence, the one starting with "ASSUMPTION:", with one or
  two sentences naming the captured frame: the macOS crash report of 2026-10-11 confirms the
  cause. SIGSEGV in `BRepAlgoAPI_BuilderAlgo::~BRepAlgoAPI_BuilderAlgo` under `tupledealloc` <-
  `list_dealloc` <- `_PyModule_ClearDict` <- `Py_FinalizeEx`: module teardown freeing
  `pair._KEEP`, which only the in-process test
  test_common_reads_the_volume_of_an_overlap_and_zero_solids_for_a_disjoint_pair filled. With it
  deselected, the other 51 tests of the block exit 0 (`-n0`, 2026-10-11).
- Leave "Why it matters" and "Next step" as written. Delete the trailing `<!-- On resolve: ... -->`
  comment, as no resolved item keeps it.
- Append a `## Resolution (2026-10-11)` section of three or four bullets in the resolved items'
  register:
  - The in-process test is deleted. Its checks (volume approx 1.0, one solid, both filler flags
    False, a positive time, the disjoint pair's `(0.0, 0)`) are now read from a child by
    `test_a_child_that_read_a_pose_comes_back_with_exit_0_the_way_the_worker_ends`, whose exit
    code stays the behaviour under test.
  - No test calls `common` in the pytest process. The remaining `run_pair` callers stub it, fail
    before the boolean, or run in a `Worker` child that ends with `os._exit(0)`. pair.py now says
    so next to `_KEEP`.
  - Measured after the fix: the Step 0 command gives `<N> passed`, rc 0 and no fatal line (139
    before). The whole file at `-n0` gives `<N> passed` and rc 0. Fill in the real numbers from
    Steps 0 and 3.
  - `pair.common`, the `_KEEP` hold and the worker are unchanged.

Step 5, INDEX. In docs/tech_debt/INDEX.md, delete the row for this item from the Active table.
Append a row at the end of the Resolved table, linking `resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md`
with the item's unchanged title. Its second cell is
`test(bench): read pair.common only in a child so the pytest worker exits clean`, the
subject-only placeholder from precedent. Task 2 adds the sha.

Step 6, commit. Run the verify block, then stage exactly these five paths:
- tests/test_bench.py
- bench/thread_spike/pair.py
- docs/tech_debt/INDEX.md
- the moved item (both sides of the rename, as `git mv` already staged them)

Commit with subject `test(bench): read pair.common only in a child so the pytest worker exits clean`.
Write a short prose body in normal sentences, not caveman:
- the in-process test parked two `(BRepAlgoAPI_Common, DSFiller)` tuples in `pair._KEEP`
- interpreter teardown freed them, and the pytest process died with SIGSEGV in
  `~BRepAlgoAPI_BuilderAlgo` after reporting green (macOS crash report, 2026-10-11; serial rc
  139 before, 0 after)
- its checks now run in the child-process test
- the debt item is resolved

End the body with the trailer line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
Let the hooks run, and never pass `--no-verify`. Right after the commit, record
`git rev-parse --short=7 HEAD` for Task 2.
  </action>
  <verify>
    <automated>out=$(.venv/bin/python -X faulthandler -m pytest tests/test_bench.py -k "common or pair or place or nut or rod_piece" -q -n0 --no-cov -p no:cacheprovider 2>&1); rc=$?; echo "$out" | tail -3; echo "rc=$rc"; test "$rc" -eq 0 && ! echo "$out" | grep -q 'Fatal Python error' && .venv/bin/python -m pytest tests/test_bench.py -k "test_a_child_that_read_a_pose" -q -n0 --no-cov -p no:cacheprovider && test "$(grep -c 'test_common_reads_the_volume_of_an_overlap' tests/test_bench.py)" -eq 0 && ! grep -nE '^[[:space:]]+[^"[:space:]].*pair\.common\(' tests/test_bench.py && r=$(awk '/^def test_a_child_that_read_a_pose/,/^def _m2_request/' tests/test_bench.py) && missing=0 && for p in 'returncode == 0' 'ast\.literal_eval\(overlap\)' 'pytest\.approx\(1\.0\)' 'solids == 1' 'errors is False' 'warnings is False' 'seconds > 0' 'apart == "\(0\.0, 0\)"'; do echo "$r" | grep -qE -- "$p" || { echo "missing: $p"; missing=1; }; done && test "$missing" -eq 0 && git diff --quiet 66d9393 -- bench/thread_spike/worker.py && pd=$(git diff -U0 66d9393 -- bench/thread_spike/pair.py) && ! echo "$pd" | grep -E '^[-+]' | grep -vE '^(\+\+\+|---|\+ *#)' && test "$(echo "$pd" | grep -cE '^\+ *#')" -le 1 && test -f docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md && test ! -e docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md && grep -q '^Status: resolved$' docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md && grep -q '_PyModule_ClearDict' docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md && grep -q '^## Resolution (2026-10-11)$' docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md && test "$(sed -n '/^## Active/,/^## Resolved/p' docs/tech_debt/INDEX.md | grep -c 'bench-pair-tests-segfault')" -eq 0 && sed -n '/^## Resolved/,$p' docs/tech_debt/INDEX.md | grep -q '(resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md)'</automated>
  </verify>
  <done>
- The Step 0 RED reading (52 passed, Fatal Python error, rc=139) and the post-fix readings are
  recorded for the SUMMARY. After the fix, the pair block gives rc=0 with no fatal line, and the
  whole file at `-n0` gives rc=0.
- The child test asserts returncode 0, volume approx 1.0, solids == 1, errors is False,
  warnings is False, seconds > 0 and the disjoint `(0.0, 0)`. Its docstring carries the crash
  frame and the date, and does not name the deleted test.
- pair.py differs from 66d9393 by one added comment line. worker.py is identical.
- The debt item is moved to resolved/, with Status resolved, the captured frame in Context in
  place of the guess, a `Resolution (2026-10-11)` section with measured numbers, and a
  subject-only `Resolved in:` placeholder. Its INDEX row is under Resolved only.
- One commit holds all five paths. `git show --stat HEAD` lists tests/test_bench.py,
  bench/thread_spike/pair.py, docs/tech_debt/INDEX.md and the rename. Neither
  `.planning/ui-reviews/` nor `web/.DS_Store` is staged. The pre-commit `make verify` passed.
  </done>
</task>

<task type="auto">
  <name>Task 2: Name the fix commit's sha in the resolved item and its INDEX row</name>
  <files>docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md, docs/tech_debt/INDEX.md</files>
  <action>
Follow the b537528 and e079ef2 precedent. Let SHA be the string Task 1 recorded with
`git rev-parse --short=7 HEAD`, which is now HEAD.

In the resolved item, replace the whole `Resolved in:` line with
`Resolved in: SHA — test(bench): read pair.common only in a child so the pytest worker exits clean`.
Use the em dash, as the INDEX rows do, and drop the "(this commit; ...)" note.

In docs/tech_debt/INDEX.md, the new Resolved row's second cell becomes the same string without
the `Resolved in: ` prefix: `SHA — test(bench): read pair.common only in a child so the pytest worker exits clean`.

Change nothing else. Stage exactly those two paths and commit with subject
`docs(tech-debt): name the fix commit in the resolved pair-test segfault item`. The body is
one sentence saying the follow-up names the sha because a commit cannot contain its own sha
(precedent b537528), then the `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
trailer. Let the hooks run.

After the commit, run `make verify` once more explicitly. pre-commit hides a passing hook's
output, so this run gives the result line for the SUMMARY. Quote the pytest result line and the
final line.

Squash-merge note, for the SUMMARY only: PRs here are squash-merged, so SHA is a branch commit,
as ef37f23 was. Whoever ships may append "(PR #N)" as that row does. This task does not.
  </action>
  <verify>
    <automated>subj='test(bench): read pair.common only in a child so the pytest worker exits clean'; dsubj='docs(tech-debt): name the fix commit in the resolved pair-test segfault item'; log=$(git log --abbrev=7 --format='%h%x09%s' 66d9393..HEAD) && sha=$(echo "$log" | awk -F'\t' -v s="$subj" '$2==s{print $1}') && dsha=$(echo "$log" | awk -F'\t' -v s="$dsubj" '$2==s{print $1}') && test "$(echo "$sha" | wc -w)" -eq 1 && test "$(echo "$dsha" | wc -w)" -eq 1 && test "$(echo "$log" | head -1 | cut -f1)" = "$dsha" && grep -qxF "Resolved in: $sha — $subj" docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md && sed -n '/^## Resolved/,$p' docs/tech_debt/INDEX.md | grep -qF "| $sha — $subj |" && files=$(git show --name-only --format= "$dsha") && test "$(echo "$files" | sort | tr '\n' ' ')" = "docs/tech_debt/INDEX.md docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md " && st=$(git status --porcelain docs/tech_debt tests bench) && test -z "$st" && make verify</automated>
  </verify>
  <done>
- The resolved item's `Resolved in:` line and its INDEX Resolved row both read
  `<fix commit sha> — test(bench): read pair.common only in a child so the pytest worker exits clean`.
- The tip of the branch is the docs commit and touches exactly those two files; the commit
  before it is the fix commit (both found by subject over 66d9393..HEAD).
- `git status --porcelain docs/tech_debt tests bench` is empty. The only untracked paths are
  still `.planning/ui-reviews/` and `web/.DS_Store`.
- The explicit `make verify` passed, and its result line is quoted in the SUMMARY.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| test to gate | The pytest process's exit status is part of what `make verify` and CI read. A crash at exit hides a real exit failure behind a known one |
| record to reader | The resolved debt item and its INDEX row are what a later agent trusts about the cause and the fix commit |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261011-fzb-01 | Tampering | tests/test_bench.py child `common` test | medium | mitigate | Every check of the deleted test reappears in the child test, parsed in the parent: volume approx 1.0, one solid, errors is False, warnings is False, seconds > 0, disjoint `(0.0, 0)`. Task 1's verify counts all six assertions in the function's region, and refuses any remaining in-process `pair.common(` call |
| T-261011-fzb-02 | Denial of service | pytest process exit status | medium | mitigate | The decisive check asserts rc 0 and no `Fatal Python error` line on the serial pair block, after a recorded RED reading of 139. The whole file at `-n0` must exit 0 before the item is resolved, or the task stops with the evidence |
| T-261011-fzb-03 | Repudiation | docs/tech_debt resolved item and INDEX | low | mitigate | The guess is replaced by the captured frame chain with its date. The fix commit's sha is named in a follow-up commit, with no history rewrite. Task 2's verify finds the fix commit by its exact subject over 66d9393..HEAD and requires the recorded string to equal its sha on a whole line |
| T-261011-fzb-04 | Information disclosure | commit text and debt item | low | accept | Only stack frame symbols, test names and dates are quoted. No host paths, user names or secrets |
</threat_model>

<verification>
After both commits, from the checkout root:
1. `.venv/bin/python -X faulthandler -m pytest tests/test_bench.py -k "common or pair or place or nut or rod_piece" -q -n0 --no-cov -p no:cacheprovider; echo "rc=$?"` ends with `rc=0` and prints no `Fatal Python error` line. Quote the pass line and rc, beside the Step 0 RED reading (rc=139).
2. `.venv/bin/python -m pytest tests/test_bench.py -k "test_a_child_that_read_a_pose" -q -n0 --no-cov` gives 1 passed.
3. `grep -c 'test_common_reads_the_volume_of_an_overlap' tests/test_bench.py` gives 0.
4. `.venv/bin/python -X faulthandler -m pytest tests/test_bench.py -q -n0 --no-cov -p no:cacheprovider; echo "rc=$?"` ends with `rc=0`. This is the debt item's own reproduction, run in Task 1 Step 3. Quote it.
5. `make verify` passes. Quote the result line (Task 2's explicit run).
6. `git status --porcelain docs/tech_debt` is empty. `test ! -e docs/tech_debt/active/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md` succeeds. `bench-pair-tests-segfault` appears in docs/tech_debt/INDEX.md under the Resolved table only.
7. `git log --oneline -3` shows the docs commit above the test(bench) commit, above 66d9393.
</verification>

<success_criteria>
- A serial `-n0` run of the pair block and of the whole of tests/test_bench.py exits 0. Before,
  the pair block exited 139.
- No test reads `pair.common` in the pytest process. The child test carries every check the
  deleted test had, and its exit code is still the behaviour under test.
- `pair.common` and the worker are unchanged. pair.py has at most one new comment line.
- The debt item is resolved per CLAUDE.md: Status flipped, `git mv` to resolved/, INDEX row
  moved, all in the fix commit. Its `Resolved in:` names the fix sha via the precedent's
  follow-up commit.
- `make verify` passes, with its result line quoted.
</success_criteria>

<output>
Create `.planning/quick/261011-fzb-stop-the-pytest-worker-segfault-at-exit-/261011-fzb-SUMMARY.md` when done. Include:
- the RED and GREEN readings (pass line plus rc) for the pair block and the whole file
- the `make verify` result line
- both commit shas and subjects
- the squash-merge note from Task 2
- a debt line: "Resolved docs/tech_debt/resolved/2026-10-10-bench-pair-tests-segfault-at-exit-when-run-serially.md; filed nothing new", unless something new had to be filed
</output>
