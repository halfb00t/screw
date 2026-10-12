---
phase: 04-iso-hex-bolts-and-screws
plan: 01
subsystem: bench
tags: [head-fuse-probe, owner-read, d-03, d-07, d-13, d-14, d-16, poppler, gitignore]

requires:
  - phase: 03-real-helical-thread
    provides: "helical.thread, precise_volume, TESSELLATION, section_area and T_GATE, bench/thread_spike/measure.py (mesh_stl, stl_check)"
provides:
  - "bench/head_fuse.py: the D-03 probe (head prism + shank cylinder + the shipped thread, fused and measured per case)"
  - "bench/RESULTS.md section 'Head fuse probe (Phase 4, D-03)': seven cases, all one valid solid inside T_GATE, zero open edges"
  - "04-OWNER-READS.md: the owner's confirmed D-07 defaults, the permanence acknowledgement, owner copy location and schema, designation forms, rendering route, the owner's preview ruling"
  - ".gitignore: *.pdf and /.standards/ (purchased standards cannot be committed by accident)"
affects: [04-03 (frozen defaults and permanence precondition), 04-04, 04-07, 04-09 (owner copy directory, rendering route, preview ruling)]

plan_head_before: d876dbd777fe2d7e75e47107d8bd39d707aac12e
plan_head_after: 23e5c59f931cfc2214c0548409b1686247dc91a0
actuals:
  tokens: 4200
  tasks: 3
  # Two commits are this plan's own (615fa86, 23e5c59). Plan 04-02 landed three commits between
  # them on the same branch, so `git rev-list --count plan_head_before..HEAD` would read 5 and
  # measure the interleaving, not this plan; the count below is the plan's own commits.
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A probe lives in bench/ as a module with a one-case test, and its record in RESULTS.md says it is a probe and not a bound"
    - "Purchased material stays outside the tree; the repo holds the owner's per-size numbers and the route, never the PDF, a render or the printed layout"

key-files:
  created:
    - bench/head_fuse.py
    - .planning/phases/04-iso-hex-bolts-and-screws/04-OWNER-READS.md
  modified:
    - bench/RESULTS.md
    - tests/test_bench.py
    - .gitignore

key-decisions:
  - "D-07 defaults confirmed by the owner from the purchased copies: d 6.0, pitch 1.0 (ISO 262:2023 first choice, coarse), s 10.0 (nom = max), k 4.0 (nominal), length 20 is a listed M6 length of ISO 4017:2022 Table 1 grade A; permanent: accepted"
  - "Designation prints ASCII 'Hexagon head screw ISO 4017 - M6 x 20' / 'Hexagon head bolt ISO 4014 - M10 x 80', decimal sizes with a comma (M3,5), no left-hand form so the designation is withheld for left-hand parts"
  - "Rendering route (a): Homebrew poppler 26.10.0, pdftoppm, PDFs at /Users/halfb00t/Documents/standards, renders to the session scratch directory only"
  - "Owner ruling 2026-10-11 ('A - 3.'): the on-disk preview PDFs are the same pages as the purchased edition and may serve as the agent's independent second copy for the tables they contain"

requirements-completed: [TABL-04]

coverage:
  - id: D1
    description: "The D-03 head-fuse probe is durable: bench/head_fuse.py plus a RESULTS.md entry with seven cases, each one valid solid inside T_GATE with closed meshes"
    requirement: "TABL-04"
    verification:
      - kind: unit
        ref: "tests/test_bench.py (head_fuse test, M2 x 4 case)"
        status: pass
      - kind: other
        ref: "grep '^## Head fuse probe (Phase 4, D-03)' bench/RESULTS.md and the M20 x 200 row"
        status: pass
    human_judgment: false
  - id: D2
    description: "Purchased standards cannot enter git: .gitignore ignores *.pdf and /.standards/, git status lists no PDF, PNG or TSV"
    requirement: "TABL-04"
    verification:
      - kind: other
        ref: "git check-ignore -v x.pdf .standards/a.pdf; git ls-files '*.pdf' '*.png' '*.tsv' prints nothing"
        status: pass
    human_judgment: false
  - id: D3
    description: "The owner's opening read is on record (confirmed defaults, permanence, owner copy schema and location, designation forms, rendering route proved on one page, preview ruling)"
    requirement: "TABL-04"
    verification: []
    human_judgment: true
    rationale: "The values come from the owner's reading of purchased standards; no test can assert them. Plan 04-09's independent second copy and the table tests are what check the table rows later."

duration: "about 80 min wall from the Task 1 commit, of which about 15 min active in this continuation (the rest is the owner checkpoint)"
completed: 2026-10-11
status: complete
---

# Phase 4 Plan 01: Head fuse probe and the owner's opening read Summary

**The D-03 head-fuse probe is on record (a hex head, shank and the shipped thread fuse to one valid solid inside the volume gate with closed meshes in all seven cases), the owner confirmed the M6 defaults from the purchased ISO 4017:2022 and ISO 262:2023 and accepted their permanence, and purchased PDFs and renders are now kept out of git.**

## Performance

- **Duration:** about 80 min wall from the Task 1 commit (14:35Z) to this one (15:54Z), of which about 15 min active in this continuation; the rest was the owner's checkpoint
- **Tasks:** 3 of 3 (Task 2 was the owner checkpoint, no commit)
- **Files modified:** 5 (two created, three modified)

## Accomplishments

