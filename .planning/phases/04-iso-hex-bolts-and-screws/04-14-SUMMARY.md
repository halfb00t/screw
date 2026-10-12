---
phase: 04-iso-hex-bolts-and-screws
plan: 14
subsystem: docs
tags: [decision-log, l13, l12-supersession, overview, requirements, roadmap, interim-bounds, d-24, d-25]

requires:
  - phase: 04-iso-hex-bolts-and-screws
    provides: "04-01 to 04-13: the probe, the owner reads, the caps, the gates, the tables, the catalogue, the page, and the pinned numbers L13 cites"
provides:
  - "docs/architecture/decision_log.md L13: every Phase 4 choice later phases build on, each with its source; it supersedes L12's cap list and records the owner's D-25 exception to L02's model-level 422"
  - "L12's Caps paragraph: measured quantity corrected (fine raw STL plus gzip level-1 copy over the INTERIM 64 MiB budget) and one pointer sentence to L13; rules and cap list untouched"
  - "docs/architecture/overview.md: the Phase 4 bolt, the tables row with the licence stance, the preset route and CLI"
  - "REQUIREMENTS TYPE-01, THRD-05, TABL-04, INFO-05; ROADMAP SC1, SC2 and Phase 5's precondition; STATE blockers; README status; the interim-bounds rows"
