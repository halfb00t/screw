# Phase 6: Printed Pair Acceptance - Research

**Researched:** 2026-10-22
**Domain:** pre-registered physical measurement (FDM prints) that sets one frozen default and two printability constants in a Python 3.12 / Pydantic v2 / FastAPI / argparse code base; no new library.
**Confidence:** HIGH for the code seams, the prior-art pattern and the test blast radius (all read this session); LOW for anything about how a printer will behave (that is what the phase measures, and nothing here may become a value).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The owner's 0.1 mm enters the phase as the pre-registered **prediction** for the default,
  written into the method before the first print. The ladder is centred on it. The default is whatever
  the D-07 rule reads from the record, so it is 0.1 only if the record says so. PAIR-02 stands as
  written: no default from a guess, forum or vendor figure.
- **D-02:** Test parts are **product parts**: per size, ISO 4017 screws at a short standard length,
  built to nominal; ISO 4032 nuts at each clearance step. Every STL comes from the product's own
  `screw export` at the fine mesh, so the test checks exactly what a user downloads. No coupons.
- **D-03:** Clearance ladder **0.05, 0.10, 0.15, 0.20, 0.25 mm** (five steps). The 0.05 floor is the
  smallest clearance the fine mesh was sized against (L15 D-21: worst deviation 0.0161 mm against a
  0.025 mm bound). The ladder must not go below it without re-measuring the mesh.
- **D-04:** Sizes **M6, M8, M10, M12** (coarse pitch), **3 samples** per cell: 60 nuts, 12 bolts.
- **D-05:** Pass rule per sample: the printed nut turns **by fingers** from first engagement to the
  bolt's head and back off, with no tool and no stripped or shaved thread. Anything else is **bind**,
  recorded with where it stopped (turns). A loose fit still passes and is noted `loose`.
- **D-06:** **One fixed print profile** for every part in the phase: one printer, 0.4 mm nozzle, one
  material, one layer height, axis vertical (nut on its face, bolt head-down). The owner types the
  printer, material, layer height and slicer profile into the pre-registration. The default holds for
  those conditions, and the `Lxx` entry says so.
- **D-07:** Rule: the default is the **smallest step where 3/3 samples pass at all four sizes, and
  every larger step on the ladder also passes at all four sizes**. — **Reversibility:** one-way —
  L02: once a default ships, every shareable link that omits `clearance` means that value forever.
- **D-08:** Escape clause: if no step passes everywhere, or the record is not monotone (a smaller
  step passes where a larger one binds at the same size), **no default ships**. The record is kept as
  written. Claude stops and brings the owner options (extend the ladder above 0.25, a reprint rule
  pre-registered in a second run, a profile change). `clearance` stays required (L15 D-01) until a
  second pre-registered run sets it. No reprint is allowed inside the first run.
- **D-09:** The default is one value for every size (L02, SC2). A nut whose size is outside M6–M12
  gets the same default plus an info-document **warning**: the default clearance was measured on
  M6–M12 only (cite the `Lxx`). The warning is on the UI, API and CLI, and every number stays.
- **D-10:** The threshold comes from a **second pre-registered run**, after the default is set. It
  prints M3, M4 and M5 coarse pairs at the default, 3 samples each (9 bolts, 9 nuts), under the D-05
  pass rule and the D-06 profile. The threshold is the smallest size where it and every larger tested
  size pass 3/3. If M5 fails, the threshold is M6 from the main matrix.
- **D-11:** Two constants from that run: `d_min` and `P_min`, the `d` and coarse pitch of the
  threshold size. A part **warns when `pitch < P_min` or `d < d_min`**, and the warning names the edge
  crossed and the run that set it. So M12 × 0.5 warns on pitch, and M3 × 0.5 warns on both.
- **D-12:** Sizes below M3 (M2, M2.5) are never printed. They are below `d_min` by construction and
  warn.
- **D-13:** Below the threshold a part **builds and every number stays**; it is never a `422`. The
  warning goes on **both** the bolt and the nut info documents, on the UI, API and CLI, citing the
  constants' `Lxx` and run.
- **D-14:** The matrix's printed nominal bolts (same profile) are run into store-bought steel ISO
  4032 / DIN 934 nuts at **M6, M8, M10 and M12, 3 samples each**, under the D-05 pass rule. PAIR-07
  is promoted to a v1.x requirement if **any size binds in 2 or more of its 3 samples**. Otherwise the
  record says it is not needed. This threshold is pre-registered with the method.
- **D-15:** Phase 6 does not release. The "not a product build" clause in the standing warning
  (`src/screw/calc/__init__.py`) **stays**. The triggers of three debt items say "Phase 6 release"
  and are rewritten to "before the first release (after Phase 7)" in this phase's docs commit. None is
  resolved here:
  - `docs/tech_debt/active/2026-10-20-iso-standards-not-purchased.md`
  - `docs/tech_debt/active/2026-10-21-fillet-ring-can-overhang-the-head-flats.md`
  - `docs/tech_debt/active/2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md`
- **D-16:** SC3's acceptance is a **separate print after the default is in the code**. The owner
  prints one fresh **M8** pair through the shipped default path:
  1. the M8 bolt preset;
  2. the bolt's Matching nut link, with the clearance field left empty so the default applies;
  3. both parts exported.

  The kernel pair verdict for that nut must read `proven` before the print. The parts must thread
  together by hand under D-05. Matrix samples do not count toward SC3.

### Claude's Discretion

- The record format the owner fills in, where the pre-registration and the records live, the run ids,
  and how the result is pinned (follow the 02-SPIKE / `bench/results/` pattern: method committed
  first, record pinned by sha256).
- The short ISO 4017 length per size, and the print order.
- The exact warning texts for D-09 and D-13, following the existing `warnings` style in
  `src/screw/calc/__init__.py`.
- D-09's warning fires on size, whether or not `clearance` was typed: an omitted field and a typed
  value equal to the default can't be told apart in a link (L02).
- How the UI field shows the default. It follows the existing default-field behaviour. The parity
  test's one-required-field rule (L15 D-01) is removed when `clearance` gets its default.

### Deferred Ideas (OUT OF SCOPE)

- **INFO-06 print hints** (orientation, layer height vs pitch): the trigger "the first printed test
  recorded" fires in this phase. Placing it is a roadmap call, not built here.
- **A bought bolt into the printed nuts at each step**: informative, but not in PAIR-06. Raised in
  discussion and not taken.
