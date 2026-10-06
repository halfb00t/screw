# screw

Parametric thread and fastener generator — screws, bolts, nuts, threaded rods — the
sibling of [spur](https://github.com/halfb00t/spur) (gears). Set the parameters, get a
live 3D preview, the numbers you would measure on the real part, and an STL or STEP
download, from a web UI, an HTTP API or a CLI.

**Status: walking skeleton (Phase 1), an internal milestone, not released, version 0.0.x.**
The `bolt` kind builds a plain unthreaded cylinder from `d` and `length`; `pitch` is
validated but builds nothing yet, and every info document says so in its warnings. The
numbers it prints are not for cutting metal to. The house rules (`AGENTS.md`), the
architecture and decision log (`docs/`) and the verification gate (`make verify`) are how
the product is built from here with gsd.

## Use

    make serve                                      # web UI and API on http://127.0.0.1:8000
    .venv/bin/screw info bolt --d 8                 # the info document as JSON
    .venv/bin/screw export bolt --d 8 -o bolt.stl   # an STL; `.step` for STEP

## Develop

Python 3.12 is the only supported interpreter (L01 in `docs/architecture/decision_log.md`).

    make                            # list every target
    make verify                     # the gate: ruff, mypy --strict, import boundaries, unfinished-work scan, pytest
    .venv/bin/pre-commit install    # once per clone: the same gate at the commit boundary

The first `make verify` builds `.venv` (~1.4 GB of OpenCascade; a couple of minutes).
How the work is driven, step by step: `docs/HOW_TO_DEVELOP.md`.