affects: [Phase 5 (nut builds on L13's document shape, tables and fields), Phase 7 (re-sweep of the caps, the refused-preset count and the preview STL)]

actuals:
  tokens: 10100
  tasks: 2
  commits: 2

plan_head_before: 138952695b27f89eb3ec1e2b09c4f2584bd8af23
plan_head_after: e3760249076cb0b1bfd0382057dcfe5f1e516426
commits: 2

tech-stack:
  added: []
  patterns:
    - "A superseding decision entry corrects the superseded one's factual claim and adds a pointer in the same commit, and leaves its rules and values alone"

key-files:
  created: []
  modified:
    - docs/architecture/decision_log.md
    - docs/architecture/overview.md
    - README.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md

key-decisions:
  - "L13 describes the full tables as generated from the purchased PDFs' text layer under the owner's ruling B (2026-10-12), not as owner-typed, and says the double entry catches a reading slip and not an error in the PDFs"
  - "L13 describes the badge as 04-13 shipped it (basis is the last exact match, not only the last pick) and cites 01-UI-SPEC.md rule 33"
  - "The preset id grammar is recorded as shipped: the size keeps its printed capital M and ids are case-sensitive (04-07), not CONTEXT D-11's lowercase"

requirements-completed: []  # TYPE-01 and TABL-04 are this plan's ids; traceability is reconciled by phase.complete, not ticked here

coverage:
  - id: D1
    description: "L13 holds the Phase 4 choices with their sources, supersedes L12's cap list in those words, and states the owner's D-25 acceptance of direct construction"
    requirement: TYPE-01
    verification:
      - kind: other
        ref: "plan Task 1 greps: ^## L13, D-25, Head fuse probe, supersedes L12's cap list, M10 72, M8 left-hand, gzip"
        status: pass
    human_judgment: true
    rationale: "Whether each paragraph states the decision and its source accurately is prose; a reader judges it against the summaries it cites"
  - id: D2
    description: "L12 keeps its original cap list and rules and gains the corrected measured quantity and a pointer to L13, in the same commit as L13"
    verification:
      - kind: other
        ref: "awk range ## L12 to ## L13: contains 'M8 67.5 mm, M10 56', 'gzip', 'L13'; git show d469e1d"
        status: pass
    human_judgment: false
  - id: D3
    description: "The overview maps the bolt, the tables row and contracts 6 and 7"
    verification:
      - kind: other
        ref: "grep 'Tables are a leaf' and 'The parameters never consult a table' docs/architecture/overview.md"
        status: pass
    human_judgment: false
  - id: D4
    description: "REQUIREMENTS, ROADMAP, STATE, README and the interim-bounds item say what Phase 4 shipped and deferred"
    requirement: TABL-04
    verification:
      - kind: other
        ref: "plan Task 2 acceptance greps (TYPE-01 and THRD-05, SC1 D-02, INFO-05 pinned sentence, SC2 pinned sentence, STATE ISO 4753 and D-18, calc/thread.py in the debt item)"
        status: pass
      - kind: integration
        ref: "make test PYTEST_ARGS=\"tests/test_cli.py -q -n0 --no-cov -k readme\" (1 passed)"
        status: pass
    human_judgment: false

duration: about 15 min
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 14: L13 and the records of what Phase 4 shipped Summary

**L13 records the ISO hex bolt and screw decisions with their sources, supersedes L12's cap list (L12 only corrected and pointed), and the overview, requirements, roadmap, state, README and interim-bounds debt now say what the phase shipped and deferred.**

## Performance

- **Duration:** about 15 min (ledger written 04:03Z, last commit 04:08Z, reading before that)
- **Tasks:** 2
- **Files modified:** 7 (docs only; no code)

## Accomplishments

- **L13** (`d469e1d`), in L12's shape (date, who decided, every figure with its run, test or summary): Geometry (plain prism, whole-part closed form, the D-03 probe cited as a probe, the deferred ends and ISO 4753, the standing warning as shipped, the bare-thread gate with Alert 5's numbers and its positive control), Fields and defaults (the owner's read of 2026-10-11 and `permanent: accepted`), thread_length (D-08, D-27, the request-boundary 422 and why `model_fields_set` cannot carry it, and the owner's D-25 exception stated as a ruling), Presets (route, id grammar as shipped, CLI, three selects, the badge as 04-13 shipped it, the 294-row catalogue), Tables (rows, double entry told as it was done, the UNVERIFIED gate, the licence stance, contracts 6 and 7 and their runtime control), Info document (groups, designation, preset, notes, the no-row warning, unrounded display, the DIN note's two web sources at MEDIUM confidence), Caps (`supersedes L12's cap list`; the 13 hand-keyed rows; run `2026-10-08-a-grid`; both caps on the built thread; the pinned count of 62 refused ISO 4017 presets and none of ISO 4014), Head rule (`s > d` as policy, with the probe that shows it is not a kernel necessity), then Reason and Reversibility.
- **L12** in the same commit: the Caps paragraph keeps its rule text and its original cap list (`M8 67.5 mm, M10 56 ...`); the parenthesis now says what was measured (right-hand rods, the fine raw STL plus its gzip level-1 copy, over the INTERIM 64 MiB budget) and one sentence at the paragraph's end points to L13. No other L12 text changed; the "Standing warning (D-06)" paragraph stays as Phase 3 history.
- **Overview:** the Main pieces paragraph describes the Phase 4 bolt; the `tables` row names ISO 262, 4014 and 4017 for M2 to M20, the leaf rule and the licence stance in one sentence; `params`, `calc`, `app` and `cli` rows mention the conflict rule, the catalogue document, `GET /api/presets` and `presets` / `--preset`. Contracts 6 and 7 and the nine-in-force list were already there (04-07, 04-08).
- **Records** (`e376024`): TYPE-01 loses "chamfered point, under-head fillet" and points to THRD-05; THRD-05 names the fillet; TABL-04's list adds ISO 4753 (Phase 5); INFO-05 is the pinned D-20 sentence; ROADMAP SC1 carries `D-02`, SC2 names `screw.params` and `screw.calc.thread`, Phase 5's precondition adds ISO 4753; STATE's TABL-04 line, ISO 4753 line and coarse-pitch line (D-18) are updated; the README status is the pinned line and a paragraph; the interim-bounds item has the `MIN_TAIL_MM` location (and corrected line ranges for the three calc/thread.py rows), the hand-keyed `FINE_STL_ROWS` row with the head and shank caveat and the 62-preset count, the `INTERIM_MAX_MM` row on `s`, `k` and `thread_length` with `d` = 1e5 unreachable, and a new M20 x 200 preview-STL row (Phase 7, OPER-02).

## Task Commits

1. **Task 1: L13, L12's pointer to it, and the architecture overview** - `d469e1d` (docs)
2. **Task 2: The requirement, roadmap, state and debt records the phase changes** - `e376024` (docs)

**Plan metadata:** the docs commit that carries this file and the STATE and ROADMAP progress.

## Verification

- `make verify` on HEAD `e376024`: ruff, mypy `--strict`, import contracts, unfinished-work scan, pytest: **2619 passed**, coverage 97.57% (floor 96.0%), exit 0. The pre-commit hook ran the same gate on both commits and passed.
- Task 1 greps (L13, D-25, Head fuse probe, `supersedes L12's cap list`, `M10 72`, `M8 left-hand`, `gzip`; L12 keeps `M8 67.5 mm, M10 56`, gains `gzip` and `L13`; overview contract names) all pass.
- Task 2 greps and the pinned INFO-05 and SC2 sentences pass; `make test PYTEST_ARGS="tests/test_cli.py -q -n0 --no-cov -k readme"`: 1 passed.

## Deviations from Plan

### Judgement calls and notes (no rule deviation)

- **Commit trailer.** The dispatch note named `Claude Fable 5.1`; the attribution this session runs under names `Claude Sonnet 5.5`, which is the model that wrote the commits, so both carry that one (as 04-09 and 04-10 did). A trailer naming another model would be false.
- **The overview was already partly done.** Plans 04-07 and 04-08 had added the `tables` row, contracts 6 and 7, "Nine are in force" and the `calc/presets.py` sentence (their own deviations). Task 1's overview diff is therefore the Main pieces paragraph and the refinements above; the contract list needed no change.
- **L13 states two limits of what the phase can claim.** The full tables are generated, not owner-typed (ruling B), so the double entry cannot catch an error in the PDFs themselves; and the grade note's wording for ISO 4014 is the ISO 4017 wording with the standard substituted, the ISO 4014 clause not having been read for it (04-11). Both are recorded where a reader of L13 will see them.
- **L13 records the id grammar as shipped** (printed capital `M`, case-sensitive) and says CONTEXT D-11 wrote lowercase; and records the badge basis as 04-13 shipped it (broader than "after a pick").
- **L13 is long** (about 250 lines against L12's 105) because the plan asked for every Phase 4 choice with its source in one entry; it is in L12's paragraph-per-topic shape.
- **Traceability statuses untouched.** `requirements.mark-complete` was not called; the 04-09 ticks stay, and TYPE-01, THRD-03 and INFO-05 stay pending for `phase.complete`.

### Auto-fixed Issues

None - plan executed as written.

## Authentication Gates

None.

## Known Stubs

None. No stub, placeholder or skipped test; nothing was written to `.planning/WINDOWS.md`.

## Threat Flags

None. Docs only; no endpoint, auth path, file access or schema change. T-04-23 (an undocumented locked choice) is mitigated: L13 records the D-xx choices with their sources and the overview lists the contracts.

## Issues Encountered

- `gsd_run` was not defined in the shell, so state updates call `gsd-tools.cjs` through `node`.
- Out of scope, for the verifier: the `INTERIM_MAX_MM` comment in `src/screw/params.py` (lines 18-31) still says "the largest diameter or length a request may ask for", while the bound is also on `s`, `k` and `thread_length` since 04-03 and 04-04. It is a code comment and this plan is docs only; the debt row now says it correctly.
- Out of scope: Phase 5 SC1 says "the nut thread and the bolt tip carry lead-in chamfers" and does not mention the under-head fillet that THRD-05 now carries; the plan listed no edit there.
- Filed no tech-debt or idea item.

## Next Phase Readiness

Phase 4 has no plan left. What remains is the phase's own closing work: `phase.complete` reconciling the traceability table, the verifier, and the end-of-phase browser UAT 04-13 listed (nothing in the page was seen on screen).

## Self-Check: PASSED

- FOUND: `docs/architecture/decision_log.md` has `## L13` (line 539) and L12's original cap list; `docs/architecture/overview.md`, `README.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` and the interim-bounds item are modified as listed.
- FOUND: commits `d469e1d` and `e376024` are ancestors of HEAD (`git rev-list --count 138952695b27f89eb3ec1e2b09c4f2584bd8af23..HEAD` is 2 before this summary's commit).
- `make verify` exit 0, 2619 passed, coverage 97.57%.

---
*Phase: 04-iso-hex-bolts-and-screws*
*Completed: 2026-10-12*
