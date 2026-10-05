# Requirements

Durable, cross-phase requirements — the ones that outlive any single piece of work.
Per-phase discovery and the roadmap belong to gsd, in `.planning/`; this directory holds
what stays true after a phase is archived.

Nothing is written here yet, and nothing should be invented to fill it. Requirements land
here when they are real: when a stated expectation survives a phase and someone would be
wrong to change it without noticing.

What goes where, once there is something to write:

- `functional.md` — what the product must do, phrased as a checkable statement.
- `nfr.md` — performance, memory, portability, reproducibility budgets, with the number
  and how it was measured.
- `errors.md` — the error contract: which conditions refuse, which cap-and-warn, what a
  client can rely on in a `4xx`/`5xx` body.
- `security.md` — the threat model actually being defended against, and what is
  explicitly out of scope.

Where a requirement already exists in another form, cite it rather than copying it. Today
the only one is the error contract's shape — refuse, cap-and-warn, or report no number —
stated in `docs/architecture/decision_log.md` (L02) and not yet exercised by any test.
