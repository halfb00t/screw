# Phase 6: Owner rulings for the printed test

Ruled: 2026-10-22

These rulings were taken before any Phase 6 record row existed, so none was chosen for the result it
would give. The owner answered plan 06-02 Task 1 through Claude Code's AskUserQuestion prompt, each
ruling picked from the options the plan offered; the owner added no words of their own. The literal
reply was `r1-a r2-a r3-a r4-a r5-b r6-a r7-a r8-b`. Plan 06-03 writes R1 to R5 into the protocol.

## Rulings

- R1 run-2 pre-registration: r1-a - R1 a: run 2 is pre-registered in PR A with run 1 (its clearance defined as the value the run-1 rule returns; the owner's run-2 predictions written now) - applied by plan 06-03
- R2 bolts for the bought nuts: r2-a - R2 a: 12 more bolts printed from the same matrix STLs, same batch and profile, used only in the bought nuts - moot after R9; never applied
- R3 order of one bolt's five nuts: r3-a - R3 a: loosest to tightest (0.25, 0.2, 0.15, 0.1, 0.05 mm), order recorded per sample - applied by plan 06-03
- R4 plate rule: r4-a - R4 a: sample k of every cell is printed on plate set k (three plate sets); plate recorded per part - applied by plan 06-03
- R5 part that fails to print: r5-b - R5 b: the failed part alone is reprinted from the same STL and profile before any part of its cell is fit-tested, and its note says `reprinted: print failure` (narrows D-08's no-reprint wording: owner ruling) - applied by plan 06-03
- R6 D-09 warning range: r6-a - R6 a: warn when `d < 6.0` or `d > 12.0` (the range of d the matrix spans) - applied by plan 06-07
- R7 decision entries: r7-a - R7 a: L17 for the default after run 1, then L18 for the threshold after run 2 - applied by plans 06-06 and 06-09
- R8 required-field helper: r8-b - R8 b: turn `_req` into the default-carrying helper (renamed `_free`: a float field with a default and no lower bound); keep the generic required-field rule in the CLI, the page and the parity tests - applied by plan 06-06
- R9 bought-nut scope: Defer + strip - "drop PAIR-06" (the owner, in chat with Claude Code, 2026-10-22, after the protocol slots were asked): move PAIR-06 and PAIR-07 to v2/deferred in REQUIREMENTS, remove the bought-nut code, record and tests from the preregistration branch, the protocol section and the 06-05 task; no new Lxx entry - applied by plan 06-03
- R10 run-2 record: accept the existing prints - "b" (the owner, in chat with Claude Code, 2026-10-23, offered (a) re-run run 2 as pre-registered or (b) accept the M2 to M5 parts the owner had already printed informally before the default shipped as the run-2 record; Claude recommended (a)): plan 06-08 skips Task 1 (no `export run-2`, no `manifest-run-2.tsv`, since the printed parts did not come from that export and a manifest committed now would imply they did), resolves Task 2 by the owner's reported results (transcribed by Claude, confirmed by the owner as "correct", 2026-10-23), and runs Task 3 as written; no new Lxx entry - applied by plan 06-08
  - Deviation 1: printed before the default shipped; the parts did not come from `export run-2`; no manifest was committed before printing; the owner did not report where the parts came from.
  - Deviation 2: the owner tested a clearance ladder on M4 and M5 ("passed at 0.1 and 0.15, loose at 0.20 and higher"; below 0.1 they bound after half a turn). Only the 0.15 mm result, the shipped L17 default, is the run-2 record; the other observations are prose in `bench/RESULTS.md` only.
  - Deviation 3: M3 "too small for the printer to print thread". The record has only pass and bind, so a part whose thread did not print is recorded `bind`, turns `0`, note `thread did not print`. M2 was also printed, is outside the record, and is prose only.
  - Deviation 4: 3 samples per size, each (size, sample) group on its own bed labelled M3-1 to M5-3 (like run 1); the dates were not reported by the owner.

R1 was not b, so no plan insertion before 06-08 is needed. R8 was not c, so no `docs/ideas/` item and no
`docs/ideas/INDEX.md` row were written.
