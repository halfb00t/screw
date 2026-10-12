"""The numbers the tool prints about a part: pure maths, free of the CAD kernel and the logger.

`derive()` runs on every keystroke in the UI, so this package never imports `cadquery`,
`logging` or `screw.records` (import-linter contracts 2 and 4). A value that cannot be
computed honestly is left out of `rows` and explained in `warnings` -- never a plausible
number (L02, D-15).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field

from screw.calc.thread import (
    MIN_TAIL_MM,
    bolt_closed_volume,
    built_thread_length,
    fine_stl_refusal,
    thread_depth,
    thread_length_conflict,
    turns_of,
)
from screw.params import BoltParams, FastenerParams

# The values the model route takes for `fmt` and `quality`. app.py keeps its own Literals (it
# imports no solid names, contract 5); tests/test_api.py pins the two together through OpenAPI.
DownloadFormat = Literal["stl", "step"]
DownloadQuality = Literal["preview", "fine"]

PROFILE = "ISO 68-1:2023 basic profile"

# The standing entry on every info document (D-04, D-18): the thread ends are plain planar cuts
# and the head has no under-head fillet, so nobody should cut metal to it as a product. Phase 5
# rewrites it when the ends land; Phase 6 removes the last clause at release.
STANDING_WARNING = "plain-cut thread ends, no tip chamfer or under-head fillet; not a product build"

# The panel headings (D-17); `calc.presets` files the rows a matched row adds under the same two.
SHANK = "Shank and thread"
HEAD = "Head"
PART = "Part"

# The one warning for a part that is no catalogue row (INFO-03, D-18, L02).
NO_ROW_WARNING = ("no ISO 4014:2022 or ISO 4017:2022 row matches these fields; "
                  "row values not reported")


class InfoRow(BaseModel):
    """One labelled number. The UI renders rows generically; it never reads a row by key."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    value: float
    unit: str
    group: str = Field(
        description="the panel heading this row sits under; the page renders one heading per "
                    "distinct group in server order and reads no group name (D-17)")


class PresetMatch(BaseModel):
    """Whether the part is a catalogue row; the page composes its badge from these keys (D-09)."""

    model_config = ConfigDict(frozen=True)

    status: Literal["exact", "custom"] = Field(
        description="exact while every field a catalogue row defines equals that row, else custom")
    id: str | None = Field(description="the matching row's id, null when custom")
    display: str | None = Field(description="the matching row's display text, null when custom")


class Download(BaseModel):
    """One download the model route serves, and whether the shared rule refuses it before any build.

    The page links, per format, the first entry not refused and reads no warning (D-10).
    """

    model_config = ConfigDict(frozen=True)

    format: DownloadFormat
    quality: DownloadQuality
    refusal: str | None = Field(
        description="the sentence the model route answers with a 422 and `screw export` prints "
                    "after `error:` (exit 2), from `download_refusal`; null when that rule does "
                    "not refuse this download on the parameters alone, which is not a promise "
                    "that the build succeeds (a part the builder refuses is still a 422 "
                    "`build_error` on every format)")


