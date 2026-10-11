---
phase: 04-iso-hex-bolts-and-screws
plan: 03
subsystem: solid
tags: [hex-head, tracer, bare-thread-gate, head-too-small, d-07, cadquery]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-01: the head-fuse probe numbers (bench/RESULTS.md) and the owner's opening read (04-OWNER-READS.md: s 10.0, k 4.0, pitch 1.0, permanent: accepted)"
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-02: FINE_STL_ROWS keyed by (d, pitch, left_hand) and fine_stl_refusal(d, pitch, length, left_hand)"
provides:
  - "BoltParams.s and .k (group Head) at the frozen owner-confirmed defaults 10.0 and 4.0, and the head_too_small rule (s must exceed d)"
  - "hex_prism_volume, bolt_closed_volume, head_too_small_refusal in calc/thread.py"
  - "bolt.thread(p) and bolt.assemble(p, thread): a sharp hex prism fused onto the L11 thread"
  - "_build gates the bare thread, then the fused part; check_solid(shape, closed, part)"
  - "info rows s, across_corners, k and a whole-part closed-form volume; the new standing warning"
affects: [04-04 (thread_length: passes t below length to bolt_closed_volume), 04-06 (bench README corpus wording), 04-07, 04-08 (row test asserts the frozen defaults), 04-09]

actuals:
  tokens: 15300
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Two gates inside the cached build: the bare thread against its own closed form, then the fused part against the whole-part closed form"
    - "A positive control for a diluted error: a thread wrong by 1.1e-4 to 1.4e-4 that the whole-part check alone passes"

key-files:
  created: []
  modified:
    - src/screw/params.py
    - src/screw/calc/thread.py
    - src/screw/calc/__init__.py
    - src/screw/solid/bolt.py
    - src/screw/solid/__init__.py
    - bench/corpus.py
    - tests/test_params.py
    - tests/test_calc.py
    - tests/test_solid.py
    - tests/test_api.py
    - tests/test_cli.py
    - tests/test_parity.py
    - tests/test_bench.py
    - tests/test_thread_maths.py

key-decisions:
  - "Defaults s 10.0 and k 4.0 are exactly the values in 04-OWNER-READS.md (D-07, L02); no fallback to expected values was needed"
  - "The thread's hand is probed on the bare thread bolt.thread(p), not the fused screw, because OCCT's isInside is unreliable on the fused M3.5 x 5.4 screw"
  - "Bench corpus entries pin s = 2 d and k = d / 2 as harness inputs so each passes s > d"

patterns-established:
  - "A kind-level rule that needs two fields lives as a model_validator with a lazy import of a pure refusal function in calc, raising PydanticCustomError with ctx.fields"

requirements-completed: [TYPE-01, TYPE-02, INFO-03]

coverage:
  - id: D1
    description: "The default link builds one valid hex head screw threaded to the head on the API, the CLI and the pool: thread on z 0..20, head on z 20..24, s across flats in x and s / cos 30 in y"
    requirement: TYPE-02
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_the_default_bolt_is_one_valid_hex_head_screw_threaded_to_the_head"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_the_default_part_served_is_the_gated_hex_head_screw"
        status: pass
      - kind: integration
        ref: ".venv/bin/screw export bolt -o x.stl --quality preview"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both gates run inside the cached build; a thread wrong by 1.1e-4 to 1.4e-4 that the whole-part check passes is refused naming the thread"
    requirement: TYPE-02
    verification:
      - kind: unit
        ref: "tests/test_solid.py#test_a_thread_wrong_by_a_part_in_ten_thousand_is_refused_on_the_thread_not_the_whole"
        status: pass
    human_judgment: false
  - id: D3
    description: "Info document rows d, pitch, length, turns, thread_depth, minor_diameter, s, across_corners, k, volume in that order, first warning the new standing text, volume from the closed form"
    requirement: INFO-03
    verification:
      - kind: unit
        ref: "tests/test_calc.py#test_the_default_document_lists_the_inputs_the_thread_the_head_then_the_volume"
        status: pass
      - kind: integration
        ref: "tests/test_parity.py#test_the_cli_and_the_api_print_the_same_document"
        status: pass
    human_judgment: false
  - id: D4
    description: "s <= d is a 422 head_too_small naming s and d on the API, a CLI exit 2 with the same text; s and k bounds refused naming themselves"
    requirement: TYPE-01
    verification:
      - kind: unit
        ref: "tests/test_params.py#test_a_head_no_wider_than_the_shank_is_refused_naming_s_and_d"
        status: pass
      - kind: integration
        ref: "tests/test_api.py#test_a_head_no_wider_than_the_shank_is_a_422_naming_s_and_d"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_a_thread_that_cannot_be_made_exits_2_naming_both_fields"
        status: pass
    human_judgment: false
  - id: D5
    description: "The page shows the head: it renders whatever STL arrives (no page code changed)"
    verification: []
    human_judgment: true
    rationale: "No browser is in the gate (L01); the head is visible only in a real viewer, and the page's code was not changed"

