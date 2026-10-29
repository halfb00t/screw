# Phase 7 owner rulings: budget, refusal shape, default cap

Date: 2026-10-29 (the questions were put on 2026-10-28)
Table: `.planning/phases/07-operability-re-sweep/07-BUDGET-TABLE.md`, blob 5ddf7b869a83106c84d2c3e10269332b07c3be52
(`git rev-parse HEAD:.planning/phases/07-operability-re-sweep/07-BUDGET-TABLE.md` at 8b18a07)
Runs: explore 40646117094, spread 40646125666

The owner answered each checkpoint by picking one option of plan 07-10's three. The reply is
quoted as the selection came back. "(Recommended)" is the orchestrator's label on the option, not
part of the ruling.

## B-01: the budget

Reply, verbatim: `c1 (Recommended)`

Ruling: **C1, catalogue-complete** (R13, G10). The orchestrator recommended it because it is the
only candidate that bounds seconds. The other two:
- C3's predicted fine-STL peak, 1.81628e+10 B, is past the 16 GB host.
- C3's rho point, `explore:bolt-d100-p10-n240-right`, has 240 turns, past the L20 wall of 90.

The per-artifact triples (raw bytes, cold build seconds, cgroup peak bytes), as the table prints them:

| artifact | budget (bytes, seconds, peak) |
| --- | --- |
| stl-preview | (55704726.47566052, 34.127968722622484, 1049185338.9620932) |
| stl-fine | (239508059.14804876, 94.42979276577135, 2930457561.336711) |
| step | (9748694.773917168, 15.000925691551677, 422239338.63724077) |

What C1 keeps and refuses, from the same rows:

| artifact | bolt catalogue kept / refused of 294 | nut catalogue kept / refused of 14 | free space admitted / refused by budget / refused by walls | admitted with a non-ok explore reading |
| --- | --- | --- | --- | --- |
| stl-preview | 294 / 0 | 14 / 0 | 103 / 64 / 88 | 5, refused 5 |
| stl-fine | 294 / 0 | 14 / 0 | 96 / 71 / 91 | 3, refused 3 |
| step | 294 / 0 | 14 / 0 | 131 / 36 / 88 | 10, refused 10 |

## B-02: the refusal shape

Reply, verbatim: `over-budget (Recommended)`

Ruling: **over-budget**. One 422 `type`, `over_budget`, covers all three artifacts. Its body
carries `ctx.fields` and `ctx.artifact`, and its text begins with the field names. The published
type `fine_stl_cap` is retired. The orchestrator recommended this because the project has not been
released, so retiring a published type costs little now. L21 lists the new type.

## B-03: how a defaulted value that pushes a part over is capped and warned (D-06)

Reply, verbatim: `part-wide (Recommended)`

Ruling: **part-wide**. When the request does not name them, the cap moves the bolt's
`thread_length` and then `length`, or the nut's `m`. It sets the field to the largest value on its
form step at which every artifact fits. One warning names the field, its default and the capped
value. The info document, the preview, every download and the file name all come from the one
capped part (L02). The cap never moves `d`, `pitch`, `s`, `k`, `clearance`, `head_chamfer` or the
hand. The cap runs at the request boundary (app and CLI), from the same explicit-key set the
conflict rules read.

The table's D-06 evidence under C1 has 4 rows with "pitch: no admitting value". They are
`bolt-d300-p1-n30-right` and `bolt-d300-p1-n30-left`, each at `stl-preview` and at `stl-fine`.
For pitch, this ruling changes nothing: the cap never moves it. The table does not show whether a
shorter defaulted length admits these parts. `bolt-d300-p1-n30-right` is also one of the 20
in-wall parts the build refuses (below).

## Also ruled on 2026-10-28: the in-wall parts the build refuses

07-09 found 20 explore parts that pass the L20 parameter model. Their readings are `refused` with
`BuildError` at every artifact. Reply, verbatim: `File must debt, continue (Recommended)`. Filed as
`docs/tech_debt/active/2026-10-29-in-wall-parts-the-kernel-refuses.md`. This ruling sets no budget
value.