class PartInfo(BaseModel):
    """The info document: identical on `/api/<kind>/info` and `screw info <kind>` (D-15)."""

    model_config = ConfigDict(frozen=True)

    kind: str
    rows: list[InfoRow]
    warnings: list[str]
    designation: str | None = Field(
        description="the standard's designation of the part, null when it matches no row or is "
                    "left-hand (the standards give no left-hand form); never a property class")
    preset: PresetMatch | None = Field(
        description="whether the part is a catalogue row; null for a kind without a catalogue")
    notes: list[str] = Field(
        description="one-line notes about the matched row, present only on an exact match; the "
                    "page shows them after the warnings in their own style (D-20)")
    downloads: list[Download] = Field(
        description="every format and quality the model route serves, in the order the page "
                    "offers them (per format the route's default quality first), each with the "
                    "reason the route and `screw export` refuse it, or null")


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
    # Imported here, never at module top: importing `screw.calc.thread` runs this file, and a
    # table import above would load the tables behind every rebuilt link (contract 6,
    # tests/test_import_boundaries.py).
    from screw.calc.presets import designation_for, match, notes, row_values

    # One built thread for every row, warning and cap below (D-27): never recomputed.
    t = built_thread_length(p.thread_length, p.length)
    row = match(p)
    # The cited values of the matched row, spliced in after the row each belongs beside (D-18):
    # the thread's after minor_diameter, the head's after k. A part that is no row gets none.
    cited = [] if row is None else row_values(row)
    after = {"minor_diameter": [r for r in cited if r.group == SHANK],
             "k": [r for r in cited if r.group != SHANK]}
    rows = [
        InfoRow(key="d", label="Diameter", value=p.d, unit="mm", group=SHANK),
        InfoRow(key="pitch", label="Pitch", value=p.pitch, unit="mm", group=SHANK),
        InfoRow(key="length", label="Length", value=p.length, unit="mm", group=SHANK),
    ]
    warnings = [STANDING_WARNING]
    # Every number below is the pinned profile's or an exact reading of the user's own fields,
    # never the kernel's Volume() (D-05). The bounds keep validated input finite, so a row is
    # left out only for an instance that skipped validation (model_construct); but "no
    # non-finite number leaves derive()" is this function's own contract (D-15): d=1e200
    # overflows a float on the way (F2) and `Fraction(repr(inf))` raises. The rows are in the
    # order the page shows them: the shank's, then the head's, the volume last (D-18).
    computed: list[tuple[str, str, str, str, str, Callable[[], float]]] = [
        ("thread_length", SHANK, "Thread length (built)", "mm", "min(thread_length, length)",
         lambda: t),
        ("shank_length", SHANK, "Plain shank length", "mm", "length - thread_length (built)",
         lambda: p.length - t),
        ("turns", SHANK, "Turns", "", "thread_length (built) / pitch",
         lambda: turns_of(t, p.pitch)),
        ("thread_depth", SHANK, f"Thread depth ({PROFILE})", "mm",
         "5H/8 with H = (sqrt(3) / 2) * pitch", lambda: thread_depth(p.pitch)),
        ("minor_diameter", SHANK, f"Minor diameter ({PROFILE})", "mm", "d - 2 * (5H/8)",
         lambda: p.d - 2 * thread_depth(p.pitch)),
        ("s", HEAD, "Across flats", "mm", "s", lambda: p.s),
        ("across_corners", HEAD, "Across corners, geometric (s / cos 30°)", "mm", "s / cos 30°",
         lambda: p.s / math.cos(math.pi / 6)),
        ("k", HEAD, "Head height", "mm", "k", lambda: p.k),
        ("volume", PART, "Volume (closed form)", "mm³",
         "the closed form section_area(d, pitch) * thread_length (built) "
         "+ pi * (d / 2)^2 * shank_length + (sqrt(3) / 2) * s^2 * k",
         lambda: bolt_closed_volume(p.d, p.pitch, p.length, p.s, p.k, t)),
    ]
    # IN-01, L02: below `MIN_TAIL_MM` of built thread the builder refuses the part, so a turns or
    # volume row would be a number for a bolt nobody can make. They are left out and the warning
    # below says why; every other row is an exact reading of the user's own fields.
    buildable = t >= MIN_TAIL_MM
    for key, group, label, unit, formula, compute in computed:
        if not buildable and key in ("turns", "volume"):
            continue
        try:
            value = compute()
        except (OverflowError, ValueError):
            value = math.nan
        if math.isfinite(value):
            rows.append(InfoRow(key=key, label=label, value=value, unit=unit, group=group))
        else:
            warnings.append(f"{key} not reported: {formula} is not a finite number "
                            "for these parameters")
        rows.extend(after.get(key, []))
    # The page's Download STL link asks for the fine default, so without this a click on a
    # capped part opens raw JSON with no notice. Same text the API and the CLI refuse with.
    if (short := _thread_length_warning(p, t)) is not None:
        warnings.append(short)
    if not buildable:
        warnings.append(f"thread_length and length: a thread of {t:g} mm is shorter than the "
                        f"{MIN_TAIL_MM:g} mm the builder can model, so this part is not built; "
                        "turns and volume not reported")
    if row is None:
        # L02: no row means no row value and no nearest row; the part is built from its fields.
        warnings.append(NO_ROW_WARNING)
    # A refused download is also a warning (L02, never a silent downgrade): the page offers the
    # next served quality in place of a refused one and labels it (plan 04-16), and this sentence
    # is the reason, on the page under the buttons, on the API and in `screw info`. Read from the
    # same call as `downloads`, so the warning and the member cannot disagree.
    downloads = _downloads(p)
    for reason in dict.fromkeys(e.refusal for e in downloads if e.refusal is not None):
        warnings.append(reason)
    if row is None:
        preset = PresetMatch(status="custom", id=None, display=None)
        designation = None
        row_notes: list[str] = []
    else:
        preset = PresetMatch(status="exact", id=row.id, display=row.display)
        designation = designation_for(p, row)
        row_notes = notes(row)
    return PartInfo(kind=p.kind, rows=rows, warnings=warnings, designation=designation,
                    preset=preset, notes=row_notes, downloads=downloads)


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


