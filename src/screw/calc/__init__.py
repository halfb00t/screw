"""The numbers the tool prints about a part: pure maths, free of the CAD kernel and the logger.

`derive()` runs on every keystroke in the UI, so this package never imports `cadquery`,
`logging` or `screw.records` (import-linter contracts 2 and 4). A value that cannot be
computed honestly is left out of `rows` and explained in `warnings` -- never a plausible
number (L02, D-15).
"""

from __future__ import annotations

import contextlib
import math
from collections.abc import Callable, Mapping
from typing import Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field

from screw.calc.printability import measured_range_warning, printability_warning
from screw.calc.thread import (
    MIN_TAIL_MM,
    TIP_ANGLE_DEG,
    axial_play,
    basic_minor_diameter,
    bolt_end_closed_volume,
    built_thread_length,
    end_depths,
    fillet_radius,
    fine_stl_refusal,
    flank_normal_gap,
    nut_end_closed_volume,
    nut_fine_stl_refusal,
    pitch_diameter,
    thread_depth,
    thread_length_conflict,
    tip_cone_fits,
    tip_cone_length,
    turns_of,
)
from screw.params import BoltParams, FastenerParams, NutParams

# The values the model route takes for `fmt` and `quality`. app.py keeps its own Literals (it
# imports no solid names, contract 5); tests/test_api.py pins the two together through OpenAPI.
DownloadFormat = Literal["stl", "step"]
DownloadQuality = Literal["preview", "fine"]

PROFILE = "ISO 68-1:2023 basic profile"

# The note on a matched ISO 4017 screw (D-11, D-18): the thread runs to the head, so there is no
# plain shank to fillet. A note, not a warning: it is what the standard's part is, nothing to fix.
NO_FILLET_NOTE = "no under-head fillet: the thread runs to the head (ISO 4017:2022)"

# The standing entry on every info document (D-04, D-18): it names the ends the builder models
# (L15, the bolt tip cone, the under-head fillet and the nut's countersinks and chamfers) and says
# they are nominal, so nobody should cut metal to it as a product. The first release, after Phase 7,
# removes the last clause (06 D-15).
STANDING_WARNING = (
    "ends modelled per L15: bolt tip chamfer, under-head fillet on an ISO 4014 plain shank, "
    "nut lead-in countersinks and face chamfers; nominal, not toleranced; not a product build")

# The panel headings (D-17); `calc.presets` files the rows a matched row adds under the same two.
SHANK = "Shank and thread"
HEAD = "Head"
PART = "Part"
# The nut's panel headings (D-17): its own thread rows, the nut's body, and what the pair adds.
THREAD = "Thread"
NUT = "Nut"
PAIR = "Pair"
# The bought-part limits' heading (INFO-02): compared byte for byte on the API, the CLI and the
# parity test, so it is one ASCII string, semicolon and spaces included. It appears only on an
# exact ISO 262 size with a 05-08 limits row and never as an empty heading.
LIMITS = "limits for a bought part; this model is nominal and not toleranced"

# The one warning for a part that is no catalogue row (INFO-03, D-18, L02).
NO_ROW_WARNING = ("no ISO 4014:2022 or ISO 4017:2022 row matches these fields; "
                  "row values not reported")

# The one warning for a nut that is no catalogue row (L02). It names the document actually read,
# GOST ISO 4032-2014 (ISO 4032:2012), not the ISO edition L14 deferred buying (L14 Citations). The
# text prints no M7, so an M7 nut reads this too.
NUT_NO_ROW_WARNING = ("no GOST ISO 4032-2014 (ISO 4032:2012) row matches these fields; "
                      "row values not reported")

# The label for a nut at M18, read from the cited record and never from a kernel call (D-20, SC4,
# SC6). The campaign `2026-10-08-a-pair` (K = 3) found size M18 not falsifiable on either hand, and
# L11's revision direction keeps the pair verdict `inconclusive` there, so the panel says so before
# anybody runs the proof. The key is the campaign's own, compared exactly: 18.0 and 2.5 are the
# ISO 262 M18 literals, and a nut one float off the size is not the size the campaign measured.
M18_KEY = (18.0, 2.5)
M18_NOTE = "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)"


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


