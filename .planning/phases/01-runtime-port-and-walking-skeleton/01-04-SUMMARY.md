---
phase: 01-runtime-port-and-walking-skeleton
plan: 04
subsystem: ui
tags: [vanilla-js, three.js, esbuild, fastapi-static, npm-ci, github-actions]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "api/kinds, api/schema?kind=, api/<kind>/info and model routes (01-01, 01-02); the KINDS registry and PartInfo document the page renders generically"
provides:
  - "Web UI served at GET /: kind selector from /api/kinds, form generated from /api/schema?kind=, live 3D preview, generic info panel (label, value, unit rows plus warnings), STL/STEP downloads, Reset and Copy link"
  - "Shareable hash that carries only fields differing from their defaults and kind= only when it differs from /api/kinds' default; an unregistered kind is an error naming it and builds nothing"
  - "Vendored three.js 0.186.0 bundle, byte-identical to spur's, rebuilt from web/ by make vendor / make vendor-check and by the CI vendor-bundle job"
  - "STATIC, the /static mount and GET / in app.py; / added to docker/smoke.py; test_index_and_static"
affects: [01-05 parity test, 01-06 docker, 01-07 ci matrix, phase-3 threads, phase-5 pair, phase-7 operational sweep]

actuals:
  tokens: 6250
  tasks: 2
  commits: 2
plan_head_before: ea1d7e35bb6d4f429df0c9ac74777471be9d8022
plan_head_after: 6d23fde4403da129af7b156c07ee76c7f2951ece

tech-stack:
  added: [three 0.186.0 (vendored bundle), esbuild 0.25.12 (build only, web/)]
  patterns:
    - "UI reads everything off the API: no field name, row key or kind label appears in app.js, so a new registered kind needs no edit there"
    - "one navigate() for startup, hashchange and the kind selector; seq, AbortController and formSeq discard overtaken responses"
    - "committed vendor bundle is reproducible: npm ci from the lockfile, byte comparison via git diff --exit-code"

key-files:
  created:
    - src/screw/static/index.html
    - src/screw/static/app.js
    - src/screw/static/style.css
    - src/screw/static/vendor/three.bundle.min.js
    - src/screw/static/vendor/three.LICENSE
    - web/entry.js
    - web/package.json
    - web/package-lock.json
    - .gitattributes
  modified:
    - src/screw/app.py
    - docker/smoke.py
    - tests/test_api.py
    - docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md
    - Makefile
    - .github/workflows/ci.yml
    - .gitignore

key-decisions:
  - "navigate() bumps seq, formSeq and aborts the in-flight request on every call, not only on a kind change, so a hash edit never lets an older response render"
  - "An unregistered kind clears the form and sets currentKind to null, and update() returns early on null: a later field edit cannot silently build the default bolt under a link that named another kind (L02)"
  - "The hash write is one writeHash() shared by update() and the selector handler instead of two copies of spur's replaceState line"

patterns-established:
  - "number inputs compare Number(input.value) !== Number(defaults[name]) so 6.0 and 6 are the same default and stay out of the link"
  - "exclusiveMinimum never sets an HTML min; the server's 422 speaks (Pitfall 5)"

requirements-completed: [FRNT-02, INFR-01]

coverage:
  - id: D1
    description: "GET / serves the page and /static serves app.js and the vendored bundle"
    requirement: FRNT-02
    verification:
      - kind: unit
        ref: "tests/test_api.py#test_index_and_static"
        status: pass
      - kind: integration
        ref: ".venv/bin/python docker/smoke.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Kind selector, schema-generated form, live preview, generic info panel, downloads and a hash that omits defaults and the default kind behave as the plan's seven-step human-check describes"
    requirement: FRNT-02
    verification: []
    human_judgment: true
    rationale: "No browser runs in the gate (L01); the plan carries the seven-step human-check to end-of-phase UAT. app.js is syntax-checked with node --check and its genericity is pinned by plan 01-05's source assertions, but rendering, the hash round trip and the stale-response behaviour are only observable in a browser."
  - id: D3
    description: "The vendored three.js bundle rebuilds byte-identical from web/ with node 22 and npm ci"
    requirement: INFR-01
    verification:
      - kind: other
        ref: "make vendor-check"
        status: pass
    human_judgment: false
  - id: D4
    description: "The CI vendor-bundle job runs the same rebuild-and-diff check"
    requirement: INFR-01
    verification: []
    human_judgment: true
    rationale: "The job is written but a GitHub Actions run cannot happen before the branch is pushed; the local make vendor-check runs the same steps."

duration: 12min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 04: The web UI and the reproducible three.js bundle Summary

**Schema-driven web UI (kind selector, generated form, live three.js preview, generic info panel, default-omitting shareable hash) over the ported runtime, with the vendored three.js 0.186.0 bundle rebuilt byte-identical from web/ by make vendor-check and a CI job**

## Performance

- **Duration:** about 12 min (start time was not captured at launch; estimated from the first and last tool timestamps)
- **Completed:** 2026-10-06T04:36:09Z
- **Tasks:** 2
- **Files modified:** 16 (9 created, 7 modified; the bundle, its licence and the lockfile counted)

## Accomplishments
- A user can open `/`, pick a kind, edit d/pitch/length in a form generated from the schema, watch the preview, read the info rows and warnings, download STL/STEP and copy a link that reopens the same part. app.js holds no field name, row key or per-kind label; every node is built with `textContent` or `Object.assign`.
- The hash carries only fields that differ from their defaults (numeric compare, so `6.0` is dropped) and `kind=` only when the kind differs from the registry default. A hash naming an unregistered kind shows an error naming it and the known kinds, and builds nothing.
- `make vendor-check` runs `npm ci` and the esbuild build in web/ and fails on any byte of drift under `src/screw/static/vendor`; it passed on this machine (node 22.23.1, npm 10.9.8). The CI `vendor-bundle` job runs the same steps. The unfinished-work scan skips the vendored bundle.
- The 350 ms debounce is labelled INTERIM in app.js and has a row in the D-02 debt item.

