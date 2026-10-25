---
phase: 06-printed-pair-acceptance
plan: 10
subsystem: bench
tags: [acceptance, printed-pair, pair-05, d-16, d-05, kernel-proof]

requires:
  - phase: 06-printed-pair-acceptance
    provides: L17 clearance default 0.15 mm, the print protocol, the acceptance export in bench/print_matrix.py (06-05, 06-06), L18 threshold (06-09)
provides:
  - the kernel verdict `proven` for the M8 pair at the shipped default, recorded verbatim
  - bench/results/phase-06/manifest-acceptance.tsv (2 rows: bolt and nut, bytes, sha256)
  - the "Acceptance pair (Phase 6, D-16)" entry in bench/RESULTS.md with the page digests and the owner's pass
  - PAIR-05 ticked with its evidence
affects: [phase 6 verification, release acceptance]

requirements-completed: [PAIR-05]

actuals:
  tokens: 12000
  tasks: 3
  commits: 2

key-files:
  created:
    - bench/results/phase-06/manifest-acceptance.tsv
  modified:
    - bench/RESULTS.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "No new decision. The shipped default (L17, 0.15 mm) was accepted unchanged: the page path gave the pre-registered default-path files and the owner's print passed under D-05."

coverage:
  - id: D1
    description: "Kernel verdict at the shipped default for M8 (d 8, pitch 1.25, s 13, m 6.8) is proven, exit 0, JSON recorded verbatim before the print"
    requirement: "PAIR-05"
    verification:
      - kind: integration
        ref: "bench/RESULTS.md '## Acceptance pair (Phase 6, D-16)' (CLI run, exit 0, verdict proven, 5.44 engagement turns)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The owner's page downloads equal the pre-registered CLI default-path exports in name, bytes and sha256 (digests recomputed by this agent)"
    requirement: "PAIR-05"
    verification:
      - kind: integration
        ref: "shasum -a 256 and stat over ~/Downloads/3dprint vs bench/results/phase-06/manifest-acceptance.tsv"
        status: pass
    human_judgment: false
  - id: D3
    description: "The owner printed the fresh pair with the protocol's profile on 2026-10-23 at 21:53 and recorded pass: the nut threads onto the bolt by hand (D-05)"
    requirement: "PAIR-05"
    verification:
      - kind: manual
        ref: "bench/RESULTS.md acceptance entry, owner's reply quoted"
        status: pass
    human_judgment: true

duration: "about 20min of agent time, most of it waiting on make verify"
completed: 2026-10-23
status: complete
plan_head_before: de25e58c2cc3784365b43800d9c4fdf96d24a412
plan_head_after: 4632b6151bf042855edd527082b0bf262ea6b27c
---

# Phase 6 Plan 10: The printed pair acceptance Summary

**The owner's fresh ISO 4017 M8 x 16 bolt and its Matching nut at the shipped 0.15 mm default, downloaded from the page and byte-identical to the pre-registered CLI exports, threaded together by hand after printing; the kernel had read `proven` first. PAIR-05 is ticked.**

## Accomplishments

- Task 1 (tracer, commit `a182f27`, a prior agent run): `screw pair nut --d 8 --pitch 1.25 --s 13 --m 6.8` with no clearance exited 0 with `"verdict": "proven"` (clearance 0.15, 5.44 engagement turns, control volume 25.1308 against three offset readings at 25.1308 and three zero-solid readings at whole pitch). The pre-registered acceptance pair was exported through the CLI default path and pinned in `manifest-acceptance.tsv`.
- Task 2 (owner checkpoint): the owner took the pair through the page, printed it and replied "Path: ~/Downloads/3dprint / Print date: 21:53 10.23.2026 / Result: pass". No turns or notes beyond `pass`.
- Task 3 (commit `4632b61`): recomputed `shasum -a 256` and `stat` size of both files in `~/Downloads/3dprint`; name, bytes and sha256 equal the manifest for both. The acceptance entry now carries the page digests, the equality result, the print date and the owner's quoted pass. PAIR-05 is `[x]` with an evidence sentence and the traceability row is `Complete`. `make verify`: 3550 passed in 214.48s.
- The dev server started for Task 2 was stopped; `curl` on `/api/health` now fails and no `make serve` or uvicorn process is left.

## Task Commits

1. **Task 1 (tracer): kernel proof at the default and the acceptance export** - `a182f27` docs(06): record the acceptance pair's kernel verdict and exports
2. **Task 2: owner's page path, print and hand test** - checkpoint, no commit
3. **Task 3: page digests vs manifest, owner's result, PAIR-05** - `4632b61` docs(06): record the owner's acceptance of the printed M8 pair

`commits: 2` is measured from the ledger base `de25e58`.

## Deviations from Plan

None - plan executed as written. Notes:

- The owner gave a directory, not two file paths. The plan's Task 2 asks for two existing STL paths; the two files in that directory are the only STLs and were resolved there and recorded in the entry with that remark.
- The owner's `pass` is a hand judgement under D-05. No mechanical check can confirm it (flagged edge in the plan: a pair that frees after a first run-in or a quarter turn). The owner reported no such qualification.
- The entry says the print used "the protocol's one profile" only through the owner's reply and the plan's instructions; the reply did not restate the profile. Nothing was asked beyond the reply.

## Issues Encountered

None.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. Docs and a manifest only. T-06-20 mitigated: the page downloads' digests were compared with the pre-registered exports and the comparison is recorded. T-06-21 mitigated: the verdict is recorded verbatim, and no rule, constant, clearance or table was changed.

## Ideas and debt

None filed by this plan.

## Open for the owner

- INFO-06 (print hints): its trigger ("the first printed test recorded") fired in 06-05 and is noted in REQUIREMENTS.md by 06-06; placing it on the roadmap is the owner's call. Nothing here built it.
- Remove the pre-registration worktrees and branches when the owner is ready: `/Users/half/git/halfb00t/screw/.claude/worktrees/phase-06-preregistration` (branch `gsd/phase-06-preregistration`) and the older `phase-05-preregistration` (branch `gsd/phase-05-preregistration`). Not touched here (destructive; owner's call).
- End-of-phase UAT items collected from 06-09 (the page check of the printability warning) remain for `/gsd-verify-work`.
- Open debt `2026-10-21-screw-pair-exit-codes-collide-with-failure-exits.md` unchanged; the verdict JSON was the discriminator here.

## Self-Check: PASSED

`bench/results/phase-06/manifest-acceptance.tsv` exists with one bolt and one nut row; `bench/RESULTS.md` holds one `## Acceptance pair (Phase 6, D-16)` heading and one `Owner's fit test: pass` line; `a182f27` and `4632b61` are ancestors of HEAD; PAIR-05 is `[x]` once in `.planning/REQUIREMENTS.md`.