class Counterpart(BaseModel):
    """The other part that mates with this one: its kind and the fields this part can carry to it.

    `fields` holds the shared d, pitch and left_hand, and the catalogue row's own size values
    when (d, pitch) is a row of the other kind. Never `clearance`, `length` or `thread_length`:
    the clearance is the nut's own field with the L17 default and is never carried from a bolt
    (D-02), and a length is the user's choice of bolt (TYPE-04).
    """

    model_config = ConfigDict(frozen=True)

    kind: str
    # The smart union keeps `left_hand` a JSON boolean instead of coercing it to 1.0 (RESEARCH F6).
    fields: dict[str, float | bool]


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
        description="one-line notes about the matched row, present only on an exact match, and "
                    "for a nut the M18 pair-proof label, keyed on the size alone; the page "
                    "shows them after the warnings in their own style (D-20)")
    downloads: list[Download] = Field(
        description="every format and quality the model route serves, in the order the page "
                    "offers them (per format the route's default quality first), each with the "
                    "reason the route and `screw export` refuse it, or null")
    counterpart: Counterpart | None = Field(
        description="the part this one mates with: a bolt's nut and a nut's bolt, with the "
                    "shared d, pitch and left_hand and, on a catalogue size, that row's own "
                    "values; never the clearance, which the user types (D-02); null for a kind "
                    "without a counterpart")


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
    from screw.calc.presets import (
        bolt_limits_for,
        counterpart_for,
        designation_for,
        match,
        notes,
        row_values,
    )

    # One built thread for every row, warning and cap below (D-27): never recomputed.
    t = built_thread_length(p.thread_length, p.length)
    row = match(p)
    # The ends the builder cuts and fuses, decided once here as it decides them (D-27): the tip
    # cone when the built thread is longer than it, the ring when (d, pitch) has a cited radius
    # and the plain shank is at least that long.
    tip = tip_cone_fits(p.pitch, t)
    ring = fillet_radius(p.d, p.pitch, p.length, t)
    # The cited values of the matched row, spliced in after the row each belongs beside (D-18):
    # the thread's after the pitch diameter, the head's after k. A part that is no row gets none.
    # The limits group follows the thread's rows and precedes the head's, so it is one contiguous
    # heading; it depends on (d, pitch) alone, so an ISO 262 size that is no catalogue row has it.
    cited = [] if row is None else row_values(row)
    after = {"pitch_diameter": [r for r in cited if r.group == SHANK]
             + bolt_limits_for(p.d, p.pitch),
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
        ("pitch_diameter", SHANK, f"Pitch diameter d2 ({PROFILE})", "mm",
         "d - 3H/4 with H = (sqrt(3) / 2) * pitch", lambda: pitch_diameter(p.d, p.pitch)),
        ("s", HEAD, "Across flats", "mm", "s", lambda: p.s),
        ("across_corners", HEAD, "Across corners, geometric (s / cos 30°)", "mm", "s / cos 30°",
         lambda: p.s / math.cos(math.pi / 6)),
        ("k", HEAD, "Head height", "mm", "k", lambda: p.k),
        ("volume", PART, "Volume (closed form)", "mm³",
         "the closed form section_area(d, pitch) * thread_length (built) "
         "+ pi * (d / 2)^2 * shank_length + (sqrt(3) / 2) * s^2 * k, less the tip cone "
         "(the thread cut at 45° from the end face from the minor diameter) and plus the "
         "under-head fillet ring where the thread has a plain shank at a cited ISO 4014 size",
         lambda: bolt_end_closed_volume(p.d, p.pitch, p.length, p.s, p.k, t, tip, ring)),
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
    if buildable and not tip:
        # L02: capped, not a thinner tip. The builder cuts no cone and the volume row has none.
        warnings.append(f"thread_length: the built thread of {t:g} mm is not longer than the "
                        f"{tip_cone_length(p.pitch, TIP_ANGLE_DEG):g} mm tip cone, so no tip "
                        "cone is cut")
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
    # D-13: below the size run 2 printed, both kinds say so; nothing is capped (L02).
    if (below := printability_warning(p.d, p.pitch)) is not None:
        warnings.append(below)
    counterpart, off_row = counterpart_for(p)
    if off_row is not None:
        warnings.append(off_row)
    if row is None:
        preset = PresetMatch(status="custom", id=None, display=None)
        designation = None
        row_notes: list[str] = []
    else:
        preset = PresetMatch(status="exact", id=row.id, display=row.display)
        designation = designation_for(p, row)
        row_notes = notes(row)
        if row.standard == "ISO 4017":
            row_notes.append(NO_FILLET_NOTE)
    return PartInfo(kind=p.kind, rows=rows, warnings=warnings, designation=designation,
                    preset=preset, notes=row_notes, downloads=downloads, counterpart=counterpart)


def _nut(p: NutParams) -> PartInfo:
    # Imported here for the reason `_bolt` gives (contract 6).
    from screw.calc.presets import (
        counterpart_for,
        match_nut,
        nut_designation_for,
        nut_limits_for,
        nut_notes,
        nut_row_values,
    )

    # Same contract as `_bolt` (D-15): every number is a reading of the user's own fields or the
    # closed form, never the kernel's Volume(), and none that is not finite leaves this function.
    row = match_nut(p)
    # The cited values of the matched row follow the across-corners row (D-17); a nut that is no
    # row gets none, and no nearest row stands in for it (L02).
    cited = [] if row is None else nut_row_values(row)
    # The limits group follows the Thread rows, on the exact ISO 262 size alone (INFO-02).
    after = {"across_corners": cited, "minor_diameter": nut_limits_for(p.d, p.pitch)}
    computed: list[tuple[str, str, str, str, str, Callable[[], float]]] = [
        ("d", THREAD, "Diameter", "mm", "d", lambda: p.d),
        ("pitch", THREAD, "Pitch", "mm", "pitch", lambda: p.pitch),
        ("thread_depth", THREAD, f"Thread depth ({PROFILE})", "mm",
         "5H/8 with H = (sqrt(3) / 2) * pitch", lambda: thread_depth(p.pitch)),
        ("pitch_diameter", THREAD, f"Pitch diameter D2 ({PROFILE})", "mm",
         "D2 = d - 3H/4 with H = (sqrt(3) / 2) * pitch", lambda: pitch_diameter(p.d, p.pitch)),
        ("minor_diameter", THREAD, f"Minor diameter D1 ({PROFILE})", "mm",
         "D1 = d - 5H/4 with H = (sqrt(3) / 2) * pitch",
         lambda: basic_minor_diameter(p.d, p.pitch)),
        ("s", NUT, "Across flats", "mm", "s", lambda: p.s),
        ("across_corners", NUT, "Across corners, geometric (s / cos 30°)", "mm", "s / cos 30°",
         lambda: p.s / math.cos(math.pi / 6)),
        ("m", NUT, "Height", "mm", "m", lambda: p.m),
        ("clearance", PAIR, "Clearance (radial)", "mm", "clearance", lambda: p.clearance),
        # The pair's numbers are closed forms of the clearance, m and pitch only: no kernel call,
        # no verdict and no mesh-derived value (PAIR-04, D-19). Fixed order, unrounded.
        ("clearance_diametral", PAIR, "Clearance (diametral, 2c)", "mm", "2 * clearance",
         lambda: 2 * p.clearance),
        ("flank_gap", PAIR, "Flank-normal gap (closed form)", "mm",
         "clearance * sin 30°", lambda: flank_normal_gap(p.clearance)),
        ("axial_play", PAIR, "Axial play, both flanks (closed form)", "mm",
         "2 * clearance * tan 30°", lambda: axial_play(p.clearance)),
        ("nut_major_diameter", PAIR, "Nut major diameter (d + 2c)", "mm",
         "d + 2 * clearance", lambda: p.d + 2 * p.clearance),
        ("nut_pitch_diameter", PAIR, "Nut pitch diameter (D2 + 2c)", "mm",
         "D2 + 2 * clearance", lambda: pitch_diameter(p.d, p.pitch) + 2 * p.clearance),
        ("nut_minor_diameter", PAIR, "Nut minor diameter (D1 + 2c)", "mm",
         "D1 + 2 * clearance", lambda: basic_minor_diameter(p.d, p.pitch) + 2 * p.clearance),
        ("engagement_turns", PAIR, "Engagement (m / P)", "turns", "m / pitch",
         lambda: turns_of(p.m, p.pitch)),
        ("volume", PART, "Volume (closed form)", "mm³",
         "the closed form (sqrt(3) / 2) * s^2 * m - section_area(d, pitch, clearance) * m, "
         "less the two lead-in countersinks (90° included, opening to 1.16 * d / 2) and the two "
         "face chamfers (30° from the face, from s / 2) at the depths this part is cut to",
         lambda: nut_end_closed_volume(p.d, p.pitch, p.s, p.m, p.clearance)),
    ]
    rows: list[InfoRow] = []
    warnings = [STANDING_WARNING]
    # D-04, PAIR-03: a clearance of 0 or below is a part the user may ask for and build, but the
    # kernel's pair verdict cannot be `proven` for it, so every front end says so out loud. The
    # test is `<= 0`, not `< epsilon`: 5e-324 is positive and carries no warning.
    if p.clearance <= 0:
        warnings.append(f"clearance {p.clearance:g} is not positive: "
                        "the pair cannot be proven (PAIR-03)")
    # R3, R5, L02: a countersink or chamfer the builder cuts shallower than its model, or leaves
    # out, because the user's own fields leave no room, is said here, naming the field.
    # Only a model_construct instance can fail here; the volume row below then says it is not
    # reported.
    with contextlib.suppress(OverflowError, ValueError):
        warnings.extend(end_depths(p.d, p.pitch, p.clearance, p.s, p.m)[2])
    for key, group, label, unit, formula, compute in computed:
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
    if row is None:
        warnings.append(NUT_NO_ROW_WARNING)
    downloads = _downloads(p)
    for reason in dict.fromkeys(e.refusal for e in downloads if e.refusal is not None):
        warnings.append(reason)
    # D-09, R6: the clearance default was measured on M6 to M12 only. Size alone decides, so the
    # default and a typed clearance read alike; nothing is capped and no row is dropped (L02).
    outside = measured_range_warning(p.d, p.pitch)
    if outside is not None:
        warnings.append(outside)
    # D-13: after the D-09 sentence, so a nut crossing both carries two separate sentences.
    if (below := printability_warning(p.d, p.pitch)) is not None:
        warnings.append(below)
    # The M18 note keys on (d, pitch) alone, so it reads on a nut that is no catalogue row too.
    m18 = [M18_NOTE] if (p.d, p.pitch) == M18_KEY else []
    counterpart, off_row = counterpart_for(p)
    if off_row is not None:
        warnings.append(off_row)
    if row is None:
        return PartInfo(kind=p.kind, rows=rows, warnings=warnings, designation=None,
                        preset=PresetMatch(status="custom", id=None, display=None), notes=m18,
                        downloads=downloads, counterpart=counterpart)
    return PartInfo(kind=p.kind, rows=rows, warnings=warnings,
                    designation=nut_designation_for(p, row),
                    preset=PresetMatch(status="exact", id=row.id, display=row.display),
                    notes=[*nut_notes(row), *m18], downloads=downloads, counterpart=counterpart)


def derive(p: FastenerParams) -> PartInfo:
    """The info document for `p`.

    Dispatches with `isinstance`, not a `match` over a closed union: base-typed callers
    (pool, app, tests) would otherwise need a union threaded through every signature. A
    registered kind without an entry here raises TypeError and fails the registry test
    that derives every `KINDS` entry, not a user.
    """
    if isinstance(p, BoltParams):
        return _bolt(p)
    if isinstance(p, NutParams):
        return _nut(p)
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
    if isinstance(p, NutParams):
        # The nut's own caps (run 2026-10-21-nut-fine-caps-amended, R16 and R17), never the rods'.
        if fmt == "stl" and quality == "fine":
            return nut_fine_stl_refusal(p.d, p.pitch, p.m, p.clearance, p.left_hand)
        return None
    raise TypeError(f"no download rule for kind {p.kind!r}")


def download_name(p: FastenerParams, fmt: str, quality: str) -> str:
    """The file name a download of `p` is saved under: the one rule `app._serve` and
    `screw export` share (D-22, R9).

    A preview STL carries `_preview` before its extension, because the mesh it holds is the
    coarse one (INTERIM 0.08 mm deflection against the fine 0.01 mm, `solid.TESSELLATION`) and a
    file opened a month later has only its name to say so (L02). The fine STL and the STEP keep
    `<slug>.<ext>`: the STEP has no tessellation, and `quality` does not change it. `slug()` holds
    only letters, digits and `_.+-` (T-01-06), so the name is filename-safe by construction.
    """
    suffix = "_preview" if fmt == "stl" and quality == "preview" else ""
    return f"{p.slug()}{suffix}.{fmt}"


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
    # No two explicit nut fields contradict each other; `nut_too_thin` is a model rule (D-13).
    NutParams.kind: None,
}
