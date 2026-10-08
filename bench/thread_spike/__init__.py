"""The thread spike (Phase 2, INFR-03): a pre-registered measurement campaign, not product code.

It answers four questions with recorded runs: which helical construction to build, what a fine
mesh costs, whether a kernel pair check can be made falsifiable, and which volume estimator
agrees with the closed form. Nothing here is in `make verify` as a timing, and nothing it
prints is a bound (L07).

Module map. The kernel-free half runs in the parent process and is held to that by an
import-linter contract: `maths` (the closed-form oracle), `verdict` (wire shapes and the pure
predicates that classify a row), `runner` (the worker subprocess handle) and `__main__` (the
command line). The kernel half imports cadquery/OCP and runs only inside the worker child:
`helical` (the builder), `measure` (volumes and the STL check) and `worker` itself.

Promotion (D-18): `maths` becomes `screw/calc/thread.py` and `helical` becomes
`screw/solid/helical.py`, moved unchanged where possible, so what was measured is what ships.
"""
