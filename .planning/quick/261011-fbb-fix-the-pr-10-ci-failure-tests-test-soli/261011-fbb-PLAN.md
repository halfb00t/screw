---
phase: quick-261011-fbb
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/test_solid.py
  - bench/thread_spike/helical.py
  - .planning/phases/03-real-helical-thread/03-01-PLAN.md
  - docs/architecture/decision_log.md
  - docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md
  - docs/ideas/INDEX.md
autonomous: true
requirements: [THRD-04]

estimate:
  tokens: 45000
  raw_tokens: 45000
  tasks: 2
  confidence: low

must_haves:
  truths:
    - "`test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid` collects exactly three ids, [2.0-0.4-4.0], [8.0-1.25-10.0] and [20.0-2.5-10.0], and all three pass on macOS arm64. Every row is one valid silent-wrong solid on linux/amd64 too: CI passes the first and third rows, and the emulated image measured the middle one at 1 solid, isValid True (THRD-04 positive control)"
    - "No assertion in the test changes. The `len(naive.Solids()) == 1`, `naive.isValid()` and `error < -0.5` checks and the refused-and-not-cached helper stay as they are. Only the middle parametrize row and the comment change"
    - "The comment above `naive = naive_sweep_fuse(...)` says why (6.0, 1.0, 10.0) is not used, with the measurement: on linux/amd64 with the same kernel pins it raises `Null TopoDS_Shape` (CI ubuntu-latest runs 38111898740 and 38112071431). On macOS arm64 it is one valid solid at 0.238 of the closed form. It points at L11's platform note"
    - "The `naive_sweep_fuse` docstring says its figures are from macOS arm64, that the fuse depends on the platform, and that M6 L10 raises `Null TopoDS_Shape` on linux/amd64. It points at L11's platform note"
    - "L11's 'Known-bad inputs for THRD-04' paragraph keeps all of its text, including the 15-row list (the decision_log diff only adds lines). A new dated paragraph follows it, starting with **Known-bad inputs, platform note**. It names the platform, the date, the kernel pins, the emulation, the five rows that differ with their outcomes, the CI runs and the rows the THRD-04 test now uses. It says the evidence is ad hoc and not a bench/RESULTS.md entry, and that neither the L11 decision nor the shipped builder is affected"
    - "03-01-PLAN.md names (8.0, 1.25, 10.0) as the middle control row in its truth (line 35) and its behaviour line (line 350), with a dated amendment that says what it was and why it changed. Its YAML frontmatter still parses"
    - "docs/ideas/ holds a new item, made from TEMPLATE.md, saying that Phase 7's OPER-02 linux/amd64 re-sweep must run the known-bad controls and not only the builder. docs/ideas/INDEX.md lists it under Open in the same commit"
    - "`make verify` passes after both commits, and the result line is quoted in the SUMMARY"
  artifacts:
    - path: "tests/test_solid.py"
      provides: "the THRD-04 naive-control parametrisation with (8.0, 1.25, 10.0) in place of (6.0, 1.0, 10.0), and the measured reason in a comment"
    - path: "bench/thread_spike/helical.py"
      provides: "`naive_sweep_fuse` docstring with the figures labelled by platform"
    - path: "docs/architecture/decision_log.md"
      provides: "the L11 'Known-bad inputs, platform note' paragraph (only adds lines)"
    - path: "docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md"
      provides: "the Phase 7 OPER-02 controls idea, in template format"
    - path: "docs/ideas/INDEX.md"
      provides: "the Open row linking the new item"
    - path: ".planning/phases/03-real-helical-thread/03-01-PLAN.md"
      provides: "the corrected positive-control criterion, with its dated amendment"
  key_links:
    - from: "tests/test_solid.py test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid"
      to: "bench/thread_spike/helical.py naive_sweep_fuse"
      via: "a parametrize row must be one valid silent solid on every platform the gate runs on (macOS dev, linux/amd64 CI and image)"
      pattern: "\\(8\\.0, 1\\.25, 10\\.0\\)"
    - from: "docs/architecture/decision_log.md L11 platform note"
      to: "tests/test_solid.py"
      via: "the note names the three rows the THRD-04 test uses; the test comment names the note"
      pattern: "platform note"
    - from: "docs/ideas/INDEX.md"
      to: "docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md"
      via: "a markdown link in the Open table"
      pattern: "2026-10-11-oper-02-resweep-runs-the-controls\\.md"
