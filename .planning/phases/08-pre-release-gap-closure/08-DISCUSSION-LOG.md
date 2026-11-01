# Phase 8: Pre-release Gap Closure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md. This log keeps the alternatives that were considered.

**Date:** 2026-11-01
**Phase:** 08-pre-release-gap-closure
**Areas discussed:** In-wall fix route, CLI build deadline, head_chamfer badge, Typed-default parity

---

## In-wall fix route

| Question | Options | Selected |
|----------|---------|----------|
| Fix route | Option 2 with guard fallback; Guard only; Option 2 + guard | Option 2 + guard |
| Where accuracy applies | Only above a d / pitch threshold; Everywhere | Above threshold |
| Platform | Runner via hand dispatch; Local linux/amd64 container | Runner via hand dispatch |
| Proof bar | Named grid with residual logged; Zero build_error in grid only; Pre-kernel catch-all | Named grid, residual logged |
| Threshold choice | From data, below every catalogue row; Per kind; You decide | From data, below every catalogue row |
| Cost cover | Re-sweep affected parts and widen envelope; Full re-sweep | Re-sweep affected parts |
| Guard | Built turns per d band; Tighter d / pitch wall in bands; Only if residual exists | Built turns per d band |
| Island (q7) below the M20 rows (q8) | Per kind thresholds; Island by guard; Stop and show data | Per kind thresholds |

**Notes:** The conflict was raised after the threshold answer. The nut island at d / pitch 7 lies
below the M20 coarse rows at 8, so "below every catalogue row" cannot hold for the nut. The owner
chose per-kind thresholds: the nut goes to 7 or below, and the bolt goes above 8 if the data allows.

---

## CLI build deadline

| Option | Selected |
|--------|----------|
| Log Lxx: unbounded by design | ✓ |
| Enforce the same timeout in a child process | |
| Enforce it, with a `--timeout` override | |

---

## head_chamfer badge

| Option | Selected |
|--------|----------|
| Amend TABL-06 to agree with L19 | ✓ |
| Change the code so the angle flips the badge (supersede part of L19) | |

---

## Typed-default parity

| Option | Selected |
|--------|----------|
| The web sends touched fields | ✓ |
| The API and CLI treat a default-equal value as unset | |
| Log an Lxx and keep the difference | |

## Claude's Discretion
- The guard's error type name and wording. The code shape of the threshold. The exact denser nut
  grid. When the web resets "touched".

## Deferred Ideas
- A CLI `--timeout` flag.
- INT-04 and INT-05, which are info findings.
