"""The walking skeleton's corpus: 12 plain cylinders on a d x length grid.

This exercises the harness. It sets no bound (L07: the harness is ported, the numbers are not).
It stays far below the D-14 corner (`d`, `length` up to 1e5 mm) on purpose, so nothing
measured against it says anything about the interim `mem_limit` or `SCREW_BUILD_TIMEOUT`.
Phase 7 replaces it with the threaded grid and keeps that one fixed from then on, so a later
run is comparable with an earlier one (OPER-02).

Deterministic: the grid is written out, never generated from a seed or the host.
"""

from __future__ import annotations

DIAMETERS = (2.0, 6.0, 20.0, 100.0)
LENGTHS = (5.0, 20.0, 200.0)


def corpus() -> list[dict[str, object]]:
    """The 12 parts, diameter outermost, as query-parameter dictionaries.

    `pitch` is left at its default: the skeleton builds no thread (D-04), so it does not change
    the solid. The heaviest part is the last, d=100 length=200.
    """
    return [{"d": d, "length": length} for d in DIAMETERS for length in LENGTHS]
