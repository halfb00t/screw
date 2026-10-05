# Phase 1: Runtime Port and Walking Skeleton - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-05
**Phase:** 1-Runtime Port and Walking Skeleton
**Areas discussed:** Interim runtime bounds, Skeleton shape + frozen defaults, API paths / kind selector / parity proof, Walling `main` and the landing flow

---

## Procedural: branch before discussion

| Option | Description | Selected |
|--------|-------------|----------|
| Cut `gsd/phase-01-runtime-port-and-walking-skeleton` now | Per HOW_TO_DEVELOP §3, so planning commits do not land on `main` | ✓ |
| Stay on `main` | Planning docs commit to `main` | |

**Notes:** `origin/main` was at `46315f3`; local `main` at `1d4bac1` (5 unpushed planning commits). The branch was cut from `origin/main` and fast-forwarded to local `main`; upstream unset. `main` pushed later in the session (see Walling `main`, Q3).

---

## Interim runtime bounds

| Option | Description | Selected |
|--------|-------------|----------|
| spur's figures, labelled interim | Timeout 30 s, 2 build workers, queue 2×workers, export cache 64 MB, spur's gzip level, `mem_limit` 4g; INTERIM comment per constant; one `must` debt item, trigger Phase 7 | ✓ |
| Measure on the skeleton now | Bench run on the plain cylinder; honest for the skeleton, meaningless for threads; redone in Phase 7 | |
| Wait for the spike's proposed constants | Phase 1 blocks on Phase 2 or ships a pool with no timeout | |

| Option | Description | Selected |
|--------|-------------|----------|
| Keep spur's 4g `mem_limit` as interim | A labelled cap beats none; skeleton lighter than the gear corpus | ✓ |
| No `mem_limit` until measured | Container uncapped | |

**User's choice:** spur's figures as labelled interim; `mem_limit` 4g interim.
**Notes:** SC3 forbids spur figures as *final* bounds; an interim labelled as such is within the wording. OPER-02 re-sweeps in Phase 7.

---

## Skeleton shape + frozen defaults

| Option | Description | Selected |
|--------|-------------|----------|
| Plain cylinder d × length | No head, no chamfer; head dims are Phase 4 table rows, ends are Phase 5 | ✓ |
| Cylinder + placeholder hex head | Bolt-shaped viewer output; every head dimension a guess | |
| Cylinder + tip chamfer | Guessed angle before ISO 4753 is read | |

| Option | Description | Selected |
|--------|-------------|----------|
| d=6.0, pitch=1.0, length=20.0 | M6 × 20, the docs' running example; ASSUMPTION on coarse pitch until the ISO 262 row | ✓ |
| d=8.0, pitch=1.25, length=30.0 | M8 × 30 | |
| d=10.0, pitch=1.5, length=40.0 | M10 × 40 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Inputs + closed-form volume + standing warning | d, pitch, length; π(d/2)²·length; warning "walking skeleton: plain unthreaded cylinder, not a product build"; version 0.0.x | ✓ |
| Inputs only, no warning | Nothing marks the output as non-product | |
| Inputs + volume, no warning | A shared link looks like a product build | |

| Option | Description | Selected |
|--------|-------------|----------|
| Positive, finite; no caps | d, pitch, length > 0 and finite; interim timeout is the backstop; Phase 7 sets caps | ✓ |
| Positive, finite, plus pitch < d | One geometric sanity rule now | |
| Conservative length cap too | An unmeasured number (L02, OPER-03) | |

**User's choice:** plain cylinder; M6 × 1.0 × 20; inputs + volume + standing warning; positive/finite, no caps.

---

## API paths, kind selector, parity proof

| Option | Description | Selected |
|--------|-------------|----------|
| `/api/schema?kind=`, `/api/kinds`, global `/api/health` | Research Q1's shape; one schema route over the registry; kind required | ✓ |
| Everything under the kind path (`/api/bolt/schema`) | Roadmap SC1's literal wording; three routes per kind | |

| Option | Description | Selected |
|--------|-------------|----------|
| Kind selector now, from `/api/kinds`, one entry | Phase 5 adds the nut by registry entry; hash `kind=` omitted = bolt forever | ✓ |
| Defer to Phase 5 with the nut | app.js hardcodes bolt; Phase 5 rewrites fetch and hash reader | |

| Option | Description | Selected |
|--------|-------------|----------|
| Schema-driven proof over app.js source | Per kind: schema == fields; 422 on foreign field; CLI flags == fields, exit 2 on foreign flag; app.js builds from `schema.properties`, no field-name literal; hash round-trip | ✓ |
| API + CLI only; UI leg not asserted | Weaker; SC2 names the UI | |
| Browser-driven (playwright) | New dependency outside L01; node in the gate | |

**User's choice:** query-form schema + global health; selector now; schema-driven parity with a source assertion over app.js.
**Notes:** Roadmap SC1 wording ("schema and health under the bolt kind path") corrected in CONTEXT.md `<domain>`.

---

## Walling `main` and the landing flow

| Option | Description | Selected |
|--------|-------------|----------|
| Code in Phase 1, ruleset after the Phase 1 merge | Scripts, hook, required-jobs, image + vendor-bundle jobs on the branch; owner enables the ruleset post-merge as the last manual checkpoint; new Lxx; idea closed; HOW_TO_DEVELOP updated | ✓ |
| Ruleset first, before any Phase 1 code | Chicken-and-egg: required jobs do not exist on `main` yet | |
| Defer the wall; amend SC3 | Phases 2–3 land unwalled | |

| Option | Description | Selected |
|--------|-------------|----------|
| One PR, plan-level commits on the branch | HOW_TO_DEVELOP: one phase = one PR = one squash | ✓ |
| One PR per plan | Smaller reviews; contradicts the loop and gsd's phase-branch strategy | |

| Option | Description | Selected |
|--------|-------------|----------|
| Push `main` now | 5 docs commits; PR diff is phase work only | ✓ |
| Let the Phase 1 PR carry them | `main` stays at `46315f3` until the merge | |

**User's choice:** code in-phase, ruleset after merge; one PR; push `main` now.
**Notes:** Evidence conflict resolved — ROADMAP SC3 ("in place") vs HOW_TO_DEVELOP §0/§9 and the idea file ("deliberately not up yet"). Resolution recorded as D-11 in CONTEXT.md.

---

## Claude's Discretion

Env prefix; `httpx` dev dependency; coverage floor by spur L34's method on the finished skeleton; `kind` log field; skeleton bench corpus; per-kind query subclasses + `strip()`; boolean control and `BooleanOptionalAction` deferred to Phase 3; `screw pair` to Phase 5; contracts 2, 3, 4, 5, 8 here, 6/7 in Phase 4, 9 in Phase 5; `calc/` and `solid/` as packages from the start.

## Deferred Ideas

None outside the roadmap. Phase-assigned items listed in CONTEXT.md `<deferred>`.
