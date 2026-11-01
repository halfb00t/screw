# Phase 7: Operability Re-sweep - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-26
**Phase:** 07-operability-re-sweep
**Areas discussed:** Measurement host + size, Shrinking the allowed space, Timeout policy, Full-grid CI cadence

---

## Measurement host + size

| Option | Description | Selected |
|--------|-------------|----------|
| GH ubuntu-latest | Native amd64, free, re-runnable by dispatch, and the same host class as the CI gate; noisy, so record the runner spec | ✓ |
| Own linux/amd64 box | Quieter and deploy-like, but not re-runnable by others; CI may be slower than the box | |
| Both: VM sets, CI checks | Most rigorous, and needs a box | |

| Option | Description | Selected |
|--------|-------------|----------|
| Runner-sized: 4 vCPU / 16 GB | mem_limit = measured peak × workers + headroom, under 16 GB | ✓ |
| Small VPS: 2 vCPU / 4 GB | Keep 4g and shrink the space hard (one in-cap fine STL peaked at 7.9 GB) | |
| No target; measure only | Record the peaks; the host fit stays open | |

| Option | Description | Selected |
|--------|-------------|----------|
| Sweep 1-2-3, pick by p95 | Best p95 that fits 16 GB, one core left for uvicorn and gzip | ✓ |
| Fix at 2 | spur's number, carried unmeasured | |

| Option | Description | Selected |
|--------|-------------|----------|
| 5 reps, median + max | Bounds set from the max; CPU model recorded | ✓ |
| 3 reps | Cheaper, weaker | |
| You decide | Size the samples from the variance | |

**User's choice:** all four recommended options.

---

## Shrinking the allowed space

| Option | Description | Selected |
|--------|-------------|----------|
| Measured cost model | Kernel-free predictor in calc, refusing before the pool; generalises FINE_STL_ROWS | ✓ |
| Per-field ceilings | Simple, but the worst corner dictates every axis | |
| Catalogue grid + small custom box | Easiest to sweep, least custom freedom | |

| Option | Description | Selected |
|--------|-------------|----------|
| Per-artifact refusal | Info always works; preview, fine STL and STEP each judged | ✓ |
| Whole-part refusal | One over-budget artifact refuses the part | |

| Option | Description | Selected |
|--------|-------------|----------|
| Conservative envelope | Prediction × (1 + worst under-prediction); CI boundary and random builds; a miss fails | ✓ |
| Exact fit, CI catches | More parts admitted, and misses reach users | |

| Option | Description | Selected |
|--------|-------------|----------|
| Subsumed by the model | FINE_STL_ROWS retired; MAX_TURNS and 1e5 kept as measured outer walls only | ✓ |
| Keep all, add model | Two overlapping rules | |

**User's choice:** all four recommended options.

---

## Timeout policy

| Option | Description | Selected |
|--------|-------------|----------|
| One per artifact | Preview, fine STL and STEP each at their measured worst × margin | ✓ |
| One global | Slowest artifact sets it | |

| Option | Description | Selected |
|--------|-------------|----------|
| 2× worst, at chosen workers | All workers busy; factor in the Lxx | ✓ |
| 1.5× worst | Tighter | |
| You decide from the variance | max / median ratio | |

| Option | Description | Selected |
|--------|-------------|----------|
| 503 + log as model miss | Backstop; no cache, no partial file | ✓ |
| 422 retroactively | Reads as a rule but is host-dependent | |

| Option | Description | Selected |
|--------|-------------|----------|
| Derive Retry-After from queue | Median build × queue depth | ✓ |
| Keep 5 s as a hint | Documented as a hint | |

**User's choice:** all four recommended options.

---

## Full-grid CI cadence

| Option | Description | Selected |
|--------|-------------|----------|
| Split tiers | Required boundary set in ci.yml (about 10 min), plus a weekly/dispatch full tier | ✓ |
| Full grid required on PRs | 60+ min merge wait | |
| Weekly only | A loosened model lands unproven | |

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, paths filter | The full tier runs on PRs touching the model, budgets, tessellation or builder; pr.land refuses while it is red | ✓ |
| No, weekly is enough | pr_land unchanged | |

**User's choice:** both recommended options.

---

## Claude's Discretion

- Gzip level, minimum_size, bytes-cache budget, solid cache, queue depth, SCREW_WORKERS, HEALTHCHECK, tmpfs, `_release_arenas`: measured on the runner, cited in an Lxx.
- Tessellation: kept unless the sweep gives a reason.
- UI debounce: relabelled as a UI choice.
- The cost model's form and features, and the boundary-set size and seed.

## Deferred Ideas

- Sizing for a smaller deploy box once a deploy target exists.
