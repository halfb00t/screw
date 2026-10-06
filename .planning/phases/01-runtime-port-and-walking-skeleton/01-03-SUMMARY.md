---
phase: 01-runtime-port-and-walking-skeleton
plan: 03
subsystem: cli
tags: [argparse, cli, uvicorn, import-linter, pytest]

requires:
  - phase: 01-runtime-port-and-walking-skeleton
    provides: "KINDS registry and BoltParams (01-01), calc.derive and PartInfo (01-01), solid.export (01-01), the API whose info document the CLI must equal (01-02)"
provides:
  - "screw serve | info <kind> | export <kind> with every flag generated from the registered model"
  - "[project.scripts] screw entry point and python -m screw"
  - "import-linter contract 3 (CLI never imports screw.app, fastapi or starlette); contract 2 now covers screw.cli"
  - "make serve"
  - "README Use section whose .venv/bin/screw commands are executed by a test"
affects: [01-04 ui, 01-05 parity test, 01-07 docker, phase-3 threads, phase-5 pair, phase-7 operational sweep]

actuals:
  tokens: 4600
  tasks: 2
  commits: 3
plan_head_before: c7f2ed6772e950c8fa2c6b9454969e74a3cf2586
plan_head_after: c0652afaf257bc869c980d29788be740ba6eade7

tech-stack:
  added: []
  patterns:
    - "one subparser per KINDS entry under nested required subparsers (dest=kind); a new kind is a registry entry, never a CLI edit"
    - "allow_abbrev=False on every parser, kind parsers included, so a flag prefix never binds a field"
    - "kernel imported lazily inside cmd_export, after the extension check"

key-files:
  created:
    - src/screw/cli.py
    - src/screw/__main__.py
    - tests/test_cli.py
  modified:
    - pyproject.toml
    - Makefile
    - README.md

key-decisions:
  - "serve reads SCREW_PORT and SCREW_WORKERS through the repo's int_env (as app.py does) instead of spur's bare int(): a garbage value falls back rather than crashing the parser build for every subcommand, including `screw info`"
  - "cmd_export checks the output extension before importing the kernel, so a typo exits in milliseconds instead of after the ~2 s cadquery load"
  - "screw info and screw export require an explicit kind; the CLI follows the API (D-08), the omitted-means-bolt rule governs only the URL hash (D-09)"

patterns-established:
  - "A RED commit that needs a module which does not exist ships a placeholder and a module-level strict xfail; the GREEN commit deletes both"
  - "README commands are collected by regex, run in-process with -o rewritten into tmp_path, and the test asserts at least two were found"

requirements-completed: [FRNT-04, FRNT-01]

coverage:
  - id: D1
    description: "screw info bolt prints the same PartInfo JSON document calc.derive produces; each field flag is read"
    requirement: FRNT-04
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_info_prints_the_part_info_document"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_info_reads_every_field_flag"
        status: pass
    human_judgment: false
  - id: D2
    description: "screw export bolt writes a binary STL (84 + 50n bytes) or a STEP file and prints the skeleton warning to stderr; --format overrides the extension"
    requirement: FRNT-04
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_export_writes_stl_and_step_and_warns_on_stderr"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_the_format_flag_overrides_the_extension"
        status: pass
    human_judgment: false
  - id: D3
    description: "Flags are generated from the model fields, in declaration order, for every registered kind and both commands"
    requirement: FRNT-01
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_the_flags_follow_the_model_fields_in_order"
        status: pass
    human_judgment: false
  - id: D4
    description: "A foreign flag, a flag prefix, a bad value and an unknown kind each exit 2 naming the offender; a bad extension exits 1 from the real process and writes nothing; a kernel failure stops the export and writes nothing"
    requirement: FRNT-01
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_a_foreign_flag_exits_2_naming_it"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_a_prefix_of_a_real_flag_is_refused"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_a_bad_value_exits_2_naming_the_field"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_an_unknown_kind_exits_2"
        status: pass
      - kind: integration
        ref: "tests/test_cli.py#test_an_unknown_output_extension_exits_1_from_the_real_process"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_a_kernel_failure_stops_the_export_and_writes_nothing"
        status: pass
    human_judgment: false
  - id: D5
    description: "screw serve runs uvicorn on screw.app:app with log_config=None; started for real on SCREW_PORT=8765 it answered /api/health with status ok"
    requirement: FRNT-04
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_serve_runs_uvicorn_on_the_app_without_its_own_log_config"
        status: pass
      - kind: other
        ref: "SCREW_PORT=8765 .venv/bin/screw serve; GET /api/health"
        status: pass
    human_judgment: false
  - id: D6
    description: "The CLI never imports the web layer (contract 3 KEPT) and screw.cli is covered by the kernel-free contract 2"
    requirement: FRNT-04
    verification:
      - kind: other
        ref: "make lint-imports (Contracts: 6 kept, 0 broken)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Every .venv/bin/screw command in README.md runs as written"
    requirement: FRNT-04
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_readme_cli_examples_run"
        status: pass
    human_judgment: false
  - id: D8
    description: "The README states the skeleton's status honestly"
    verification: []
    human_judgment: true
    rationale: "Whether the prose describes the walking skeleton faithfully and does not oversell it is a judgment; the acceptance greps only prove the stale sentence is gone and the Use section exists"

