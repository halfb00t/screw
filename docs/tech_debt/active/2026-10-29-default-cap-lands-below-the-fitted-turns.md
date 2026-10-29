# The default cap can pick a thread shorter than any turn count the cost model was fitted on

Severity: must
Status: active
Date: 2026-10-29
Source: plan 07-12 (B-03's default cap, `cost.cap_defaults`), found while moving the CLI/API parity
test. Trigger: plan 07-15's runner readings, or before phase 7 closes.
Related files:
- src/screw/calc/cost.py (`cap_defaults`, `predict`)
- bench/results/phase-07/fit.json (the `ln_turns` coefficients)
- tests/test_parity.py (`test_the_cli_and_the_api_print_the_same_document`, the M6 with s 15 case)

## Context
R11 fits `ln_turns` on the bolt's built thread over the pitch. The smallest turn count among the
1247 fitted bolt points is 3 (computed by `bench.oper_fit.fit_points` and `features` over the records
of runs explore 40646117094 and spread 40646125666). `ln_turns` is positive on every bolt model, so
fewer turns always predict a cheaper part, and below 3 turns that is an extrapolation.

The cap takes the largest form-step value at which every artifact fits, so it goes as low as the
prediction lets it. An M6 with only `s` 15 named (s/d 2.5, above the G28 band) is over its preview
budget, and `cost.cap_defaults` at commit dc4b7fd caps its defaulted thread_length from 20 mm to
0.5 mm: half a turn, a bolt with almost no thread, admitted on a prediction no run supports below
3 turns. An explicit thread_length under 3 turns rests on the same extrapolation, but there the user
chose the part; here the cap chooses it.

## Why it matters
A head-dominated part with a tiny thread can cost more than the log-linear fit predicts (the head
and shank add geometry that does not shrink with the thread), so the cap could serve a part over
its budget, and the part it serves may be far from what the user meant to change. The warning names
the capped value, so nothing is silent, but the value rests on an unmeasured range (L02).

## Next step
Ask plan 07-15 to read admitted parts below 3 turns (a capped one among them) at 5 repetitions; if one
reads over its enveloped prediction, the owner rules between a turns floor on the prediction (like
G28's low edge) and a floor on the cap. Revisit when 07-15 reports.