duration: approx. 55 min
completed: 2026-10-11
status: complete
plan_head_before: da94077b8d56f9f339dd2735bede249f36d38cce
plan_head_after: 478fc3f3049dec00862f52fa90cbdcacb186b64b
commits: 2
---

# Phase 4 Plan 03: Hex head screw tracer Summary

**The empty link now builds a gated ISO 4017 M6 x 20 style hex head screw (s 10, k 4 as the owner confirmed) on every front end: a sharp hex prism fused onto the L11 thread, judged twice, once on the bare thread and once on the whole part.**

## Performance

- **Duration:** approx. 55 min (start time was not captured at launch; estimated from the first read to the last commit)
- **Completed:** 2026-10-11
- **Tasks:** 2
- **Files modified:** 14 (451 insertions, 125 deletions)
- **Actuals note:** tokens is chars / 4 over the realized diff (61,176 chars), the estimate's scale; the plan estimated 140,000

## Accomplishments

- Precondition checked read-only before any edit: 04-OWNER-READS.md holds s 10.0, k 4.0, pitch 1.0 and `Permanence acknowledged: 2026-10-11, permanent: accepted`. The defaults committed are exactly those.
- `BoltParams` gains `s` ("Across flats") and `k` ("Head height") in a `Head` group, with the head_too_small rule (D-23, D-26: the rule is product policy; the probe fused s < d into a valid solid).
- `calc/thread.py`: `hex_prism_volume`, `bolt_closed_volume` and `head_too_small_refusal`, kernel-free; `calc/__init__.py`: the rows `s`, `across_corners` (s / cos 30 degrees, a full float, 11.547005383792515 for s 10), `k`, and a `volume` from the whole-part closed form, never the kernel's `Volume()`; the standing warning is now `plain-cut thread ends, no tip chamfer or under-head fillet; not a product build`.
- `solid`: `bolt.thread` and `bolt.assemble`; `_build` gates the bare thread against `closed_volume` (part "thread"), then the fused part against `bolt_closed_volume`. The thread is 0.570 of the whole volume at M6 x 20.
- Test ripple: 50 tests that pinned the old default part were updated in the same green commit (RESEARCH Pitfall 3), the bench corpus now pins `s = 2 d`, `k = d / 2`.
- Tracer gate: the plan's `<verify>` was re-run end to end after the commit (298 tests on the plan's seven files, the shipped CLI export, the info keys); "Tracer verified end-to-end" logged before Task 2.

## Task Commits

1. **Task 1: default link builds a hex head screw threaded to the head (tracer)** - `406c523` (feat)
2. **Task 2: head edges, bare-thread gate control, head_too_small on every front end** - `478fc3f` (test)

**Plan metadata:** the SUMMARY and state commits that follow.

## Files Created/Modified

- `src/screw/params.py` - `s`, `k` fields with frozen defaults; `_head_too_small` validator
- `src/screw/calc/thread.py` - hex prism, whole-bolt closed form, head_too_small refusal text
- `src/screw/calc/__init__.py` - head rows, whole-part volume row, new standing warning
- `src/screw/solid/bolt.py` - `thread(p)` and `assemble(p, thread)` replacing `rod`
- `src/screw/solid/__init__.py` - the two gates, `check_solid(..., part)`
- `bench/corpus.py` - each entry pins a head
- `tests/test_*.py` (8 files) - the default-part ripple plus the head edges

## Decisions Made

- Defaults from the owner's record only (D-07, L02); the literal `(6.0, 1.0, 20.0, 10.0, 4.0)` is asserted in `tests/test_params.py`.
- Hand probe on the bare thread (see deviation 1).
- `bench/README.md` left alone as the plan said; plan 04-06 rewords "The corpus".

## TDD Gate Compliance

Task 2 carries `tdd="true"`, and the pre-commit hook runs `make verify`, so a separate failing RED commit is impossible here (as in plan 04-02). What each phase showed:

