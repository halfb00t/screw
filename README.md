# screw

Parametric thread and fastener generator — screws, bolts, nuts, threaded rods — the
sibling of [spur](https://github.com/halfb00t/spur) (gears). Set the parameters, get a
live 3D preview, the numbers you would measure on the real part, and an STL or STEP
download, from a web UI, an HTTP API or a CLI.

**Status: nothing is built yet.** This repository holds the agent-ready foundation — the
house rules (`AGENTS.md`), the architecture and decision log (`docs/`), and the
verification gate (`make verify`). The product is planned and built from here with gsd.

## Develop

Python 3.12 is the only supported interpreter (L01 in `docs/architecture/decision_log.md`).

    make                            # list every target
    make verify                     # the gate: ruff, mypy --strict, import boundaries, unfinished-work scan, pytest
    .venv/bin/pre-commit install    # once per clone: the same gate at the commit boundary

The first `make verify` builds `.venv` (~1.4 GB of OpenCascade; a couple of minutes).
How the work is driven, step by step: `docs/HOW_TO_DEVELOP.md`.