---

<objective>
Fix the one failing CI test on PR #10 (branch gsd/phase-03-real-helical-thread, HEAD a0d727a).
On linux/amd64, `tests/test_solid.py::test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid[6.0-1.0-10.0]`
raises `ValueError: Null TopoDS_Shape object` inside `naive_sweep_fuse`, at the core-cylinder
`fuse` on bench/thread_spike/helical.py:50. The pins are the same on both sides: cadquery 2.8.0,
cadquery-ocp 7.9.3.1.1. On macOS arm64 the row is one valid solid. The control is
platform-dependent. The shipped builder is not.

Owner decisions (this session, not re-litigated): swap the row for (8.0, 1.25, 10.0) and amend
L11. Also file the docs/ideas item. The L11 decision itself (sewn twist, K = 3, the gate) is NOT
superseded. Only its known-bad appendix gains a dated platform qualification.

Commit split (the planner's call, as the constraints asked): two commits, two concerns.
- Commit 1 is Task 1: make the THRD-04 test pass on every platform it runs on, and correct the
  two places that describe that test (the control's docstring, the Phase 3 criterion).
- Commit 2 is Task 2: record the platform evidence in the decision log, and file the
  follow-up idea.

Purpose: PR #10 cannot land on a red CI. A positive control that raises instead of returning a
silent-wrong solid never exercises the volume gate it exists to test.

Output: the two commits on the current branch, and
`.planning/quick/261011-fbb-fix-the-pr-10-ci-failure-tests-test-soli/261011-fbb-SUMMARY.md`.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@docs/CODING_VALUES.md
@.planning/STATE.md

Evidence (measured by the orchestrator on 2026-10-11; treat it as data, do NOT re-run the Docker sweep):
- CI: runs 38111898740 and 38112071431, ubuntu-latest x86_64, Python 3.12.15. Both read
  "1 failed, 859 passed". The only failure is the [6.0-1.0-10.0] row. Rows (2.0, 0.4, 4.0) and
  (20.0, 2.5, 10.0) pass.
- Ad-hoc linux/amd64 sweep of all 15 L11 known-bad rows: local image `screw:latest` (image id
  8d0261837661), run under qemu emulation on an arm64 host (OrbStack), "Linux x86_64 glibc 2.36,
  cadquery 2.8.0", same pins. It is NOT a bench/RESULTS.md entry, and none is to be added. Ten
  rows are 1 solid with isValid True, as on macOS. Five rows differ:
  - (2.5, 0.45, 4.5): raises `Null TopoDS_Shape`
  - (2.5, 0.45, 10.0): raises `Null TopoDS_Shape`
  - (6.0, 1.0, 10.0): raises `Null TopoDS_Shape`
  - (8.0, 1.25, 80.0): raises `Null TopoDS_Shape`
  - (20.0, 2.5, 200.0): 2 solids
  The emulated run reproduces CI exactly on the test's three rows.
- The replacement row (8.0, 1.25, 10.0) reads as follows.
  - macOS arm64: 1 solid, isValid True, precise ratio 0.231722 (bench/RESULTS.md, `2026-10-08-a-controls`), so the relative error is about -0.77, below -0.5.
  - linux/amd64 emulated: 1 solid, isValid True, about 0.5 s per control build.
- Volume caveat (the planner checked this on macOS, 2026-10-11): the ad-hoc sweep's "vol" figures
  are cadquery's default `Shape.Volume()`, not the precise BRepGProp eps 1e-6 estimator behind
  RESULTS.md's ratios. (2.0, 0.4, 20.0) reads `Volume()` 10.896 on both platforms, which is 0.2229
  of the closed form, against a precise 0.251542. So the L11 note claims outcomes only (raised,
  solid count, isValid) and never sets those volumes beside RESULTS.md's ratios.
- L11's known-bad list (`2026-10-08-a-controls`) was measured on macOS arm64 only. L11's
  container block (`2026-10-08-a-container`, linux/amd64, 7160 of 7160 ok) ran the shipped sewn
  builder, not the naive control.

Out of scope (leave untouched):
- tests/test_bench.py lines around 3106 and 3225. They assert RESULTS rendering of recorded data
  for (6.0, 1.0, 10.0), call no kernel, and pass on CI.
- 03-RESEARCH.md and 03-CONTEXT.md (historical research).
- bench/RESULTS.md.
- The coverage floor.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Swap the platform-dependent control row, record why, correct the Phase 3 criterion (commit 1)</name>
  <files>tests/test_solid.py, bench/thread_spike/helical.py, .planning/phases/03-real-helical-thread/03-01-PLAN.md</files>
  <read_first>
    - tests/test_solid.py lines 151-186 (the `_relative_error` and `_assert_refused_and_not_cached` helpers, the parametrize list on line 174, the comment on lines 178-179)
    - bench/thread_spike/helical.py lines 28-50 (`naive_sweep_fuse` and its docstring)
    - .planning/phases/03-real-helical-thread/03-01-PLAN.md line 35 (a frontmatter truth, a YAML double-quoted string), line 350 (behaviour bullet), lines 364-365 (the action text quoting "0.44 s, 0.50 s and 0.26 s")
    - docs/CODING_VALUES.md lines 20-50 (comments carry the measurement)
  </read_first>
  <action>
1. tests/test_solid.py, the parametrize list of `test_the_gate_refuses_the_naive_sweep_the_kernel_calls_valid`
   (line 174): replace the middle row (6.0, 1.0, 10.0) with (8.0, 1.25, 10.0). The list reads
   (2.0, 0.4, 4.0), (8.0, 1.25, 10.0), (20.0, 2.5, 10.0). Change nothing else in the test body,
   in either helper, or in any assertion.
2. Same test, the comment above `naive = naive_sweep_fuse(d, pitch, length)`. Keep its two
   existing lines: they stay true, because (8.0, 1.25, 10.0) is on the L11 list. Add at most four
   lines (ruff line-length 100, 4-space indent) that carry the constraint that forced the choice:
   - (8.0, 1.25, 10.0) is used, not L11's (6.0, 1.0, 10.0), because the naive fuse depends on the platform.
   - With the same pins, (6.0, 1.0, 10.0) raises `Null TopoDS_Shape` on linux/amd64. Cite CI
     ubuntu-latest, and say the emulated `screw:latest` image agrees.
   - On macOS arm64 the same row is one valid solid at 0.238 of the closed form.
   - All three rows here are one valid solid on both platforms.
   - Close with "L11, platform note".
   Cite the CI run ids in the decision log, not in the comment.
3. bench/thread_spike/helical.py, `naive_sweep_fuse` docstring, first paragraph after "Re-run
   here, the same recipe gave 0.238, 0.274 and the two exceptions.": add one or two sentences.
   - Those figures are macOS arm64.
   - The fuse depends on the platform: on linux/amd64 with the same pins, M6 L10 also raises
     `Null TopoDS_Shape`. Cite CI and the emulated image, 2026-10-11.
   - L11's known-bad platform note names the five rows that differ.
   Leave the code and the second paragraph alone. Keep the docstring at 100 columns.
4. .planning/phases/03-real-helical-thread/03-01-PLAN.md, line 35. Inside the double-quoted YAML
   string, replace (6.0, 1.0, 10.0) with (8.0, 1.25, 10.0). Before the closing quote, append a
   dated amendment in this sense: "; amended 2026-10-11 (quick 261011-fbb): the middle row was
   (6.0, 1.0, 10.0), which raises `Null TopoDS_Shape` on linux/amd64 with the same kernel pins
   (L11, Known-bad inputs, platform note)". Add no double-quote characters inside the string.
   Backticks are fine.
5. Same file, line 350 (behaviour bullet). Replace (6.0, 1.0, 10.0) with (8.0, 1.25, 10.0) and
   append "(amended 2026-10-11, quick 261011-fbb; see the positive-control truth)".
6. Same file, lines 364-365. The timing parenthetical "RESEARCH measured 0.44 s, 0.50 s and
   0.26 s" belongs to the old middle row. Append, inside that parenthetical: "; the 0.50 s row
   was (6.0, 1.0, 10.0), replaced by (8.0, 1.25, 10.0) on 2026-10-11, quick 261011-fbb".
   Do not invent a macOS timing for the new row. Record the measured test duration in the
   SUMMARY instead (step 7).
7. Run the verify command below. It runs the swapped test with `--durations=3`. Copy the pytest
   result line and the duration of the [8.0-1.25-10.0] case into the SUMMARY.
8. Commit only these three files, as a Conventional Commit:
   `test(solid): feed the gate a naive-sweep row that is one solid on linux/amd64 too`.
   The body, in normal prose: CI runs 38111898740 and 38112071431 raise `Null TopoDS_Shape` on
   (6.0, 1.0, 10.0) with the same pins, and macOS gives one valid solid. (8.0, 1.25, 10.0) is one
   valid solid on both platforms (L11 ratio 0.231722). The docstring and the 03-01 criterion are
   corrected to match. End with the Co-Authored-By trailer from the session's attribution
   reminder. The pre-commit hook runs `make verify`; if it fails, fix the cause, never use --no-verify.
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/test_solid.py -k naive_sweep -q --durations=3 && ids="$(.venv/bin/python -m pytest tests/test_solid.py -k naive_sweep --collect-only -q)" && printf '%s\n' "$ids" | grep -qF 'kernel_calls_valid[2.0-0.4-4.0]' && printf '%s\n' "$ids" | grep -qF 'kernel_calls_valid[8.0-1.25-10.0]' && printf '%s\n' "$ids" | grep -qF 'kernel_calls_valid[20.0-2.5-10.0]' && ! printf '%s\n' "$ids" | grep -qF 'kernel_calls_valid[6.0-1.0-10.0]' && d="$(git diff -U0 HEAD -- tests/test_solid.py)" && test "$(printf '%s\n' "$d" | grep -c '^-.*assert')" = 0 && .venv/bin/python -c "import yaml; t=yaml.safe_load(open('.planning/phases/03-real-helical-thread/03-01-PLAN.md').read().split('---')[1])['must_haves']['truths']; assert any('(8.0, 1.25, 10.0)' in s and '2026-10-11' in s for s in t)" && .venv/bin/ruff check tests/test_solid.py bench/thread_spike/helical.py</automated>
  </verify>
  <done>
- The three collected ids are [2.0-0.4-4.0], [8.0-1.25-10.0] and [20.0-2.5-10.0], and all pass on macOS.
- No assertion line was removed.
- The new comment and docstring say why (6.0, 1.0, 10.0) is not used, with the measurement.
- The 03-01-PLAN.md truth and behaviour line name (8.0, 1.25, 10.0) with a dated amendment, and the frontmatter parses.
- Commit 1 is on gsd/phase-03-real-helical-thread with only the three files.
  </done>
</task>

<task type="auto">
  <name>Task 2: Add L11's dated platform note and file the Phase 7 controls idea (commit 2)</name>
  <files>docs/architecture/decision_log.md, docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md, docs/ideas/INDEX.md</files>
  <read_first>
    - docs/architecture/decision_log.md lines 358-371. Read the "Known-bad inputs for THRD-04" paragraph, which ends "...the ones the gate must catch by volume.", then the blank line and the **Container.** paragraph.
    - docs/ideas/TEMPLATE.md, docs/ideas/INDEX.md, docs/ideas/2026-10-11-*.md (none yet) and docs/ideas/2026-10-05-wall-main-like-spur.md (house tone and wrapping)
  </read_first>
  <action>
1. docs/architecture/decision_log.md: add lines only. Do not edit or delete any existing line.
   The known-bad paragraph and its 15-row list stay byte-identical. After the paragraph's last
   line ("...the ones the gate must catch by volume.") add a blank line and one new paragraph.
   Keep that paragraph free of blank lines, wrap it near 100 columns like its neighbours, and
   start its first line with the exact lead `**Known-bad inputs, platform note**`, followed by
   "(added 2026-10-11, quick 261011-fbb)."
   It must state, in this order:
   (a) The list above was measured on macOS arm64 only (`2026-10-08-a-controls`). The container
       block ran the shipped builder, not this control.
   (b) The naive fuse depends on the platform with identical pins (cadquery 2.8.0, cadquery-ocp
       7.9.3.1.1). CI's ubuntu-latest x86_64 runner (runs 38111898740 and 38112071431) raises
       `Null TopoDS_Shape` on (6.0, 1.0, 10.0).
   (c) An ad-hoc re-run of all 15 rows on 2026-10-11, under `screw:latest` (image id
       8d0261837661) as linux/amd64 in qemu emulation on an arm64 host, found ten rows still one
       solid with `isValid()` true. Five rows differ: (2.5, 0.45, 4.5), (2.5, 0.45, 10.0),
       (6.0, 1.0, 10.0) and (8.0, 1.25, 80.0) raise `Null TopoDS_Shape`, and (20.0, 2.5, 200.0)
       is two solids. Say that the re-run is an emulation figure, ad hoc, not a
       `bench/RESULTS.md` entry, and that it agrees with CI on the test's three rows.
   (d) So a row is known-bad for a test only on a platform where it was measured silent. THRD-04's
       test uses (2.0, 0.4, 4.0), (8.0, 1.25, 10.0) and (20.0, 2.5, 10.0), which are silent on
       both platforms.
   (e) The decision above is unchanged, and the shipped builder is not implicated (container
       7160 of 7160 ok). Phase 7's native linux/amd64 re-sweep (OPER-02) is where the controls
       get measured per platform; link the idea item by its repo path.
   Quote no volume or ratio from the ad-hoc run (see the volume caveat in context). Use the
   facts as listed; do not round, re-derive or add numbers.
2. Create docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md from docs/ideas/TEMPLATE.md.
   Use exactly the template's lines and headings: title, Date, Source, Related files, then
   ## Context, ## Why it matters, ## Next step. Wrap it like the existing item.
   - Title: "Phase 7's linux/amd64 re-sweep runs the known-bad controls, not only the builder".
   - Date: 2026-10-11.
   - Source: the PR #10 CI failure (quick 261011-fbb).
   - Related files: docs/architecture/decision_log.md (L11), tests/test_solid.py,
     bench/thread_spike/helical.py, bench/RESULTS.md.
   - Context: L11's known-bad list was measured on macOS arm64 only, and the container block
     covered the builder alone. On linux/amd64, five of the 15 rows behave differently: name
     them, and say "see L11, platform note". The THRD-04 test row (6.0, 1.0, 10.0) failed CI and
     was swapped for (8.0, 1.25, 10.0).
   - Why it matters: THRD-04's positive-control test needs rows that are silent-wrong on the
     platform it runs on, and CI and the image are linux/amd64. A control that raises fails the
     test instead of exercising the volume gate. The 2026-10-11 evidence is one emulated, ad-hoc
     run.
   - Next step: "revisit when Phase 7 (OPER-02) is planned". The linux/amd64 re-sweep runs the
     `controls` block (`naive_sweep_fuse`, `one_pipe`) natively, next to the builder, and
     records it as a `bench/RESULTS.md` entry. Then check the THRD-04 test rows and the L11
     known-bad list against it.
3. docs/ideas/INDEX.md, `## Open` table: remove the placeholder row (the one with empty Date and
   Why cells) and add this row:
   2026-10-11 | [Phase 7's linux/amd64 re-sweep runs the known-bad controls, not only the builder](2026-10-11-oper-02-resweep-runs-the-controls.md) | Phase 7 (OPER-02) owns the first native linux/amd64 sweep.
   Use the table's pipe format. Leave the Done table alone.
4. Run the verify command below BEFORE committing. Its diff check compares against HEAD, which
   is commit 1.
5. Commit only these three files:
   `docs(decisions): qualify L11's known-bad rows by platform and file the OPER-02 controls idea`.
   The body, in normal prose: the five rows that differ on linux/amd64; the evidence (CI runs
   plus the emulated image, ad hoc, not a RESULTS.md entry); L11's decision unchanged. End with
   the Co-Authored-By trailer. The pre-commit hook runs `make verify`.
6. In the SUMMARY, state the filed item's path: docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md.
  </action>
  <verify>
    <automated>d="$(git diff -U0 HEAD -- docs/architecture/decision_log.md)" && test "$(printf '%s\n' "$d" | grep -c '^-[^-]')" = 0 && note="$(awk '/^\*\*Known-bad inputs, platform note\*\*/,/^$/' docs/architecture/decision_log.md)" && test -n "$note" && for s in '2026-10-11' 'macOS arm64' 'linux/amd64' 'emulation' 'cadquery 2.8.0' 'cadquery-ocp 7.9.3.1.1' '38111898740' '38112071431' 'Null TopoDS_Shape' '(2.5, 0.45, 4.5)' '(2.5, 0.45, 10.0)' '(6.0, 1.0, 10.0)' '(8.0, 1.25, 80.0)' '(20.0, 2.5, 200.0)' '(8.0, 1.25, 10.0)' 'RESULTS.md' 'OPER-02'; do printf '%s' "$note" | grep -qF -- "$s" || { echo "note missing: $s"; exit 1; }; done && grep -qF '(20.0, 2.5, 20.0), (20.0, 2.5, 200.0). Recipe:' docs/architecture/decision_log.md && f=docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md && grep -qx '## Context' "$f" && grep -qx '## Why it matters' "$f" && grep -qx '## Next step' "$f" && grep -q '^Date: 2026-10-11$' "$f" && grep -q 'OPER-02' "$f" && open_rows="$(awk '/^## Open/,/^## Done/' docs/ideas/INDEX.md)" && printf '%s\n' "$open_rows" | grep -qF '](2026-10-11-oper-02-resweep-runs-the-controls.md)' && test "$(printf '%s\n' "$open_rows" | grep -c '^| |')" = 0</automated>
  </verify>
  <done>
- The decision_log diff only adds lines, and the 15-row list is intact.
- The platform note paragraph carries the date, both platforms, the pins, the emulation label,
  both CI run ids, the five differing rows with their outcomes, the three test rows, the
  not-a-RESULTS.md-entry label and the OPER-02 pointer.
- The ideas item exists in template format, and INDEX.md lists it under Open with no placeholder row.
- Commit 2 is on the branch with only the three files.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| measurement to record | Platform evidence (CI logs, an emulated ad-hoc run) becomes a dated entry in the decision log that later phases plan on |
| test to gate | The positive-control test is the only proof that the THRD-04 volume gate catches a valid-looking wrong solid |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261011-fbb-01 | Tampering | tests/test_solid.py positive control | medium | mitigate | The replacement row comes from the same L11 list. Every assertion stays (one solid, isValid, error below -0.5, refused twice, not cached). Task 1's verify refuses a diff that removes an `assert` line and checks the three collected ids |
| T-261011-fbb-02 | Repudiation | docs/architecture/decision_log.md L11 | medium | mitigate | The note cites both CI run ids, labels the 15-row re-run as emulated, ad hoc and not a RESULTS.md entry, and quotes no `Volume()` figure beside the precise ratios. Task 2's verify refuses any deleted line in decision_log.md, so the original record stays intact |
| T-261011-fbb-03 | Information disclosure | commit text | low | accept | Only public CI run ids and a local image id are cited; no secrets or hosts |
| T-261011-fbb-SC | Tampering | npm/pip/cargo installs | low | accept | This plan installs no package and does not touch requirements.txt or pyproject.toml |
</threat_model>

<verification>
After both commits, from the checkout root:
1. `.venv/bin/python -m pytest tests/test_solid.py -k naive_sweep -q`: 3 passed. Quote the line.
2. `make verify`: ruff, mypy --strict, lint-imports, no-fake-done and pytest -n under the coverage floor all pass. Quote the result line. It takes about 4 min. The pre-commit hook runs it per commit too; this explicit run is the one quoted.
3. `git log --oneline -3` shows the two new commits on gsd/phase-03-real-helical-thread above a0d727a, and `git show --stat HEAD~1 HEAD` shows three files in each.

Linux/amd64 proof of the swapped row: the emulated measurement above, then the CI run that the
orchestrator triggers by pushing. The executor does not push.
</verification>

<success_criteria>
- The THRD-04 naive-control test collects [2.0-0.4-4.0], [8.0-1.25-10.0] and [20.0-2.5-10.0], passes locally, and every row is measured silent-wrong on linux/amd64.
- No assertion was weakened, and the comment carries the measured reason.
- L11 gains a dated platform note naming the five rows that differ, with the platform, date, pins, emulation and CI runs. Its original text is unchanged.
- The `naive_sweep_fuse` docstring and the 03-01-PLAN.md criterion match the new row.
- docs/ideas/2026-10-11-oper-02-resweep-runs-the-controls.md exists, with an INDEX.md Open row, in the same commit.
- `make verify` passes, and its result line is quoted in the SUMMARY.
</success_criteria>

<output>
Create `.planning/quick/261011-fbb-fix-the-pr-10-ci-failure-tests-test-soli/261011-fbb-SUMMARY.md` when done. Include:
- both commit shas;
- the quoted pytest and `make verify` result lines;
- the duration of the [8.0-1.25-10.0] case;
- the filed ideas item path.
</output>