- **RED for Task 1 (the ripple):** with the production change in the working tree and none of the tests updated, `make test` reported **50 failed, 821 passed**. The failures were exactly the tests that pin the old default part: default `BoltParams` values and schema property list, the slug (`..._length20` with no head), the info row keys and the standing warning text, the `d = 1e5` and `d = 10` fixtures that now need a head wider than d, `bolt.rod` as the monkeypatch target, `zmax` 20 against 24 and the bench corpus labels. Each was a deliberate assertion on the old behavior (semantic assessment: expected, intended RED).
- **RED for Task 2 (the new tests):** the new tests passed on first run because the behavior shipped in Task 1 (unexpected green by construction, not a wrong test). To prove they have teeth I mutated the implementation and re-ran them, then restored it (`src/` was clean afterwards):
  - Removing the bare-thread `check_solid(..., part="thread")` call: `test_a_thread_wrong_by_a_part_in_ten_thousand_is_refused_on_the_thread_not_the_whole` fails with `DID NOT RAISE BuildError`.
  - `circumscribed=True` to `False`: `test_the_default_bolt_is_one_valid_hex_head_screw...` and both `test_the_head_is_a_sharp_hex_prism...` cases fail.
  - `if s > d` to `if s >= d`: the head_too_small boundary tests in `tests/test_thread_maths.py` and `tests/test_params.py` fail (3 failed).
- **GREEN:** `make verify` (ruff, mypy --strict, import contracts, unfinished-work scan, pytest) exits 0 on both commits; the hook ran it. After Task 1: 917 passed, coverage 96.97 % (floor 96.0 %).
- **REFACTOR:** none.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Hand probe moved from the fused screw to the bare thread**
- **Found during:** Task 1 (ripple fix of `test_the_hand_decides_which_way_the_thread_climbs_and_both_pass_the_same_gate[folded-tail]`)
- **Issue:** `Shape.isInside` (OCCT's ray classifier) misreads the fused M3.5 x 5.4 screw: at 80 % of the tooth height it says outside at +theta, z 1.35 and 3.15, where the bare thread says inside; at 50 % the left-hand fused part reads inside at +theta. The fused solid is valid and inside T_GATE of its closed form, so this is a classifier limit, not a wrong part.
- **Fix:** the hand is probed on `bolt.thread(p)`, the exact solid `_build` fuses the head onto (the head is a prism on top and cannot change the hand); `build(p)` still asserts one valid solid and the whole-part volume for both hands. The reason and the measurement are in the test's comment.
- **Files modified:** tests/test_solid.py
- **Verification:** the test passes for both hands in all segments; the mutation checks above.
- **Committed in:** 406c523

**2. [Rule 1 - Bug] The CLI text rows cannot use the `error: <field>:` form**
- **Found during:** Task 2
- **Issue:** the plan asked `s` and `k` text to be refused naming themselves on the CLI; argparse rejects `--s text` before the model and prints `argument --s: invalid float value: 'text'`, not `error: s:`.
- **Fix:** a separate test asserts argparse's text, which names the flag; zero, negative, inf, nan and the bound stay in the `error: <field>:` list.
- **Files modified:** tests/test_cli.py
- **Committed in:** 478fc3f

**3. [Note] across_corners literal**
- The plan's must-have quotes 11.547005383792516 for s 10 (the kernel's bounding box reading); the row computed from the plan's own formula `p.s / math.cos(math.pi / 6)` is 11.547005383792515, one ulp lower. The row follows the formula; the test asserts equality with that expression and `approx(11.547005383792516, abs=1e-12)`. No effect on any consumer; flagged for the owner's awareness only.

**Total deviations:** 2 auto-fixed (both Rule 1, test-side), 1 note. **Impact:** no scope change; no source behavior differs from the plan.

## Issues Encountered

- `docs/architecture/decision_log.md` (around line 503) still quotes the old standing warning `threaded rod: no head, ...`. It is a historical decision record, not behavior, and the plan does not list it; plan 04-14 is where the decision log is corrected. Not edited here.
- The Task 1 `make verify` hook takes about 95 s; the commits landed without a timeout.

## Known Stubs

None. No stub, placeholder or skipped test was added; nothing was written to `.planning/WINDOWS.md`.

## Threat Flags

None. `s` and `k` reach the kernel through `BoltParams` as T-04-04 and T-04-05 describe; T-04-05 is mitigated by the two gates and exercised by the positive control.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 04-04 can pass `t = built_thread_length(...)` below `length` to `bolt_closed_volume`, and replace `t = p.length` in `_build`.
- The frozen defaults are asserted in `tests/test_params.py`; plan 04-08's row test should compare them with the cited ISO 4017:2022 M6 row.
- Carry-over for 04-06: `bench/README.md` "The corpus" still describes the corpus without the head pin.

## Self-Check: PASSED

All seven source files named in key-files (created or new symbols) exist; commits `406c523` and `478fc3f` are ancestors of HEAD; `make verify` passed in both commit hooks.

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-11*
