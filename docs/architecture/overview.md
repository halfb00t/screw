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

The `bolt` kind is a hex head bolt or screw (Phase 4): an ISO 4014 bolt (partial thread, plain
shank) or an ISO 4017 screw (threaded to the head), built from explicit millimetres (`d`, `pitch`,
`left_hand`, `length`, `s`, `k`, `thread_length`) and served by the web UI, the HTTP API and the
CLI from one registered model. The thread is the ISO 68-1:2023 basic profile, right- or
left-hand, built by the one construction L11 chose; the head is a plain hex prism and both thread
ends are plain planar cuts, the chamfer and the fillet being Phase 5's (L13). A preset ("ISO 4017
M6 x 20") only fills those fields from a cited, double-entered ISO row: no link carries a preset
and no part is rebuilt from a table. No nut yet. Every build passes the THRD-04 postcondition,
on the bare thread and then on the whole part, before it reaches a cache, a preview or a download
(L12, L13). Each real subsystem gets its own `architecture/<subsystem>/` once a single file stops
holding it.

| Module | What it is |
|---|---|
| `params` | The one validated, frozen, hashable model: `FastenerParams`, `BoltParams`, the `KINDS` registry and `DEFAULT_KIND`. Its JSON schema builds the web form and the CLI flags; validated once at the boundary, trusted afterwards. It never consults a table (contract 6); two explicit values in conflict (`thread_length` above `length`) are refused at the request boundary, not here (L13). |
| `calc` | `PartInfo` and `derive`: the numbers you would measure on the part. Pure arithmetic, no CAD kernel and no logging, because it runs on every keystroke. `calc/thread.py` is the thread oracle (the ISO 68-1:2023 profile, the closed-form volume, `T_GATE`) and the kernel-free rules (the root-radius bound, the 250-turn cap, the fine-STL rows). `calc/presets.py` is the one calc module that reads `screw.tables` (the exact row match, the matched row's cited values and notes, the designation, and the catalogue document); `_bolt` imports it inside the function, so a rebuilt link never loads a table. |
| `tables` | Tables are a leaf: stdlib only. Cited ISO 262:2023, ISO 4014:2022 and ISO 4017:2022 rows for M2 to M20 as per-size records of numbers, each with a required typed `Source`; double-entered against the owner's copy and gated against `unverified` rows in `make verify`. The licence stance in one sentence: numeric values with their source only, no clause wording, notes, figures or table layout (L13, D-16). `tables/presets.py` hands out the 294-row catalogue and `expand`; no link ever carries a preset, so a part is rebuilt from its fields without a table. |
| `solid` | The only doorway to `cadquery`/`OCP`: `build`, `export`, `clear_cache`. Vendor types stop here. `solid/helical.py` is the one helical builder, for the rod and for the void; the THRD-04 gate (`check_solid`) and the export checks sit in `solid/__init__.py`, inside the function the solid cache wraps. |
| `pool` | Worker processes that run builds outside the serving process: affinity by parameter hash, per-build timeout, replacement of a dead or overrun worker, the D-16 same-slot guard. |
| `records` | The JSON-lines log vocabulary: one formatter, one level knob, one function per event. |
| `build_errors` | The build exception types, kernel-free so the CLI and the app can share them. |
| `app` | The FastAPI app: per-kind routes, `GET /api/presets` (the catalogue document), admission control (a bounded build queue), the bytes cache, gzip, the static files. Never imports the kernel. |
| `cli` | `serve`, `info`, `export` and `presets` over the same model, `--preset` on `info` and `export`, with no web-serving policy. |
| `static/` | The schema-driven form and the viewer (vanilla JS, a vendored three.js bundle built from `web/`). |
| `docker/`, `bench/`, `scripts/` | The image smoke driver and lock refresh; the measurement harness (`bench/RESULTS.md`, never a gate), including the slow thread grid tier (`make grid`, `.github/workflows/grid.yml`: outside `make verify` and the required jobs); the PR-landing and commit-message guards. |

The dependency direction is enforced, not hoped for: `pyproject.toml` carries the
import-linter contracts and `make verify` fails on a violation. Nine are in force, by their
names there, under the numbers the code comments cite (`contract 5`, `contract 8`):

- 1: The app never imports its own tests
- 2: The thread maths stays free of the CAD kernel
- 3: The CLI does not inherit web-serving policy
- 4: The thread maths stays free of the logger
- 5: The serving process never imports the CAD kernel
- 6: The parameters never consult a table (its runtime half is `tests/test_import_boundaries.py`)
- 7: Tables are a leaf
- 8: Only the solid package imports the CAD kernel
- The spike's oracle, verdict and parent process stay free of the CAD kernel (unnumbered). It now
  also covers `screw.calc.thread`, which the spike imports back, so the oracle the gate uses is
  the one the spike measured.

The gap is planned: contract 9 (the pair proof) lands in Phase 5, in the commit that adds the
module it guards.

## Source of truth

- **The part** — nothing is stored. Every answer is derived from the parameters on demand;
  any cache is a speed optimisation and safe to lose.
- **The parameters** — the URL. A model link carries its full parameter set, which is why
  defaults are frozen (L02).
- **The dependency closure** — `requirements.txt`, the runtime closure resolved in
  linux/amd64 by `make lock` (L07, L08).
- **Decisions** — `decision_log.md`. **Per-phase intent** — gsd's `.planning/`.
