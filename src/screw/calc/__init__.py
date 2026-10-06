"""The numbers the tool prints about a part: pure maths, free of the CAD kernel and the logger.

`derive()` runs on every keystroke in the UI, so this package never imports `cadquery`,
`logging` or `screw.records` (import-linter contracts 2 and 4). A value that cannot be
computed honestly is left out of `rows` and explained in `warnings` -- never a plausible
number (L02, D-15).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict

from screw.params import BoltParams, FastenerParams

# The standing entry on every info document (D-06): the skeleton is an internal milestone,
# not a product, and nobody should cut metal to its numbers.
SKELETON_WARNING = "walking skeleton: plain unthreaded cylinder, not a product build"


class InfoRow(BaseModel):
    """One labelled number. The UI renders rows generically; it never reads a row by key."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    value: float
    unit: str


class PartInfo(BaseModel):
    """The info document: identical on `/api/<kind>/info` and `screw info <kind>` (D-15)."""

    model_config = ConfigDict(frozen=True)

    kind: str
    rows: list[InfoRow]
    warnings: list[str]


def _bolt(p: BoltParams) -> PartInfo:
    rows = [
        InfoRow(key="d", label="Diameter", value=p.d, unit="mm"),
        InfoRow(key="pitch", label="Pitch", value=p.pitch, unit="mm"),
        InfoRow(key="length", label="Length", value=p.length, unit="mm"),
    ]
    warnings = [SKELETON_WARNING]
    # The closed form, never the kernel's Volume() (D-06). D-14's bound keeps validated
    # input far below overflow, so this guard is reached only by an instance that skipped
    # validation (model_construct), but "no non-finite number leaves derive()" is this
    # function's own contract (D-15): d=1e200 overflows a float on the way here (F2).
    try:
        volume = math.pi * (p.d / 2) ** 2 * p.length
    except OverflowError:
        volume = math.inf
    if math.isfinite(volume):
        rows.append(InfoRow(key="volume", label="Volume (closed form)", value=volume, unit="mm³"))
    else:
        warnings.append("volume not reported: pi * (d / 2)^2 * length is not a finite number "
                        "for these parameters")
    return PartInfo(kind=p.kind, rows=rows, warnings=warnings)


def derive(p: FastenerParams) -> PartInfo:
    """The info document for `p`.

    Dispatches with `isinstance`, not a `match` over a closed union: base-typed callers
    (pool, app, tests) would otherwise need a union threaded through every signature. A
    registered kind without an entry here raises TypeError and fails the registry test
    that derives every `KINDS` entry, not a user.
    """
    if isinstance(p, BoltParams):
        return _bolt(p)
    raise TypeError(f"no info document for kind {p.kind!r}")
