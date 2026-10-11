"""The numbers the tool prints about a part: pure maths, free of the CAD kernel and the logger.

`derive()` runs on every keystroke in the UI, so this package never imports `cadquery`,
`logging` or `screw.records` (import-linter contracts 2 and 4). A value that cannot be
computed honestly is left out of `rows` and explained in `warnings` -- never a plausible
number (L02, D-15).
"""

from __future__ import annotations

import math
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict

from screw.calc.thread import closed_volume, fine_stl_refusal, thread_depth, turns_of
from screw.params import BoltParams, FastenerParams

PROFILE = "ISO 68-1:2023 basic profile"

# The standing entry on every info document (D-06): while the bolt is a bare threaded rod it is
# not a product, and nobody should cut metal to it. Phase 4 rewrites it when the head lands;
# Phase 6 removes it at release.
STANDING_WARNING = "threaded rod: no head, plain-cut thread ends; not a product build"


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
    warnings = [STANDING_WARNING]
    # Every number below is the pinned profile's or an exact reading of the user's own fields,
    # never the kernel's Volume() (D-05). The bounds keep validated input finite, so a row is
    # left out only for an instance that skipped validation (model_construct); but "no
    # non-finite number leaves derive()" is this function's own contract (D-15): d=1e200
    # overflows a float on the way (F2) and `Fraction(repr(inf))` raises.
    computed: list[tuple[str, str, str, str, Callable[[], float]]] = [
        ("turns", "Turns", "", "length / pitch", lambda: turns_of(p.length, p.pitch)),
        ("volume", "Volume (closed form)", "mm³",
         "the closed form section_area(d, pitch) * length",
         lambda: closed_volume(p.d, p.pitch, p.length)),
        ("thread_depth", f"Thread depth ({PROFILE})", "mm", "5H/8 with H = (sqrt(3) / 2) * pitch",
         lambda: thread_depth(p.pitch)),
        ("minor_diameter", f"Minor diameter ({PROFILE})", "mm", "d - 2 * (5H/8)",
         lambda: p.d - 2 * thread_depth(p.pitch)),
    ]
    for key, label, unit, formula, compute in computed:
        try:
            value = compute()
        except (OverflowError, ValueError):
            value = math.nan
        if math.isfinite(value):
            rows.append(InfoRow(key=key, label=label, value=value, unit=unit))
        else:
            warnings.append(f"{key} not reported: {formula} is not a finite number "
                            "for these parameters")
    # The page's Download STL link asks for the fine default, so without this a click on a
    # capped part opens raw JSON with no notice. Same text the API and the CLI refuse with.
    fine = fine_stl_refusal(p.d, p.pitch, p.length, p.left_hand)
    if fine is not None:
        warnings.append(fine)
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


def download_refusal(p: FastenerParams, fmt: str, quality: str) -> str | None:
    """The reason a download of `p` is refused before any build, or None.

    The one rule `app._serve` and `screw export` share (FRNT-05 parity). Kernel-free, so a
    refused request never reaches the cache, the admission slot or the pool. Only the fine
    STL is ever refused (D-02): the preview STL and the STEP of the same part are served.
    Dispatches with `isinstance` like `derive`: a registered kind without an entry raises
    TypeError, whatever `fmt` and `quality` say, so the registry test catches it.
    """
    if isinstance(p, BoltParams):
        if fmt == "stl" and quality == "fine":
            return fine_stl_refusal(p.d, p.pitch, p.length, p.left_hand)
        return None
    raise TypeError(f"no download rule for kind {p.kind!r}")
