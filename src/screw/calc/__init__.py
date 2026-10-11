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

from screw.calc.thread import (
    MIN_TAIL_MM,
    bolt_closed_volume,
    built_thread_length,
    fine_stl_refusal,
    thread_depth,
    turns_of,
)
from screw.params import BoltParams, FastenerParams

PROFILE = "ISO 68-1:2023 basic profile"

# The standing entry on every info document (D-04, D-18): the thread ends are plain planar cuts
# and the head has no under-head fillet, so nobody should cut metal to it as a product. Phase 5
# rewrites it when the ends land; Phase 6 removes the last clause at release.
STANDING_WARNING = "plain-cut thread ends, no tip chamfer or under-head fillet; not a product build"


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


def _thread_length_warning(p: BoltParams, t: float) -> str | None:
    """Why the thread built is not the thread asked for, or None when it is (D-08, D-25, D-27).

    The text says `(default)` when the value equals the field's frozen default: that is the only
    thing a model can test, so an explicit `thread_length` equal to the default reads `(default)`
    only on direct Python construction; the API and the CLI refuse two explicit values with
    plan 04-05's 422 first.
    """
    if p.thread_length > p.length:
        default = BoltParams.model_fields["thread_length"].default
        mark = " (default)" if p.thread_length == default else ""
        return (f"thread_length {p.thread_length:g}{mark} exceeds length {p.length:g}: "
                "thread built to the full length")
    if p.thread_length < p.length and t == p.length:
        return (f"thread_length {p.thread_length:g} leaves a plain shank of "
                f"{p.length - p.thread_length:g} mm, shorter than the {MIN_TAIL_MM:g} mm the "
                "builder can model: thread built to the full length")
    return None


def _bolt(p: BoltParams) -> PartInfo:
    # One built thread for every row, warning and cap below (D-27): never recomputed.
    t = built_thread_length(p.thread_length, p.length)
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
    # overflows a float on the way (F2) and `Fraction(repr(inf))` raises. The rows are in the
    # order the page shows them: the shank's, then the head's, the volume last (D-18).
    computed: list[tuple[str, str, str, str, Callable[[], float]]] = [
        ("thread_length", "Thread length (built)", "mm", "min(thread_length, length)",
         lambda: t),
        ("shank_length", "Plain shank length", "mm", "length - thread_length (built)",
         lambda: p.length - t),
        ("turns", "Turns", "", "thread_length (built) / pitch", lambda: turns_of(t, p.pitch)),
        ("thread_depth", f"Thread depth ({PROFILE})", "mm", "5H/8 with H = (sqrt(3) / 2) * pitch",
         lambda: thread_depth(p.pitch)),
        ("minor_diameter", f"Minor diameter ({PROFILE})", "mm", "d - 2 * (5H/8)",
         lambda: p.d - 2 * thread_depth(p.pitch)),
        ("s", "Across flats", "mm", "s", lambda: p.s),
        ("across_corners", "Across corners, geometric (s / cos 30°)", "mm", "s / cos 30°",
         lambda: p.s / math.cos(math.pi / 6)),
        ("k", "Head height", "mm", "k", lambda: p.k),
        ("volume", "Volume (closed form)", "mm³",
         "the closed form section_area(d, pitch) * thread_length (built) "
         "+ pi * (d / 2)^2 * shank_length + (sqrt(3) / 2) * s^2 * k",
         lambda: bolt_closed_volume(p.d, p.pitch, p.length, p.s, p.k, t)),
    ]
    # IN-01, L02: below `MIN_TAIL_MM` of built thread the builder refuses the part, so a turns or
    # volume row would be a number for a bolt nobody can make. They are left out and the warning
    # below says why; every other row is an exact reading of the user's own fields.
    buildable = t >= MIN_TAIL_MM
    for key, label, unit, formula, compute in computed:
        if not buildable and key in ("turns", "volume"):
            continue
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
    if (short := _thread_length_warning(p, t)) is not None:
        warnings.append(short)
    if not buildable:
        warnings.append(f"thread_length and length: a thread of {t:g} mm is shorter than the "
                        f"{MIN_TAIL_MM:g} mm the builder can model, so this part is not built; "
                        "turns and volume not reported")
    fine = fine_stl_refusal(p.d, p.pitch, t, p.left_hand)
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
            return fine_stl_refusal(
                p.d, p.pitch, built_thread_length(p.thread_length, p.length), p.left_hand)
        return None
    raise TypeError(f"no download rule for kind {p.kind!r}")