- The probe (`python -m bench.head_fuse`) fuses a hex prism, a plain shank and `helical.thread` per case and records build-and-fuse time, solid count, validity, whole-part and bare-thread volume error, z extent, mesh sizes at both qualities, open edges and the head-plus-shank fine bytes. All seven cases are one valid solid; the whole-part volume error is at most 1.6e-06 against T_GATE 9e-05; every mesh has zero open edges; the head and shank add 1.1 to 26.3 KB to a fine STL of 3.1 to 145 MB. It is recorded as a probe, not a bound, with the head values labelled UNVERIFIED preview readings.
- The owner's opening read: defaults d 6.0, pitch 1.0, s 10.0, k 4.0 confirmed, 20 mm in the M6 series, `permanent: accepted` typed on its own. This is the line plan 04-03's precondition checks.
- The rendering route is proved: poppler installed from the Homebrew formula, page 7 of `ISO-4017-2022.pdf` (printed page 3) rendered to a PNG in the scratch directory and displayed legibly with the Read tool; no value was read off it.
- `.gitignore` ignores `*.pdf` and `/.standards/`; `git status --porcelain` and `git ls-files` list no PDF, PNG or TSV.

## Task Commits

1. **Task 1: Record the D-03 head-fuse probe in bench/RESULTS.md** - `615fa86` (docs, made by the earlier executor)
2. **Task 2: Owner opening read (checkpoint:human-action, blocking-human)** - no commit; answered by the owner 2026-10-11
3. **Task 3: Keep the purchased material out of git, prove the rendering route, record the opening read** - `23e5c59` (chore)

**Plan metadata:** the commit that carries this file (docs: complete plan).

## Files Created/Modified

- `bench/head_fuse.py` - the D-03 probe (Task 1)
- `bench/RESULTS.md` - the `## Head fuse probe (Phase 4, D-03)` entry (Task 1)
- `tests/test_bench.py` - one `head_fuse` test on the M2 x 4 case (Task 1)
- `.gitignore` - `*.pdf` and `/.standards/` with a comment naming D-16 and L13
- `.planning/phases/04-iso-hex-bolts-and-screws/04-OWNER-READS.md` - the owner's opening read

## Decisions Made

- D-07 defaults confirmed and made permanent by the owner (above). Plan 04-03 commits exactly these without asking again.
- Designation form, decimal comma and `none` for left-hand as the owner read them from Clause 7; the tool prints ASCII, the clause's en-dash and multiplication sign are recorded beside it.
- Route (a), owner-chosen; Homebrew formula only, no Python or JS package (threat T-04-SC accepted as planned).
- The owner's preview ruling, recorded verbatim with its date in `04-OWNER-READS.md`.

## Deviations from Plan

### Owner rulings that changed the plan's premise (not code deviations)

**1. [Owner ruling] The on-disk PDFs are previews, and the owner ruled they may serve as the second copy**
- **Found during:** Task 2 checkpoint (orchestrator reading of the PDFs)
- **Issue:** The plan and D-14 assume purchased PDFs that carry every table. The PDFs on disk are 7, 10 and 10 page preview portions; `ISO-4017-2022.pdf` has no Clause 7 body. The owner's Clause 7 text came from screenshots of the full document.
- **Resolution:** the owner ruled (`A - 3.`, 2026-10-11) that the preview pages are the same pages as the purchased edition and may serve as the independent second copy for the tables they contain. Recorded verbatim in `04-OWNER-READS.md`.
- **Tension to surface:** plan 04-01's own prohibition lists "the iTeh previews" as a forbidden source of values, and the rendered page carries an iTeh preview watermark. The owner's ruling is the standing exception and is recorded as such; plan 04-09 and the verifier should read the prohibition through it. The owner's typed copy remains the first copy.

### Auto-fixed Issues

None. The acceptance string `proved on page` was reworded once in `04-OWNER-READS.md` (`Route proved on page 7`) so the literal criterion matches; no behaviour changed.

**Total deviations:** 0 auto-fixed, 1 owner ruling recorded. **Impact:** none on code; the second-copy provenance for plan 04-09 is the preview pages under the ruling.

## Authentication Gates

None.

## Known Stubs

None. No `.py` file in this plan holds a stub or placeholder.

## Threat Flags

None. The only new surface is the `*.pdf` ignore rule and a local Homebrew formula install on the owner's choice (T-04-01, T-04-SC as planned).

## Issues Encountered

- `screw-owner-copy-raw` exists next to the owner copy (three files, mode 600, older drafts as far as the listing shows). It is not part of the owner copy named in the reply, was not read and was left alone.
- `.planning/ui-reviews/` and `web/.DS_Store` stay untracked and are not this plan's.

## Next Phase Readiness

Plan 04-03 can read `Permanence acknowledged:` and `Owner copy directory:` from `04-OWNER-READS.md` and freeze d 6.0, pitch 1.0, s 10.0, k 4.0, thread length from the owner's confirmation. Plan 04-09 reads the rest of the sizes from the owner and uses the rendering route and the preview ruling for the second copy.

## Self-Check: PASSED

- `bench/head_fuse.py`, `bench/RESULTS.md`, `tests/test_bench.py`, `.gitignore` and `04-OWNER-READS.md` exist on disk.
- `615fa86` and `23e5c59` are ancestors of HEAD.
- `make verify` ran green before the Task 3 commit: 871 passed, coverage 96.53% against the 96.0% floor.
- `git status --porcelain` lists no PDF, PNG or TSV.