- **A second print profile or layer height** (research P5's two heights): one fixed profile in v1
  (D-06).
- **Removing "not a product build" and settling the three release debt items**: at the first release,
  after Phase 7 (D-15).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAIR-02 | Default `clearance` set once from a recorded FDM printed test (M6–M12 matrix, owner checkpoint), cited in the decision log; never a forum or vendor figure. | Pre-registration pattern (Phase 5 05-01 / 02-SPIKE); a kernel-free rule module that re-derives the default from the owner's committed record (pattern of `test_nut_fine_stl_every_cap_is_recomputed_from_the_committed_records`); the one code seam `NutParams.clearance` (`params.py:186`); the test blast radius of removing "required" (section "Test blast radius"). |
| PAIR-05 | A printed bolt and nut at the default thread together by hand; kernel `proven` necessary, not sufficient. | D-16 path through the shipped CLI/UI (verified commands below); the recorded M8 grid verdicts; the 0.25 mm gap in the recorded grid; manual-only checkpoint. |
| PAIR-06 | The printed test also drives a nominal printed bolt into a bought nut; a bind promotes PAIR-07. | D-14 rule as a pure function in the same rule module; REQUIREMENTS.md has no v1.x section today, so promotion means adding one; sample-wear order effect (Pitfall 3, Open Question 2). |
| INFO-04 | Sizes and pitches below the printable threshold get a cap-and-warn printability warning citing its source. | One kernel-free seam: `derive()` in `src/screw/calc/__init__.py` feeds the UI, API and CLI, so one warning source reaches all three (verified); constants home in `src/screw/calc/`; constants re-derived from the run-2 record by test. |
</phase_requirements>

## Summary

The phase has two halves with different risk. The **code half is small and well-seamed**: `NutParams.clearance` is the only required field in the registry (`params.py:186-190`); every warning on every front end is a string in the `PartInfo.warnings` list built by `derive()` in `src/screw/calc/__init__.py` (the API route, `screw info`, `screw export` stderr and the page's `info.warnings` all read that one list), so the D-09 and D-13 warnings need exactly two insertion points (`_nut`, `_bolt`) and no JS change. The page already shows a defaulted field pre-filled from the schema default and omits it from the hash when equal to the default, so D-16's "clearance left empty" is "clearance left at its default" and needs no UI change. [VERIFIED: src/screw/static/app.js:104,365,390 and src/screw/calc/__init__.py:198-418 read this session]

The **process half is the hard part**: a pre-registered physical experiment whose rule must be committed on `main` before the first print, whose record the owner fills by hand, and whose result sets a one-way constant. The closest prior art is Phase 5 plan 05-01 (separate worktree + branch cut from `origin/main`, expected results *derived by script* from a recorded run, a re-derivation test in `make verify`, a protocol file with Question / Environment / Method / Predictions / Escape clause / Results, then the other CLI reviews and `make pr.land` lands it as its own PR before any run) and the house constant pattern (rule stated in a bench module docstring, JSONL/TSV record, a test that recomputes the typed constant from the committed record, a decision entry that cites the run). Phase 6 should copy that shape with one substitution: the "run" is the owner's hands, so the record is a hand-filled TSV validated strictly by a kernel-free rule module, and the rule module is exercised with synthetic records (positive and negative controls) so the escape clause is proven to fire before any real data exists.

Three non-obvious findings the planner must act on: (1) the recorded pair grid has **no 0.25 mm column** and several kernel verdicts at 0.05/0.10 are `inconclusive` for M10 and M12, so the "kernel verdict `proven`" precondition in D-16 is only guaranteed for M8 at 0.05-0.20 and needs a fresh `screw pair` run if D-07 lands on 0.25; (2) the 12 printed bolts are each tried against five nuts (and then a steel nut), so **test order is a confound that must be pre-registered**; (3) the registry-wide tests pin "clearance is required" in ~10 places (listed below) and the pre-registered `STANDING_WARNING` comment that says "Phase 6 removes the last clause" is stale against D-15.

**Primary recommendation:** Land one pre-registration PR (protocol + kernel-free rule module with synthetic-record tests + blank record template + STL manifest generator) from a worktree cut from `origin/main` before any print; make the owner-typed profile and predictions a blocking human-action inside it; derive the default and the thresholds only through `bench/print_rules.py`, never by hand; then wire `default + D-09` after run 1, and `D-13` after run 2, each pinned to the record by a test.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| The `clearance` default value | API / Backend (`screw.params`, the one validated model) | — | A parameter is validated once at the model boundary and trusted after (CLAUDE.md); schema default feeds UI, API and CLI automatically (FRNT-01). |
| Printability + "measured on M6–M12 only" warnings | API / Backend (`screw.calc.derive`, kernel-free) | Browser (renders `info.warnings` generically) | `derive()` is the single producer of warnings for all three front ends; no front end may carry its own text (`tests/test_parity.py` pins `info.warnings` is read in one place). |
| Printability constants (`d_min`, `P_min`, default's source, M6–M12 range) | API / Backend (new kernel-free module under `screw.calc`) | — | `calc` runs on every keystroke and must stay free of `cadquery`, `logging` and `screw.tables`. |
| Deriving default and thresholds from the record | Offline tooling (`bench/`, kernel-free, imported by tests only) | — | Same tier as `bench/pair_expected.py`; `src/screw` must never import `bench`. |
| STL generation for the prints | CLI (`screw export`) / `screw.solid` | — | D-02: product's own export path; kernel runs only in `solid`. |
| Kernel pair verdict for the D-16 nut | CLI (`screw pair`, imports `screw.solid.pair` lazily) | — | Never in the serving process (import contract "The serving process and its workers never import the pair proof"). |
| Printing, fit testing, recording | Owner (manual) | — | Cannot be automated; the plan's job is to make the record checkable. |
| The default field display / matching-nut link | Browser (existing generic form) | — | No change: default is prefilled from schema, omitted from hash at default. |

## Standard Stack

No new library. The phase uses what is already pinned.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12.15 | runtime (L01: 3.12 only) | locked [VERIFIED: `.venv/bin/python --version`] |
| pydantic | 2.13.5 | the parameter model; the default lands here | locked [VERIFIED: `.venv/bin/pip list`] |
| fastapi | 0.142.2 | API; query model copies model defaults | locked [VERIFIED: `.venv/bin/pip list`] |
| pytest | 9.1.1 (+ xdist 3.8.0, cov 7.1.0) | tests; coverage floor 96 | locked [VERIFIED: `.venv/bin/python -m pytest --version`, `pip list`; `pyproject.toml` `fail_under = 96`] |
| ruff / mypy | 0.16.10 / 2.4.0 | gate (`mypy --strict`, no `Any`, L04) | locked [VERIFIED: `.venv/bin/pip list`] |
| import-linter | 2.15 | module-graph contracts | locked; a new kernel-free bench module must be added to the contract "The spike's oracle, verdict and parent process stay free of the CAD kernel" (as 05-01 did for `bench.pair_expected`) [CITED: 05-01-SUMMARY.md, pyproject.toml:236-253] |
| stdlib `csv`, `hashlib`, `pathlib` | — | read the owner's TSV, pin sha256 | the pattern of `bench/pair_expected.py` (derive/render, sha256-pinned record) [CITED: 05-01-PLAN.md Task 1] |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `screw export <kind> --preset <id> [--clearance c] -o <dir> --format stl` | generate every test STL at the fine mesh (default quality is fine) | D-02. Verified: nut M8 c 0.1 writes `nut_d8_pitch1.25_left_hand0_s13_m6.8_clearance0.1.stl` (3,858,784 bytes, 2.9 s); bolt `iso4017:M8x16` writes `bolt_d8_pitch1.25_left_hand0_length16_s13_k5.3_thread_length16.stl` (10,204 KiB). Two exports of the same nut gave identical sha256 `9ada9620114be4870b44446cbcf50e26d0364f9728d71463f87566546b9fc7ce` on this host. [VERIFIED: ran it this session] |
| `screw pair nut --d .. --pitch .. --s .. --m ..` | D-16 kernel verdict | takes no `--preset`; pass the row's numbers. Exit 0 proven, 1 violated, 2 inconclusive, and the JSON on stdout is the discriminator (open debt `2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md`). [CITED: src/screw/cli.py:185-209, 245-257] |
| `make pr.land PR=N`, `git worktree add` | land the pre-registration PR first | as in 05-01 / 05-03. [CITED: 05-01-PLAN.md, docs/HOW_TO_DEVELOP.md §9] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-filled TSV record | JSONL like the bench records | JSONL is the bench house format for *machine* runs; the owner types this one, a TSV (like `tests/data/pair_expected.tsv`) is hand-editable and diffable. Recommend TSV. |
| One decision entry (L17) holding default and thresholds | L17 (default, D-09 range, profile) then L18 (thresholds) | The default is one-way (D-07) and ready after run 1; holding it for run 2 delays the D-16 acceptance. Recommend two entries; the planner may choose one entry amended in place (L15's own precedent). |
| Pre-registering run 2 after run 1 | Pre-register run 2 in the same PR as run 1, its clearance defined *by reference* ("the default D-07 reads") | Cleaner (predictions for M3-M5 predate all data) and one fewer pre-registration PR; its STL manifest is generated later. Recommend this; flag to the owner (Open Question 1). |

**Installation:** none. **Version verification:** versions above read from `.venv` this session; no package is added, so the Package Legitimacy Gate has nothing to check.

## Package Legitimacy Audit

No external package is installed by this phase. Table intentionally empty.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
 PRE-REGISTRATION (before any print)              OWNER (manual)                      CODE (after the record)
 -----------------------------------              --------------                      -----------------------
 06-PRINT-PROTOCOL.md  --\                                                           
 bench/print_rules.py   --+--> PR A on origin/main  (landed before print 1)           
 blank record TSV       --/        |                                                  
 STL manifest script               v                                                  
                         screw export (fine) --> STLs + manifest sha256 --> PRINT (one profile, D-06)
                                                                                |
                                  run 1: 60 nuts x 12 bolts  (M6-M12 x 5 steps x 3)   fit test D-05 --> record TSV (pass|bind, turns, loose)
                                  PAIR-06: 12 bolts x bought steel nut                 fit test D-05 --> record TSV
                                                                                |
                                          bench/print_rules.py  <-- committed record (sha256 pinned)
                                             |  D-07 rule        |  D-14 rule
                                             v                   v
                              default c  -- or ESCAPE (D-08: no default, stop, options)     PAIR-07 promoted? (any size >= 2 of 3 bind)
                                             |
                       NutParams.clearance = default (params.py)  + D-09 warning (calc.derive, nut)  + L17
                                             |
        +------------------------------------+-----------------------------+
        v                                                                  v
 run 2 (D-10): M3,M4,M5 pairs at the default (9+9)                 D-16: M8 preset -> Matching nut link (no clearance typed)
   -> record -> print_rules -> d_min, P_min -> calc warning D-13        -> `screw pair nut ... ` must read proven -> export both -> PRINT -> thread by hand
        (bolt AND nut, UI/API/CLI via derive())                                   -> PAIR-05 recorded by owner
```

### Recommended Project Structure
```
.planning/phases/06-printed-pair-acceptance/
├── 06-PRINT-PROTOCOL.md      # Question / Print profile (owner-typed) / Method / Matrix / Pass rule / Rules / Predictions / Escape clause / Results pointer
bench/
├── print_rules.py            # kernel-free: parse+validate the record, D-07/D-08/D-10/D-14, no I/O beyond reading the TSV
├── print_matrix.py           # the matrix as data (sizes, preset ids, lengths, steps, sample ids); optional `main()` that shells `screw export` and writes the manifest
└── results/phase-06/
    ├── print-run-1.tsv       # one row per sample: owner fills result/turns/note
    ├── print-run-2.tsv       # M3-M5 at the default
    └── manifest.tsv          # file name, bytes, sha256 per STL (not the STLs)
src/screw/calc/
└── printability.py           # constants D_MIN, P_MIN, MEASURED_RANGE, run ids + the two warning builders; imports nothing but math/typing
tests/
├── test_print_rules.py       # synthetic records: pass, escape (no step, non-monotone), D-14 boundary; the committed record re-derives the shipped constants
└── data/                     # nothing new required
```

### Pattern 1: Derive, never type (copy of `bench/pair_expected.py`)
**What:** a kernel-free script produces the constant from the committed record by the pre-registered rule; a `make verify` test recomputes it and fails on any difference; the record's sha256 is pinned in the module.
**When to use:** the clearance default, `d_min`, `P_min`, and the PAIR-07 verdict.
**Example** (shape only; the names are proposals, no value below is a product value):
```python
# bench/print_rules.py -- kernel-free; add to the spike kernel-free import contract.
LADDER = (0.05, 0.10, 0.15, 0.20, 0.25)      # D-03
SIZES = ("M6", "M8", "M10", "M12")           # D-04
SAMPLES = 3

def default_from(record: Record) -> float | None:
    """D-07: the smallest step with 3/3 at every size AND every larger step also 3/3 at every size.
    None means D-08 fired: no default ships. Non-monotone at any size is also None."""
    ok = {c: all(passes(record, s, c) == SAMPLES for s in SIZES) for c in LADDER}
    if any(not_monotone(record, s) for s in SIZES):
        return None
    firsts = [c for c in LADDER if all(ok[x] for x in LADDER if x >= c)]
    return firsts[0] if firsts else None
```

### Pattern 2: Pre-registration PR, then everything else
**What:** exactly 05-01/05-03: worktree + branch cut from `origin/main` (not `make worktree.new`, which branches from HEAD), own `make venv` in the worktree, commits go through the hook, other CLI reviews, `make pr.land` squashes, then merge `origin/main` back into the phase branch. The order is only visible on `main` across PRs because `make pr.land` squashes (02 D-19).
**When to use:** before print 1. [CITED: 05-01-PLAN.md objective; 05-03-SUMMARY.md]

### Pattern 3: Owner-typed inputs as a blocking checkpoint
**What:** Phase 5 05-02 used a `checkpoint:human-action` (`gate="blocking-human"`) and `05-OWNER-READS.md`. Phase 6 needs the same for (a) the print profile (printer, material, layer height, slicer profile; D-06), (b) the predictions beyond the owner's 0.1 mm, (c) each print session's record. [CITED: 05-02-PLAN.md:181; 05-OWNER-READS.md]

### Pattern 4: Warnings are strings in `derive()`
**What:** add to `_nut` and `_bolt` in `src/screw/calc/__init__.py`; keep `STANDING_WARNING` first; keep the counterpart `off_row` warning last (existing tests assert `warnings[-1]` for it: `tests/test_calc.py:1160,1167,1173`; `tests/test_api.py:1289`). Insert the new warnings *before* the `counterpart_for` block. D-09 only on the nut (the default is the nut's); D-13 on both kinds.

### Anti-Patterns to Avoid
- **A typed default or threshold.** The only way a number enters `params.py`/`printability.py` is by the rule module reading the committed record; a test re-derives it. (L02, PAIR-02, INFO-04.)
- **Reading the rule after the data.** No rule, ladder, size list, pass definition or threshold edit once a record row exists; a change after landing is a new PR that visibly post-dates the protocol (02 D-19).
- **A `422` for a small size.** D-13: below the threshold the part builds, every number stays, a warning is added. Nothing is capped (nothing *can* be capped without changing a user-set `d` or pitch).
- **Putting the warning text in JS or a second place.** `tests/test_parity.py:739` pins `info.warnings` read once; the text is Python-only.
- **Re-using the matrix bolts blindly** (see Pitfall 3).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Deriving the default / thresholds | an agent reading the TSV by eye | `bench/print_rules.py` + a re-derivation test | the default is one-way (D-07); a typed value is the failure mode T-05-01 guarded against |
| A new warning transport | an API/CLI/JS-specific message path | the existing `PartInfo.warnings` list | one producer, three consumers, parity already tested |
| Record integrity | trusting the owner's file | strict validation: every cell present, 3 samples, `result` in {pass, bind}, `turns` required on bind, sha256 pinned in the module | an incomplete or ambiguous record must fail loudly, not be interpreted |
| Pass/bind for the STL set | ad-hoc loops | one matrix-as-data module that the manifest, the record template and the tests all read | the 60/12/12 counts and file names must not drift between the three |
| Pre-registration ordering proof | a note saying "landed first" | the PR order on `main` (git history) as in Phase 5 | `make pr.land` squash makes the order checkable |
| The kernel verdict at the default | a hand calculation | `screw pair nut ...` (exit 0 + `"verdict": "proven"`) | PAIR-03 says the control makes it honest |

**Key insight:** every number that ships here is a *reading of a record*, so the work is making the reading mechanical and the record unforgeable-by-accident; the code change itself is a dozen lines.

## Common Pitfalls

### Pitfall 1: The recorded kernel grid does not cover the ladder
**What goes wrong:** D-16 requires `proven` before the print; the recorded K = 3 grid has clearances 0.05, 0.10, 0.15, 0.20 only. `grep 0.25 tests/data/pair_expected.tsv` returned nothing (this session). If D-07 lands on 0.25, the M8 verdict at the default is an *unregistered* fresh kernel run.
**Why:** `PAIR_CLEARANCES: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20)` is the proof bracket (`src/screw/calc/pair.py:40`); `prove()` itself accepts any `0 < c < d/2` (`src/screw/solid/pair.py:321-345`).
**How to avoid:** the plan states it up front: at the default, run `screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8` and record the JSON in `bench/RESULTS.md`; if the verdict is not `proven`, D-16 cannot be met as written -> stop and ask (CLAUDE.md "plan's acceptance criterion cannot be met"). Do **not** edit the table or any rule to turn it `proven` (L11, PAIR-03).
**Warning signs:** default = 0.25.

### Pitfall 2: Kernel `inconclusive` at the default for M10/M12 is not a print failure, and not a bug
**What goes wrong:** the recorded verdicts for the right/right hand cell, read this session by script from `tests/data/pair_expected.tsv`: M10 `inconclusive` at 0.05 and 0.10 (proven at 0.15, 0.20); M12 `inconclusive` at 0.05 (proven at 0.10-0.20); M6 and M8 `proven` at all four; M5 `inconclusive` at 0.05; M3 `inconclusive` at 0.05 and 0.15. [VERIFIED: tests/data/pair_expected.tsv, script output this session] So a default of 0.05 or 0.10 makes `screw pair` read `inconclusive` for some M6-M12 sizes by L11's scoping, independent of any print.
**How to avoid:** do not use the pair verdict as an input to D-07 (it is "necessary, not sufficient", PAIR-05). Mention in the L17 entry which sizes read `inconclusive` at the shipped default. Only M8 is a D-16 precondition.

### Pitfall 3: Bolt reuse is an uncontrolled confound in the matrix and PAIR-06
**What goes wrong:** D-04 gives 12 bolts for 60 nuts, so each bolt meets five nuts (and, by D-14, a steel nut). A bind can shave or deform the printed thread (D-05 itself names "stripped or shaved thread"), so a later nut meets a damaged bolt; a steel nut is harder than PLA/PETG and can abrade a printed thread.
**Why it happens:** no order is fixed by the decisions.
**How to avoid (recommend, pre-register):** (a) test each bolt against its five nuts from the loosest step to the tightest (0.25 -> 0.05): a binding nut then shaves the bolt only for steps that, by D-07's monotonicity, would not be counted as passes anyway; (b) record the order per sample in the TSV; (c) run the bought-nut test on bolts printed for it, from the same STL, same plate batch, same profile — "the matrix's printed nominal bolts" is satisfied by the matrix's STL, and it removes the wear confound. This departs from the literal D-14 reading if the owner meant the very same 12 physical bolts: **ask** (Open Question 2). These are design recommendations, not measurements. [ASSUMED]

### Pitfall 4: Samples of one cell sharing a plate
**What goes wrong:** three samples of one (size, clearance) cell printed on the same plate share bed temperature, first-layer and material-lot conditions; a plate-level fault looks like a clearance effect.
**How to avoid:** pre-register a plate rule (e.g. sample k of every cell on plate set k; record plate and bed position per part). [ASSUMED: general experimental design, not a measured printer fact]

### Pitfall 5: A hand-filled record that the rule can't read
**What goes wrong:** blank cells, `Pass`/`pass ` spelling drift, bind without turns, a fourth sample, a missing size, a reprint inside the run (forbidden by D-08).
**How to avoid:** the rule module refuses (raises, naming the row) rather than guessing; the blank template lists every expected sample id so a missing row is detectable; the sha256 is pinned only after the owner's last edit and the module's `RECORD_SHA256` is committed in the same change as the derived constant. Same refusal style as `bench/pair_expected.derive` (sha mismatch -> `ValueError` naming both digests). [CITED: 05-01-PLAN.md Task 1]

### Pitfall 6: "Outside M6-M12" is under-specified for the D-09 warning
**What goes wrong:** D-09 says "a nut whose size is outside M6-M12". Sizes are (d, pitch) pairs; the measured cells are the coarse pitches of four ISO 262 sizes. A user-set `d = 9` or pitch 0.75 at M8 is in no measured cell. Whether the warning keys on `d` alone, on `(d, pitch)`, or on membership in the measured set decides how often it fires.
**How to avoid:** pick one rule in the protocol and test its edges; recommend `d < 6.0 or d > 12.0` (a continuous range on the one variable the user sets, the interval the matrix spans) because pitch is already covered by the D-11 `P_min` rule for the fine side. Flag to the owner (Open Question 3). The warning must fire whether or not `clearance` was typed (CONTEXT, Claude's Discretion).

### Pitfall 7: Threshold semantics at the M6 floor
**What goes wrong:** D-10 can only return M3, M4, M5 or M6, so `d_min` is in {3, 4, 5, 6} and `P_min` in {0.5, 0.7, 0.8, 1.0} (the ISO 262 coarse pairs). If the threshold is M6, a *fine-pitch* M8 x 0.75 warns on pitch and the **default M6 x 1.0 bolt/nut does not** (1.0 is not < 1.0). The code must use strict `<` exactly as D-11 states, and equality of floats at M6 (`6.0`, `1.0`) is safe only because those are literals the model stores unchanged. [VERIFIED: `FastenerParams.d` default 6.0 and `pitch` default 1.0, src/screw/params.py:83-86]

### Pitfall 8: Test blast radius of removing "required"
See the dedicated section below; the failure mode is changing production code, running `make verify`, and discovering ten registry-wide tests that pinned the opposite.

### Pitfall 9: Stale comments that contradict D-15
`src/screw/calc/__init__.py:53-54` says "Phase 6 removes the last clause at release"; D-15 says the clause stays. `src/screw/params.py:184-185` says no default "until Phase 6 records the printed test". `src/screw/calc/pair.py:38-39` says the bracket "brackets Phase 6's printed matrix" (the ladder tops at 0.25, the bracket at 0.20). Update the first two with the change; the third is a statement the owner's ladder now contradicts at its top step, say so in the L17 entry.

## Test blast radius of giving `clearance` a default

`clearance` is the only required field of any kind. Things that pin "required" or depend on a missing clearance being a 422 (all read/grepped this session):

| File | What pins it | Action |
|------|--------------|--------|
| `tests/conftest.py:27` | `REQUIRED_VALUES = {"nut": {"clearance": 0.1}}` and `part_of` | becomes `{}`; keep the structure if the generic rule (below) stays |
| `tests/test_parity.py:184-203` | `test_the_required_fields_are_exactly_the_ones_the_samples_name` + planted-field teeth | with `REQUIRED_VALUES == {}` the first asserts no required field; keep both (the planted test keeps the rule honest) |
| `tests/test_parity.py:342-354` | per-case loop over `REQUIRED_VALUES` | `clearance` now flows through the generic "float default x 1.5" branch automatically |
| `tests/test_parity.py:970` | a `detail["type"] == "missing"` assertion | re-read; likely a nut-without-clearance case that now succeeds |
| `tests/test_params.py:69-77` | `test_the_clearance_has_no_default_and_a_missing_one_is_refused_naming_it` | replace with the default-literal + "default re-derives from the record" tests |
| `tests/test_nut.py:218-251, 322-329` | required field, 422 `missing` on info/model routes, help marks `[required]` | rewrite to the default |
| `tests/test_api.py:145-148` | nut schema `required == ["clearance"]` | now `[]`/absent; assert `default` is in the schema |
| `tests/test_cli.py:205-212` | `[required]` in `info nut --help` | the nut help now shows the default; move the `[required]` assertion to a planted field or drop with the CLI branch |
| `tests/test_cli.py` (nut clearance missing -> `error: clearance:`, ~line 195-200) | exit 2 on missing clearance | rewrite |
| `src/screw/cli.py:57`, `src/screw/static/app.js:54,181,318,464,525`, `src/screw/app.py:11,16,431,463`, `src/screw/calc/__init__.py:139-146` (Counterpart docstring) | comments/branches describing a required clearance | update comments; the `is_required()` CLI branch and `_req` become unused by any model: delete or keep only if a test pins them (surgical-edit rule: raise it, do not refactor silently) |
| `docs/architecture/overview.md:28` | "a required radial `clearance`" | update |

New warnings can also break exact-list assertions at sizes below the threshold or outside M6-M12 (e.g. `tests/test_calc.py:113,142,158,254,301,307,351,358,438,454,467,472,502,739,765`); most use d >= 6 so few will, and `make verify` finds the rest. A schema helper is needed because `_f` demands `gt=`: `clearance` accepts any finite value up to `INTERIM_MAX_MM` including <= 0 (`_req` has no `gt`; a nominal fit is legal, `tests/test_params.py:80` area and `NutParams` comment "D-04"). Use a default-carrying sibling of `_req` (no `gt`) rather than a negative `gt`, which would add `exclusiveMinimum` to the schema and an `input.min` to the form. [VERIFIED: src/screw/params.py:34-58, app.js:112-115 reads `prop.minimum`]

## Code Examples

### Where the D-09 / D-13 warnings go (insertion points, verbatim anchors)
`_nut` currently builds `warnings = [STANDING_WARNING]` then appends reasons, then `downloads`, then the M18 note, then the `counterpart_for` `off_row` warning last. [VERIFIED: src/screw/calc/__init__.py:377-410] Add the two warnings after the download refusals and before `counterpart_for`; `_bolt` likewise (`src/screw/calc/__init__.py:300-305`). Quoted anchor for the standing entry that must stay first:
```python
STANDING_WARNING = (
    "ends modelled per L15: bolt tip chamfer, under-head fillet on an ISO 4014 plain shank, "
    "nut lead-in countersinks and face chamfers; nominal, not toleranced; not a product build")
```
[VERIFIED: src/screw/calc/__init__.py:55-57]

### The seam that takes the default
```python
clearance: float = _req(
    le=INTERIM_MAX_MM, title="Clearance (radial)", group="Pair", unit="mm", step=0.01,
```
[VERIFIED: src/screw/params.py:186-188] The default literal is whatever `bench/print_rules.py` returns; this file may carry it only with a comment citing the run and `Lxx` and a test that re-derives it.

### The D-16 commands (default path, no clearance typed)
```bash
# 1. bolt: the M8 preset (shortest ISO 4017 M8 row in the catalogue is M8x16)
screw export bolt --preset iso4017:M8x16 -o out/ --format stl
# 2. nut: via the page's "Matching nut" link, or equivalently the M8 row's numbers with NO --clearance
screw export nut --preset iso4032:M8 -o out/ --format stl
# 3. kernel verdict before printing (exit 0 and "verdict": "proven")
screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8
```
The nut row `iso4032:M8 {'d': 8.0, 'pitch': 1.25, 's': 13.0, 'm': 6.8}` and the shortest ISO 4017 lengths per size (M6 12, M8 16, M10 20, M12 25; M3 6, M4 8, M5 10) were read from `screw presets nut|bolt` output this session. [VERIFIED: ran `.venv/bin/screw presets nut`, `presets bolt`] The bolt's counterpart link carries `{'d': 3.0, 'pitch': 0.5, 'left_hand': False, 's': 5.5, 'k': 2.0}`-shaped fields and never `clearance`. [VERIFIED: `screw info nut --preset iso4032:M3 --clearance 0.1` output; src/screw/calc/__init__.py:134-148]

### What the page does with a default (no JS change needed)
```javascript
for (const [name, { input }] of fields) write(input, h.get(name) ?? defaults[name]);
```
and `Number(value) !== Number(defaults[name])` decides whether a field enters the hash. [VERIFIED: src/screw/static/app.js:365,390] `lastTyped` only stores fields whose `defaults[name] === undefined` (app.js:727), so it becomes inert for the nut once a default exists.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Default clearance from forum/blog/vendor figures (reported 0.125-1.3 mm in one thread, "0.1-0.2 mm per side" in blogs) | the project's own printed matrix, rule fixed first | PROJECT.md decision, 2026-10-05 | those figures are **priors only**; `.planning/research/PITFALLS.md` C8 rates them LOW and says no controlled study exists [CITED: .planning/research/PITFALLS.md:252] |
| "Required clearance" (L15 D-01) | one frozen default with a cited run | this phase | a one-way door (D-07) |
| Printability warning from vendor "M5/M6 and up" | threshold constants from run 2 | this phase | the vendor figure never enters the code |

**Deprecated/outdated:** the standing comments listed in Pitfall 9.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Testing each bolt against its five nuts loosest-to-tightest limits wear contamination; printing separate bolts for PAIR-06 removes the steel-nut abrasion confound | Pitfall 3 | If the owner meant the very same 12 bolts, D-14 text is read looser than intended; the wear confound is a design judgement, not measured |
| A2 | Spreading the 3 samples of a cell across plates avoids a plate-level confound | Pitfall 4 | Costs print planning only; harmless if wrong |
| A3 | D-09's "outside M6-M12" is best keyed on `d < 6.0 or d > 12.0` | Pitfall 6, Open Question 3 | Fires less/more than the owner expects; one-line change, no data effect |
| A4 | Run 2 may be pre-registered in the run-1 PR with its clearance "by reference" | Alternatives, Open Question 1 | If the owner wants run-2 predictions informed by run 1, a second pre-registration PR is needed before run-2 prints |
| A5 | FDM facts used as design context (elephant foot on the nut's bed face, overhang of the nut's top countersink, bolt tip overhang when printed head-down) | Pitfall 4, Environment | None affect a value; they are items for the protocol's "profile" section, owner confirms |
| A6 | Two decision entries (L17 default, L18 thresholds) rather than one | Alternatives | Cosmetic; either satisfies SC2/SC5 |
| A7 | A kernel run of `screw pair` at 0.25 on M8 will read `proven` | Pitfall 1 | If not, D-16 cannot be met as written and the phase stops for an owner decision |

## Open Questions

1. **When is run 2 pre-registered?**
   - What we know: D-10 says "a second pre-registered run, after the default is set"; SC1 requires method, predictions and escape clause before the *first print*.
   - What's unclear: whether "pre-registered" for run 2 may share PR A (clearance by reference) or must post-date run 1.
   - Recommendation: one PR A with both protocols, run 2's clearance defined as "the value `bench/print_rules.py` returns from run 1", predictions for M3-M5 written then; the owner confirms. Costs nothing if wrong (a later PR can add a stricter protocol before run 2's prints).
2. **Same 12 matrix bolts into the bought nuts, or 12 more from the same STL?**
   - What we know: D-14 "the matrix's printed nominal bolts (same profile)".
   - What's unclear: wear (Pitfall 3).
   - Recommendation: print 12 additional bolts from the same STLs in the same batch; if the owner insists on the literal bolts, run PAIR-06 first on pristine bolts and say so in the protocol.
3. **How is "outside M6-M12" tested for the D-09 warning?** (Pitfall 6) Recommendation: `d < 6.0 or d > 12.0`.
4. **One decision entry or two?** (Alternatives) Recommendation: L17 (default) then L18 (thresholds).
5. **Should the now-unused required-field machinery (`_req`, the CLI `[required]` branch, the JS comments) be deleted?** Surgical-edit rule says raise, not refactor; recommendation: leave `_req` and the generic CLI/JS branches (the planted-field test still exercises the generic rule) and edit only comments that state a required clearance.
6. **PAIR-07's home.** `REQUIREMENTS.md` has "v1 Requirements" and "v2 Requirements" only; PAIR-07 sits under v2. "Promoted to a v1.x requirement" needs a new `## v1.x Requirements` heading (move the bullet) when D-14 fires; if it does not fire, the record says "not needed" and the v2 bullet stays with that note. The plan must hold both outcomes.
7. **INFO-06 trigger fired** by the first recorded printed test; the roadmap call is the owner's (CONTEXT deferred). Surface it in the phase summary; do not build.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 venv in the main checkout | everything | ✓ | 3.12.15 | — |
| `screw` CLI (`.venv/bin/screw`) | STL export, `screw pair`, presets | ✓ | runs; export and presets verified | — |
| CadQuery/OCP kernel | `screw export`, `screw pair` | ✓ | cadquery 2.8.0 / cadquery-ocp 7.9.3.1.1 (pinned, L06; read from 05 summaries) | — |
| `git`, `gh`, `make pr.land` | pre-registration PR, landing | ✓ (used in Phase 5) | — | — |
| A second worktree venv | PR A worktree (`make venv`, ~1.4 GB, first run ~2 min) | not created | — | reuse by building in the worktree, never point it at the main `.venv` (05-01 rule) |
| FDM printer, filament, calipers-free fit test, store-bought steel nuts M6/M8/M10/M12 (ISO 4032 or DIN 934) | prints and PAIR-06 | owner's | unknown | none: blocks the phase; manual checkpoint |
| The other CLI (Codex) for review | PR A review (HOW_TO_DEVELOP §8) | used in Phase 5 | — | owner decides |

**Missing dependencies with no fallback:** the owner's printer, material and bought nuts (recorded by the owner in the protocol, D-06).
**Cold-start warning:** a fresh venv's first `pytest` run took 122 s for `tests/test_params.py tests/test_pair.py` here (198 passed); later runs were far shorter in Phase 5 (≈14 s). [VERIFIED: ran it this session]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-xdist 3.8.0 + pytest-cov 7.1.0, coverage floor 96 (`fail_under = 96`) [VERIFIED: pyproject.toml, pip list] |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`, markers `grid`, `pair` deselected by `addopts`; import-linter contracts) |
| Quick run command | `make test PYTEST_ARGS="tests/test_print_rules.py tests/test_params.py tests/test_calc.py -q -n0 --no-cov"` (Makefile `test` target; first run in a cold venv is minutes) |
| Full suite command | `make verify` (ruff, mypy --strict, lint-imports, no-fake-done, pytest under the floor); slow tiers `make pair SIZE=M8`, `make grid` stay outside the gate |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAIR-02 | the rule module returns the right default for synthetic records: smallest all-3/3-and-everything-above step; `None` when no step passes; `None` when non-monotone at any size; refuses incomplete/ambiguous/4-sample/duplicate rows | unit | `pytest tests/test_print_rules.py -k default -q -n0 --no-cov` | ❌ Wave 0 |
| PAIR-02 | the committed record's sha256 equals the module pin and the shipped `NutParams.model_fields["clearance"].default` equals `default_from(record)` | unit | `pytest tests/test_print_rules.py -k committed -q -n0 --no-cov` | ❌ Wave 0 (after the owner's record lands) |
| PAIR-02 | the default is one absolute-mm literal for every size; a nut built at any size without `clearance` carries it; a link omitting it rebuilds that value | unit | `pytest tests/test_params.py tests/test_nut.py tests/test_api.py tests/test_cli.py -q -n0 --no-cov` | ✅ exists, must be rewritten (blast radius table) |
| PAIR-02 | the registry has no required field and the parity rules still bite (planted required field fails) | unit | `pytest tests/test_parity.py -k required -q -n0 --no-cov` | ✅ exists, adjust |
| PAIR-02 | a nut outside the measured range carries the D-09 warning on API and CLI identically, with `clearance` typed or omitted, naming the entry | unit/parity | `pytest tests/test_calc.py tests/test_parity.py -k measured -q -n0 --no-cov` | ❌ Wave 0 |
| PAIR-05 | precondition: the kernel verdict of the M8 pair at the default is `proven` | kernel (slow, outside the gate) | `screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8`; JSON recorded in `bench/RESULTS.md` | n/a manual run |
| PAIR-05 | the M8 bolt's counterpart carries `d, pitch, left_hand, s, m` and no clearance; the nut built from it uses the default | unit | `pytest tests/test_calc.py -k counterpart -q -n0 --no-cov` | ✅ exists (`test_following_a_bolts_counterpart_gives_the_nut_row_of_its_size`) |
| PAIR-05 | the printed pair threads by hand | **manual-only** | owner, D-16 | — |
| PAIR-06 | D-14 rule: a size with >= 2 of 3 binds promotes PAIR-07; exactly 1 of 3 does not; `None`/refusal on incomplete data | unit | `pytest tests/test_print_rules.py -k bought -q -n0 --no-cov` | ❌ Wave 0 |
| PAIR-06 | the printed bolts bind or not in a bought nut | **manual-only** | owner | — |
| INFO-04 | below the threshold (either edge, both) both kinds carry the warning naming the edge crossed, the run and the `Lxx`; at and above no warning; a part below still has every row and no 422 | unit | `pytest tests/test_calc.py -k printab -q -n0 --no-cov` | ❌ Wave 0 (after run 2) |
| INFO-04 | `d_min`, `P_min` equal `thresholds_from(record2)`; strict `<` at M6 literals | unit | `pytest tests/test_print_rules.py -k threshold -q -n0 --no-cov` | ❌ Wave 0 |
| INFO-04 | CLI `screw info` and API `/info` print the same warnings for a below-threshold bolt and nut; the page renders them via `info.warnings` only | unit/parity | `pytest tests/test_parity.py -k printab -q -n0 --no-cov`; existing source pins `tests/test_parity.py:559,739` | partly ✅ |
| INFO-04 | a size below the threshold really displays the warning in the page | **manual** (no browser test in the gate; idea `docs/ideas/2026-10-21-browser-test-of-the-page-in-the-gate.md`) | owner at UAT | — |
| protocol integrity | the record template, manifest and tests agree on 60 nuts + 12 bolts (+12 bought-nut bolts) + 9+9 and the file names; the protocol text states the numbers the module reads | unit | `pytest tests/test_print_rules.py -k protocol -q -n0 --no-cov` | ❌ Wave 0 |
| contract | `bench.print_rules` stays kernel-free; `screw.calc.printability` imports nothing from `tables`, `cadquery`, `logging` | import-linter | `make lint-imports` | contract edit in `pyproject.toml` |

### Sampling Rate
- **Per task commit:** the quick command above for the touched modules (the pre-commit hook runs `make verify` anyway; give commits a 600 s timeout as Phase 5 did).
- **Per wave merge:** `make verify`.
- **Phase gate:** `make verify` green, the record's sha256 pinned, the PAIR-05 acceptance recorded by the owner, before `/gsd-verify-work`.

### Manual-only verifications (the physical checkpoints)
| # | Checkpoint | Who | Evidence kept in the repo |
|---|-----------|-----|---------------------------|
| M1 | type print profile (printer, nozzle, material, layer height, slicer profile, orientation, bought-nut brand/plating) and predictions into the protocol before PR A lands | owner | protocol text on `main` |
| M2 | review PR A by the other CLI; land it | owner + Codex | PR #, merge commit |
| M3 | print run 1 (60 nuts + 12 bolts) and fit-test every sample by D-05, in the pre-registered order | owner | `print-run-1.tsv`, sha256 in `bench/RESULTS.md` |
| M4 | PAIR-06: bolts into bought steel nuts, 3 per size | owner | same record |
| M5 | after default is in code: print run 2 (M3-M5, 9+9) and fit-test | owner | `print-run-2.tsv` |
| M6 | D-16: print the fresh M8 pair through the shipped default path, thread by hand | owner | a line in the phase SUMMARY/UAT plus the exported file names and sha256 |
| M7 | glance at the page: a below-threshold part shows the warning | owner | UAT line |

### Wave 0 Gaps
- [ ] `bench/print_rules.py`, `tests/test_print_rules.py` — covers PAIR-02, PAIR-06, INFO-04 rules with synthetic positive/negative controls
- [ ] `bench/print_matrix.py` (matrix as data, manifest writer) and the blank `bench/results/phase-06/print-run-*.tsv`
- [ ] `06-PRINT-PROTOCOL.md`
- [ ] `pyproject.toml`: add `bench.print_rules` (and the matrix data module if kernel-free) to the kernel-free contract; a contract/test that `screw.calc.printability` imports no `tables`/`logging`
- [ ] Framework install: none

## Security Domain

`security_enforcement` is on (absent/true in `.planning/config.json`, ASVS level 1).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no accounts exist (REQUIREMENTS out of scope) |
| V3 Session Management | no | stateless; the URL is the store |
| V4 Access Control | no | — |
| V5 Input Validation | yes | the default is just another pydantic field; `allow_inf_nan=False`, `le=INTERIM_MAX_MM` unchanged; the owner's TSV is parsed with a strict validator that raises on anything unexpected; no `eval`/`pickle` |
| V6 Cryptography | no (integrity only) | stdlib `hashlib.sha256` to pin the record and manifest; nothing hand-rolled |
| V10/V14 Output | yes (minor) | warnings reach the page through `textContent` (`src/screw/static/app.js:404-411`), never `innerHTML`; warning strings are built from validated floats and constants |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Tuning the record or the rule after seeing data to get a default | Tampering / Repudiation | protocol and rule land on `main` first; sha256 pin; re-derivation test; no reprints inside run 1 (D-08) |
| A hand-typed default that disagrees with the record | Tampering | the `make verify` re-derivation test (copy of T-05-01 mitigation) |
| Skip token in a PR title/body that becomes `main`'s commit message | Elevation of privilege | commit-msg hook and `make pr.land` refuse tokens (L08) [CITED: 05-01-PLAN.md T-05-03] |
| Path or content injection via the manifest/record parser | Tampering | fixed paths anchored on the repo root (05-01 deviation 2); parse with `csv`, validate every field |
| `git config` damage from a test that runs `git` under the pre-commit hook | Tampering | the 05-03 incident: delete every `GIT_*` env var before a test touches git [CITED: 05-03-SUMMARY.md] |

## Project Constraints (from CLAUDE.md)

- `make verify` is the gate (ruff, mypy `--strict`, import contracts, unfinished-work scan, pytest); state the command and the result line in the reply; Python 3.12 only; `Any` is never written (L04).
- L02: a printed number is one someone cuts metal to; a value that cannot be computed honestly is a warning and no number. Defaults are absolute mm and never move. Cap and warn, or `422`; never guess.
- A parameter is validated once at the model boundary and trusted afterwards; the thread-maths module (`screw.calc`) never imports `cadquery`; vendor types stop at their boundary; an import-boundary contract lands with each new module.
- Stop and ask on: an architectural claim not in the decision log, a locked decision that looks wrong, an acceptance criterion that cannot be met as written (D-16 at 0.25, Pitfall 1), unverified library behaviour, evidence conflicts, destructive operations, stability-vs-speed trades.
- New non-trivial choices (the L17/L18 entries) are logged as `Lxx` after the human picks among 2-3 options; do not re-litigate logged decisions.
- One concern per commit; Conventional Commits (normal prose); new behaviour ships with its tests; no `TODO`/`pass`/unreachable branches; deliberate cuts are `docs/tech_debt/` items with the owner's sign-off; state before the final reply whether any item was filed and its path.
- Start file-changing work through a gsd entry point; commits wait for the hook (give Bash 600000 ms); user-facing text caveman, code ponytail.
- Comments carry the measurement or constraint that forced the choice (docs/CODING_VALUES.md): the default's and thresholds' comments cite the run id, the record sha256 and the owner's profile.
- Cross-CLI review: whoever wrote the diff does not review it.

## Sources

### Primary (HIGH confidence)
- `src/screw/params.py` (read in full), `src/screw/calc/__init__.py` (read in full), `src/screw/cli.py` (read in full), `src/screw/static/app.js` (lines 20-200, 400-540, grep of 727-753), `src/screw/solid/pair.py` (lines 1-80, 290-372), `src/screw/calc/pair.py:30-60`
- `tests/conftest.py:1-35`, `tests/test_parity.py` (lines 150-260, 335-420, 1035-1085), `tests/test_params.py:60-80`, `tests/test_thread_maths.py:486-526`, `tests/data/pair_expected.tsv` (scripted read of all right/right rows)
- `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-01-PLAN.md`, `05-01-SUMMARY.md`, `05-03-SUMMARY.md`, `05-OWNER-READS.md`, `05-VALIDATION.md`; `.planning/phases/02-thread-spike/02-SPIKE.md` (section shape, Predictions, Escape clause, Results)
- `docs/architecture/decision_log.md` L02, L16; `docs/HOW_TO_DEVELOP.md` §8-9; `Makefile`; `pyproject.toml` (contracts, pytest config); `bench/nut_fine_caps.py` docstring; `bench/RESULTS.md` headings and the M18/pair entries
- CLI runs this session: `screw presets nut|bolt`, `screw export nut|bolt`, `screw info nut --preset iso4032:M3 --clearance 0.1`, `pytest --version`, `pip list`

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` C5, C8 and `.planning/research/SUMMARY.md` (priors on clearance and printable size; rated LOW by the project itself)

### Tertiary (LOW confidence)
- None used as a value. No web search was run: the phase forbids external figures as inputs (PAIR-02, INFO-04) and the CONTEXT confines research priors to the repo's own research files.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, nothing new; versions read from the venv
- Architecture (seams, test blast radius, prior-art pattern): HIGH, read this session
- Pitfalls on process design (wear order, plate confound, D-09 range): MEDIUM, design judgement flagged [ASSUMED], not measurements
- Anything about print outcomes: not researched by design

**Research date:** 2026-10-22
**Valid until:** 30 days, or until the code seams move (`derive()`, `NutParams`, the parity registry rules) or the kernel pair is bumped (a kernel bump is a re-measure event per the 02-SPIKE Environment rule)
