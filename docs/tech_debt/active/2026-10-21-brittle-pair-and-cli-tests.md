# Three pair and CLI tests couple to prose, internal names and a wall-clock bound

Severity: nice
Status: active
Date: 2026-10-21
Source: 05-REVIEW.md IN-04, filed by plan 05-20 (owner's choice 2026-10-21)
Related files:
- tests/test_pair.py:726 (`test_the_shipped_row_is_called_evidence_in_the_docstring`) at ad09d46
- tests/test_pair.py:493-496 (the `rod_piece`, `blank` and `build` monkeypatch seams) at ad09d46
- tests/test_cli_pair.py:41 (`REFUSAL_SECONDS = 5.0` in `test_a_nut_too_thin_for_its_void_exits_2_and_names_it_before_any_kernel_loads`) at ad09d46
- docs/tech_debt/active/2026-10-20-ci-test-job-tripled-by-two-pair-tests.md

## Context
- `test_the_shipped_row_is_called_evidence_in_the_docstring` asserts that the word "evidence" occurs
  in `prove.__doc__`. That pins prose, not behaviour; the behaviour (the shipped row never changes
  the verdict) is covered by `test_a_planted_non_empty_shipped_reading_leaves_the_verdict_unchanged`.
- The orchestration tests replace `solid_pair.rod_piece`, `solid_pair.blank` and `solid_pair.build`
  with `monkeypatch`. The kernel cannot run `common` in-process, so a seam is justified, but the
  tests are coupled to the module's internal names. Correction, checked by the plan 05-20 planner:
  `monkeypatch.setattr` defaults to `raising=True`, so a rename fails the fixture loudly. The review's
  "silently passes" does not hold; the cost is coupling.
- `test_a_nut_too_thin_for_its_void_exits_2_and_names_it_before_any_kernel_loads` asserts a 5 s
  wall-clock bound. The flake is not observed. The runner's slowness is the subject of the item above,
  which this one does not re-plan.

## Why it matters
Each is cheap noise in a change that renames or moves code, or a flake waiting for a slow runner. None
hides a defect today.

## Next step
Revisit the first time the 5 s assertion fails, or at the next edit to the pair orchestration tests.
Drop the docstring test, pass the bodies through `prove` if a seam is wanted, and drop the timing
assertion (`test_a_refusal_leaves_the_kernel_out_of_the_process` covers the no-kernel property).
