# Architecture overview

One-page map of the system. Grows as the project does.

## What it is

A parametric thread and fastener generator — screws, bolts, nuts, threaded rods. One
validated parameter set will produce a live 3D preview, the dimensions you would measure
on the finished part, and an STL or STEP download, reachable three ways — web UI, HTTP
API, CLI — from one parameter model. The sibling of `spur` (gears), built to the same
rules (L02).

## Stack

Python 3.12, FastAPI + Pydantic v2, uvicorn; CadQuery over OpenCascade; pytest; Docker and
GitHub Actions. Why → `L01`. The viewer is vanilla JS + a vendored three.js bundle.

## Main pieces

The walking skeleton (Phase 1): the `bolt` kind is a plain unthreaded cylinder, served by
the web UI, the HTTP API and the CLI from one registered model. No thread, head, table or
nut yet. Each real subsystem gets its own `architecture/<subsystem>/` once a single file
stops holding it.

| Module | What it is |
|---|---|
| `params` | The one validated, frozen, hashable model: `FastenerParams`, `BoltParams`, the `KINDS` registry and `DEFAULT_KIND`. Its JSON schema builds the web form and the CLI flags; validated once at the boundary, trusted afterwards. |
| `calc` | `PartInfo` and `derive`: the numbers you would measure on the part. Pure arithmetic, no CAD kernel and no logging, because it runs on every keystroke. |
| `solid` | The only doorway to `cadquery`/`OCP`: `build`, `export`, `clear_cache`. Vendor types stop here. |
| `pool` | Worker processes that run builds outside the serving process: affinity by parameter hash, per-build timeout, replacement of a dead or overrun worker, the D-16 same-slot guard. |
| `records` | The JSON-lines log vocabulary: one formatter, one level knob, one function per event. |
| `build_errors` | The build exception types, kernel-free so the CLI and the app can share them. |
| `app` | The FastAPI app: per-kind routes, admission control (a bounded build queue), the bytes cache, gzip, the static files. Never imports the kernel. |
| `cli` | `serve`, `info`, `export` over the same model, with no web-serving policy. |
| `static/` | The schema-driven form and the viewer (vanilla JS, a vendored three.js bundle built from `web/`). |
| `docker/`, `bench/`, `scripts/` | The image smoke driver and lock refresh; the measurement harness (`bench/RESULTS.md`, never a gate); the PR-landing and commit-message guards. |

The dependency direction is enforced, not hoped for: `pyproject.toml` carries the
import-linter contracts and `make verify` fails on a violation. Six are in force, by their
names there, under the numbers the code comments cite (`contract 5`, `contract 8`):

- 1: The app never imports its own tests
- 2: The thread maths stays free of the CAD kernel
- 3: The CLI does not inherit web-serving policy
- 4: The thread maths stays free of the logger
- 5: The serving process never imports the CAD kernel
- 8: Only the solid package imports the CAD kernel

The gaps are planned: contracts 6 and 7 (the tables) land in Phase 4 and contract 9 (the
pair proof) in Phase 5, each in the commit that adds the module it guards.

## Source of truth

- **The part** — nothing is stored. Every answer is derived from the parameters on demand;
  any cache is a speed optimisation and safe to lose.
- **The parameters** — the URL. A model link carries its full parameter set, which is why
  defaults are frozen (L02).
- **The dependency closure** — `requirements.txt`, the runtime closure resolved in
  linux/amd64 by `make lock` (L07, L08).
- **Decisions** — `decision_log.md`. **Per-phase intent** — gsd's `.planning/`.
