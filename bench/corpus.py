"""The Phase 1 corpus: 12 parts on a d x length grid, threaded since Phase 3.

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

    `pitch` is left at its default of 1 mm, so since Phase 3 each entry builds the L11 thread
    at that pitch (up to 200 turns for the heaviest part, which is the last, d=100 length=200).
    The grid was chosen for the cylinders it first described and is still not a bound. Since
    Phase 4 each entry also pins a head, `s = 2 * d` and `k = d / 2`: harness inputs chosen so
    every entry passes `s > d` and keeps the grid's shape, not ISO rows and not bounds (04-03).
    It pins `thread_length = length` too: the default is a 20 mm thread under a plain shank, which
    would quietly turn the 200-turn part into a cheap one, so each entry builds the full-length
    thread it built in Phase 3 and later runs stay comparable (OPER-02, 04-06). The grid itself
    is unchanged.
    """
    return [{"d": d, "length": length, "s": 2 * d, "k": d / 2, "thread_length": length}
            for d in DIAMETERS for length in LENGTHS]


def label(entry: dict[str, object]) -> str:
    """`d=100 length=200`: the entry's own `key=value` pairs in order, numbers as `%g`.

    One spelling for the corpus and for a sweep file, so a label printed by one run is found by
    `bench.export_cost --set` in another. Lives here, not in `bench.build_time`, because that
    module imports `screw.solid` and so the CAD kernel, which `bench.latency` -- a measuring
    client that must stay kernel-free -- must not pull in.
    """
    return " ".join(
        f"{k}={v:g}" if isinstance(v, int | float) else f"{k}={v}" for k, v in entry.items())
