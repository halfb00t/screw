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

## B-03 clarification: a named thread_length and the length cap (2026-10-29)

Source: the 07-12 executor's checkpoint. B-03 says the cap moves the bolt's `thread_length` and then
`length` "when the request does not name them", truth 1 of plan 07-12 caps each unnamed field, and
the plan's Task 1 behaviour 3 says a part with `thread_length` named returns uncapped. Read field by
field with no guard, a named `thread_length` could be shortened by a `length` cap.

Evidence: bolt d 30, s 48, k 18, pitch at its default 1, refused at `stl-preview` and `stl-fine`.
The figures are `cost.fits` at commit bf7b173 (fit.json, runs explore 40646117094 and spread
40646125666), scanned down each field's 0.5 mm form step; plan 07-12's tests re-derive them through
`cost.cap_defaults`.

| request | per field, no guard | per field, guard (ruled) | only when neither is named |
| --- | --- | --- | --- |
| d, s, k | thread_length 20 to 6.5 | thread_length 20 to 6.5 | thread_length 20 to 6.5 |
| + thread_length 20 | length 20 to 6, a 6 mm thread built for a named 20 | no cap, 422 per artifact | no cap, 422 |
| + thread_length 10 | length 20 to 6, a 6 mm thread built for a named 10 | no cap (no length 10 to 19.5 fits), 422 | no cap, 422 |
| + length 60 | thread_length 20 to 6.5 | thread_length 20 to 6.5 | no cap, 422 |

The owner's replies, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling):

1. "A: per field, guard (Recommended)"
2. "OK, serve it capped (Recommended)"

Ruling 1: each field the request does not name is capped on its own, the bolt's `thread_length`
first, then `length`. `length` is never capped below a named `thread_length`, so the built thread
stays what the user named. When no admissible value is left, the answer is B-02's `over_budget` 422.
Plan 07-12's behaviour 3 holds as written.

Ruling 2: a bolt with only `d` 5 named, whose preview G28 ruling 5 refuses (k/d 0.8, above the
band), is served with its defaulted `thread_length` capped (16.5 mm by the same scan) and a warning,
not refused at the preview. Its prediction is unchanged; the cap is applied to the request's part.

## B-03 second clarification: the cap never goes below the fitted minimum turns (2026-10-29)

Source: the orchestrator, from the debt item
`docs/tech_debt/resolved/2026-10-29-default-cap-lands-below-the-fitted-turns.md` (filed 6cb928b).
The question, as put: the B-03 cap can cut a defaulted thread to almost nothing. An M6 with only
s=15 named gets thread_length 20 -> 0.5 mm, which is 0.5 turns. The fitted bolt points start at 3
turns.

Evidence: `cost.cap_defaults` at 97600d7.

| request | cap result |
| --- | --- |
| `BoltParams(s=15)`, explicit {s} | thread_length 0.5, length 20, 0.5 turns, capped for stl-preview |
| `BoltParams(d=5)`, explicit {d} | thread_length 16.5, 16.5 turns |
| `BoltParams(d=30, s=48, k=18)`, explicit {d, s, k} | thread_length 6.5, 6.5 turns |

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "Floor at fitted min turns (Recommended)"

Ruling: the floor is the smallest built-thread turn count over the fitted bolt points of R11 (runs
explore 40646117094 and spread 40646125666), `calc.thread.built_thread_length(thread_length,
length) / pitch` with each point's omitted fields at their defaults. `bench.oper_fit` computes it
and `emit-constants` emits it into `calc/cost.py` as `MIN_FITTED_TURNS`; it is never typed (L02).
The bolt cap, `thread_length` first and then `length`, with ruling 1's guard, only takes values
whose built turns are at or above the floor. When no such value fits every artifact, the answer is
B-02's `over_budget` 422, as for any part no cap can save. The nut `m` cap is unchanged: the nut
has no turns feature, and G28 holds m/d at its low edge.

Outcome at the implementing commit: the emitted floor is 2.9999999999999996 (the n3 points at pitch
0.1). The d 5 and d 30, s 48, k 18 caps stay at 16.5 and 6.5. The M6 with only s=15 named is no
longer capped: no value of thread_length or length at or above the floor fits, so its preview
download is the `over_budget` 422 and its fine STL and STEP are served.

## B-02 and B-03: a bolt below the fitted turns is refused at every artifact (2026-10-30, G30)

Source: the G28/G29 stop of plan 07-15 (`07-GAP-RULINGS.md`, G30). In outband run 40909768713
the G29 bolt `turns-below-iso4017:M2x4` (thread_length 1.0, 2.5 built turns) read 1446684 bytes
at the fine STL in all 5 repetitions, 1.3116 x its enveloped prediction. The fit has no point below
`cost.MIN_FITTED_TURNS`, so no reading supports a prediction there.

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "1: widen nuts, guard G29 (Recommended)".

Ruling: a bolt whose built thread, `calc.thread.built_thread_length(thread_length, length) /
pitch`, has fewer turns than `MIN_FITTED_TURNS` is refused before any build at every artifact. The
refusal is B-02's `over_budget` 422; it names the fields that set the turns, pitch, length and
thread_length, in `msg` and in `ctx.fields`, and it prints no figure (L02). B-01 holds: none of
the 294 bolt catalogue rows is below the floor, and a test pins it. B-03's second clarification is
unchanged: the cap never takes a value below the floor, so it cannot cap a part into this refusal.
The bolt stl-fine bytes e is not widened. The nut stl-fine seconds and peak e widen from the nut
out-of-band readings, re-derived by committed code (G30).

### G30 clarification: the turns refusal answers before the builder's own check (2026-10-30)

Source: the 07-15 executor's report. Since bccb6f3, a bolt too short to build at all (a length of
1e-8 mm, and parts like it) also has fewer than `MIN_FITTED_TURNS` turns. It now gets the
`over_budget` 422 (CLI exit 2) instead of `build_error` (CLI exit 1). The 422 still names the length,
and no file is written either way. Six tests were re-pinned to this.

The owner's reply, verbatim (the label "(Recommended)" is the orchestrator's, not part of the
ruling): "Keep over_budget (Recommended)".

Ruling: the turns refusal keeps its place, ahead of the builder's check. There is one rule with no
exception, and G30's "at every artifact" covers these parts.