# The page's preference: per format the route's default quality first, then the coarser preview it
# falls back to (`solid.TESSELLATION`, INTERIM: preview 0.08 mm and 0.5 rad, fine 0.01 mm and
# 0.1 rad). STEP ignores quality in `solid._write_export`, but the route accepts both, so both are
# listed and both are true. tests/test_api.py pins the set and the first quality to the route.
_DOWNLOADS: tuple[tuple[DownloadFormat, DownloadQuality], ...] = (
    ("stl", "fine"), ("stl", "preview"), ("step", "fine"), ("step", "preview"))


def _downloads(p: FastenerParams) -> list[Download]:
    """The download state of `p`: one entry per `_DOWNLOADS`, refused by the rule `_serve` and
    `cmd_export` call, so the document, the route and the CLI cannot disagree. Kind-generic: the
    rule dispatches by kind, and every kind's info builder must call this (the member is required).
    """
    return [Download(format=fmt, quality=quality, refusal=download_refusal(p, fmt, quality))
            for fmt, quality in _DOWNLOADS]


class ExplicitConflict(NamedTuple):
    """A refusal between two values the request named: the error type the API answers with,
    the fields it names, and the one sentence both front ends print."""

    type: str
    fields: tuple[str, ...]
    msg: str


def explicit_conflict(kind: str, values: Mapping[str, object]) -> ExplicitConflict | None:
    """The rule between two explicit values of `kind`, or None when they agree (D-25).

    Runs at the request boundary, before any model exists: FastAPI copies every field default
    into the query model and pydantic then cannot tell an explicit value from a default
    (04-RESEARCH Alert 1), so `values` holds only what the request named -- the raw query
    keys on the API, the flags given on the CLI. Dispatched by kind name the way `derive` and
    `download_refusal` dispatch by type: a registered kind without an entry raises, so a new
    kind states its rule (or `None`) instead of inheriting the bolt's or escaping it
    (04-REVIEW WR-02). A value that is not a float is the model's to refuse, naming the field.
    """
    try:
        rule = _EXPLICIT_CONFLICTS[kind]
    except KeyError:
        raise TypeError(f"no explicit-conflict rule registered for kind {kind!r}") from None
    return None if rule is None else rule(values)


def _bolt_explicit_conflict(values: Mapping[str, object]) -> ExplicitConflict | None:
    length, thread_length = values.get("length"), values.get("thread_length")
    if not (isinstance(length, float) and isinstance(thread_length, float)):
        return None
    msg = thread_length_conflict(length, thread_length)
    if msg is None:
        return None
    return ExplicitConflict("thread_length_conflict", ("thread_length", "length"), msg)


# One entry per registered kind (tests/test_calc.py walks `KINDS`); `None` is a kind with no
# rule between its explicit values.
_EXPLICIT_CONFLICTS: dict[str, Callable[[Mapping[str, object]], ExplicitConflict | None] | None] = {
    BoltParams.kind: _bolt_explicit_conflict,
}