duration: 8 min
completed: 2026-10-06
status: complete
---

# Phase 1 Plan 03: CLI Summary

**`screw serve | info <kind> | export <kind>` with every flag generated from the registered model, `allow_abbrev=False` on all seven parsers so a prefix like `--len` exits 2 instead of binding `--length`, and import-linter contract 3 keeping the web layer out of the CLI.**

## Performance

- **Duration:** about 8 min of agent time (start not recorded at launch; derived from the previous plan's STATE update at 04:20Z)
- **Started:** 2026-10-06T04:20:00Z (approximate)
- **Completed:** 2026-10-06T04:28:00Z
- **Tasks:** 2
- **Files modified:** 6 (3 created, 3 modified; excludes `.planning/`)

## Accomplishments

- `screw info bolt` prints exactly `derive(BoltParams()).model_dump_json(indent=2)`; `screw export bolt -o x.stl|.step` writes a binary STL (size checked as 84 + 50n) or STEP and prints `warning: walking skeleton: plain unthreaded cylinder, not a product build` on stderr.
- Flags come from `model_fields` per `KINDS` entry under the help group `<kind> parameters (defaults in brackets)`; a test walks the registry and compares `--help` output to field order for both commands.
- Refusals measured by hand and by test: `--m 5`, `--len 5`, `--pit 1`, `--hos` (serve), `info nut`, `--d 0|inf|nan|100001`, `--length -1` all exit 2 naming the argument; `export -o b.obj` exits 1 from a real subprocess with the exact message and writes nothing; `--d 1e-9` passes the model and the kernel refuses it, so export stops with `error: Geometry kernel produced an invalid solid ...` and no file.
- `screw serve` started for real (`SCREW_PORT=8765`) answers `/api/health` with `status: ok` and logs through the one JSON handler.
- `make verify`: 162 passed, `Contracts: 6 kept, 0 broken` (was 136 and 5).

## Task Commits

1. **Task 1 RED: failing CLI tests against a placeholder `main`** - `d45bcb4` (test)
2. **Task 1 GREEN: serve, info and export, entry point, contract 3, `make serve`** - `151cd6f` (feat)
3. **Task 2: README status and Use section, README commands as a test** - `c0652af` (docs; also adds `test_readme_cli_examples_run`)

**Plan metadata:** committed with STATE and ROADMAP after this SUMMARY (docs: complete plan).

## TDD Gate Compliance

- **RED** (`d45bcb4`): 25 tests written first, run against a placeholder `cli.main` that raises `SystemExit("screw: command line not built yet ...")`. Real run, no marker: `25 failed in 0.17s`. Each fails on the planned behaviour, not on collection: a `SystemExit` where output or a specific exit code was asserted, `returncode == 1` for the real-process test (the placeholder has no `__main__` guard, so it returned 0). Semantic assessment: no test failed on an import, fixture or syntax error, and none passed unexpectedly. A strict module-level `xfail` carried the commit past the pre-commit `make verify`, as in 01-01; the placeholder exists only because `from screw import cli` would otherwise fail `mypy --strict` in that hook. `gsd_run check tdd-red-evidence` was not run: pytest's plain-text report is not one of its supported formats, so the evidence above is the raw run plus this assessment.
- **GREEN** (`151cd6f`): placeholder replaced, marker removed, `25 passed`, full gate green.
- **REFACTOR:** none needed.

## Files Created/Modified

- `src/screw/cli.py` - the three commands; `_add_args`, `_params`, `cmd_serve`, `cmd_info`, `cmd_export`, `main`
- `src/screw/__main__.py` - `python -m screw`
- `tests/test_cli.py` - 26 collected tests (25 before the README test), several parametrised over flags, values, kinds and commands
- `pyproject.toml` - `[project.scripts] screw`, contract 2 gains `screw.cli`, new contract 3
- `Makefile` - `serve` target
- `README.md` - status paragraph replaced, `## Use` section

## Decisions Made

See `key-decisions` above. None needed an owner decision: each is local to `cli.py` and consistent with how `app.py` already reads its environment.

## Deviations from Plan

### Auto-fixed Issues

None to code. Three small differences from the plan text, all inside `cli.py`:

- `serve` reads `SCREW_PORT` / `SCREW_WORKERS` with `int_env` (the repo's own helper, used by `app.py`) rather than `int(env(...))` from spur. Reason: the parser is built on every invocation, so spur's form would crash `screw info bolt` with a traceback if `SCREW_PORT=abc` were set. [Rule 1 - Bug avoided in the port]
- `cmd_export` imports the kernel after the extension check, not before, so the exit-1 path costs milliseconds.
- Extra tests beyond the eleven named: `test_the_format_flag_overrides_the_extension`, `test_version_prints_the_package_version`, `test_serve_runs_uvicorn_on_the_app_without_its_own_log_config`. They pin plan truths (`--format`, `--version`, "runs uvicorn on screw.app:app with log_config=None") that no named test covered.

---

**Total deviations:** 0 auto-fixed in the Rule 1-3 sense; 3 local port/test additions listed above.
**Impact on plan:** none; every acceptance criterion passes as written.

## Issues Encountered

- The first RED commit attempt was refused by the pre-commit gate: the placeholder docstring was 101 columns (ruff E501). Shortened, recommitted; no `--no-verify`.
- `make verify` reinstalled the editable package after `pyproject.toml` changed (stamp dependency), which is what makes `.venv/bin/screw` exist.

## Known Stubs

None. The placeholder `main` from the RED commit is gone in `151cd6f`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 01-04 (web UI): `make serve` and `screw serve` are the way to run it; the README's `make serve` line already says "web UI and API", which becomes true when 01-04 lands.
- Plan 01-06 still owes the debt row for the INTERIM `SCREW_WORKERS=1` comment in `cmd_serve` (the plan assigns it there; nothing is filed from this plan).
- 01-05's parity test over the registry can read `cli.main([cmd, kind, "--help"])` the same way `test_the_flags_follow_the_model_fields_in_order` does.

Debt filed by this plan: none.

---
*Phase: 01-runtime-port-and-walking-skeleton*
*Completed: 2026-10-06*

## Self-Check: PASSED

- FOUND: src/screw/cli.py, src/screw/__main__.py, tests/test_cli.py
- FOUND commits: d45bcb4, 151cd6f, c0652af (all ancestors of HEAD)
- `make verify`: 162 passed, Contracts: 6 kept, 0 broken
- Acceptance greps: `allow_abbrev=False` x7, entry point, contract 3, `serve:` target, `## Use`, no "nothing is built yet", `test_readme_cli_examples_run` passes