## Task Commits

1. **Task 1: The page** - `8fd0ab0` (feat)
2. **Task 2: Reproducible bundle (make vendor, vendor-check, CI job)** - `6d23fde` (build)

**Plan metadata:** committed with this SUMMARY (docs: complete plan).

## Files Created/Modified
- `src/screw/static/index.html` - page shell with the `#kind` selector and the ids app.js uses
- `src/screw/static/app.js` - kinds loader, schema form builder, `navigate()`, `partQuery()`, `update()`, generic `renderInfo()`, viewer ported from spur
- `src/screw/static/style.css` - spur's stylesheet minus the three mating-gear rules
- `src/screw/static/vendor/three.bundle.min.js`, `three.LICENSE` - byte copies of spur's (checked with `cmp`)
- `src/screw/app.py` - `STATIC`, the `/static` mount after the GZip middleware, `GET /`
- `docker/smoke.py` - `/` joins the 200-checked paths
- `tests/test_api.py` - `test_index_and_static`
- `docs/tech_debt/active/2026-10-05-interim-runtime-bounds.md` - UI debounce row
- `web/entry.js`, `web/package.json`, `web/package-lock.json` - the bundle build, writing into `src/screw/static/vendor`
- `Makefile`, `.github/workflows/ci.yml`, `.gitattributes`, `.gitignore` - `vendor`, `vendor-check`, vendor-bundle job, vendored-file attributes, `web/node_modules/`

## Decisions Made
- `navigate()` bumps `seq` and `formSeq` and aborts the in-flight request on every call. The plan names `formSeq` for a schema fetch overtaken by a newer navigation; bumping it on every navigation (also unknown-kind and same-kind ones) closes the gap where a late schema response would rebuild the form for a kind the hash no longer names.
- After an unknown kind the form is cleared and `currentKind` is null; `update()` returns early on null. Leaving the old form live would let one keystroke build the default bolt under a link that named another kind.
- One `writeHash()` serves `update()` and the selector handler.

## Deviations from Plan

None - plan executed exactly as written.

The two choices above go beyond the plan's wording but stay inside its stated requirements (never render an older response; L02), so they are recorded as decisions rather than deviations.

## Issues Encountered
- A `sed -i` call without the macOS empty backup suffix consumed its script as the suffix and failed before changing anything; redone with `sed -i ''`. No file was affected.
- pre-commit stashes unstaged files around each commit; the orchestrator-owned `.planning/config.json`, `milestone.lock` and `state.json` were restored unchanged both times (checked with `git status` after each commit).

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. The skeleton warning rendered in the panel is the server's standing `SKELETON_WARNING`, not a UI placeholder.

## Threat Flags

None. The new surface (static mount, `GET /`, the page) is covered by T-01-15 to T-01-17 and T-01-SC; no network endpoint, auth path or file access beyond the plan's threat model was added.

## Verification

- `make verify`: ruff, mypy --strict, `Contracts: 6 kept, 0 broken`, unfinished-work scan, `163 passed in 26.49s` (162 before this plan plus `test_index_and_static`).
- `.venv/bin/python -m pytest tests/test_api.py -q -p no:cacheprovider -k index_and_static`: `1 passed, 64 deselected`.
- `.venv/bin/python docker/smoke.py`: prints `smoke: kernel, exports, ASGI stack and validation all live`.
- `node --check` on a `.mjs` copy of app.js: no output, exit 0.
- `cmp` of the bundle and licence against spur's: identical.
- `make vendor-check`: exit 0, `git status --porcelain -- src/screw/static/vendor` empty.
- All acceptance greps for both tasks matched. `grep -o 'src/screw/static/vendor/three\.[A-Za-z.]*' web/package.json | sort -u` prints exactly the two paths (the order differs by locale).

### Human UAT carried to end of phase
Task 1's seven-step human-check (selector shows bolt; form order and units; hash `#d=8` without `kind=`; `6.0` drops `d`; clearing Length drops it; `d=100001` shows an error naming Diameter and keeps the last part; `#kind=nut` shows an error naming nut and listing bolt; copy-link round trip; STL and STEP download; rapid typing shows only the last value) has not been run: no browser is available to the gate (L01).

## Next Phase Readiness
- Plan 01-05's parity test can pin app.js now: the pinned statements (`fetch('api/kinds')`, `for (const [name, prop] of Object.entries(schema.properties)) {`, `fields.set(name, { input, wrap, title });`, `const kind = h.get('kind') ?? kinds.default;`, `for (const row of info.rows) {`, `hashQ.set('kind', currentKind)`) are present, and none of `d`, `pitch`, `length`, `volume` appears as a quoted literal or a property read in app.js.
- Plan 01-06 appends its remaining rows (`SCREW_WORKERS`, `mem_limit`, HEALTHCHECK, tmpfs) to the debt item; the intro line now says so.
- The Docker image must copy `src/screw/static` (including `vendor/`) into the package; that is plan 01-06's concern.
- The CI `vendor-bundle` job has not run on GitHub yet.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*

## Self-Check: PASSED

All nine created files exist on disk; commits `8fd0ab0` and `6d23fde` are ancestors of HEAD; `make verify` and `make vendor-check` pass on the final tree.
