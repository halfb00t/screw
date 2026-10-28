"""Fastener parameters: one validated, hashable model per kind, shared by the API, web UI
and CLI.

All lengths are millimetres. Field metadata (group, unit, step) is exported through the
JSON schema and drives the web form and the CLI flags, so a field added here shows up in
both automatically. Each kind is a class registered in `KINDS`; adding a kind is one class
and one registry entry, never an edit to the form or the flag generator.
"""

from __future__ import annotations

from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.config import JsonDict
from pydantic_core import PydanticCustomError

# Kernel outer walls on the size of a part, in mm (07 D-08, rule R8 of `07-SWEEP-PROTOCOL.md`, with
# the owner's ruling G27): for each field the largest decade of 1e3, 1e4 and 1e5 mm at which the
# kernel built the field's ceiling corner on linux/amd64 on the GitHub runner, read once in walls
# run 40646134133 and again in 5 repetitions in confirm run 40678150220. A wall is where the kernel
# refuses or crashes, never a budget: what a build costs is bounded by the cost model (L21) and the
# container limit (L22), set separately. The value of a field is what its corner tested, which is
# not always the decade: the head rule (s > d) and the thin-nut rule (s > d + 2 c) admit nothing
# between the tested value and the decade. A value above a wall is a 422 naming the field, never a
# clamp (L02). The F1 cylinder table the 1e5 first came from (d=1e5, 9,932 triangles, 553 MiB on
# macOS arm64) bounded a plain cylinder and no thread; no number below comes from it.
#
# The value the most fields share. Bolt `s` and nut `s` are at 1e3 and so is every other field's
# first decade, and 1e3, 1e4 and 1e5 are each the value of two fields, a tie that goes to the lower
# (R8). Bolt `s`: `ceiling-bolt-s-1000` and `ceiling-bolt-d-1000` ok in 5 of 5 repetitions, the
# `d` reading at 1e4 refused in 5 of 5. Nut `s`: `ceiling-nut-s-1000` and the lead-in nuts M2, M8
# and M14 at s 1e3 ok in 5 of 5, `nutlead-M2-s10000` refused in 5 of 5. Nut `d` has no wall of its
# own and stays under this value (G27): `ceiling-nut-d-1000` read ok once and `capped` (cost) in 5
# of 5 repetitions, `ceiling-nut-d-10000` refused in 5 of 5, so 1e3 lies below its first refused
# decade, 1e4, and the cost model's admission bounds a large nut.
MAX_FIELD_MM = 1e3
# Bolt `d`: `ceiling-bolt-d-1000` (d 999.999, the largest 6-figure value under 1e3, s 1e3) ok in 5
# of 5; `ceiling-bolt-d-10000` refused in 5 of 5. s must exceed d, so 1e3 itself was never tested.
MAX_BOLT_D_MM = 999.999
# Bolt `length`: `ceiling-bolt-length-10000` and `ceiling-bolt-thread-10000` ok in 5 of 5;
# `ceiling-bolt-length-100000` refused in 5 of 5.
MAX_BOLT_LENGTH_MM = 1e4
# Bolt `k`: `ceiling-bolt-k-100000` ok in 5 of 5. The lifted reading at 1e6
# (`beyond-bolt-k-1000000`) was ok too and awards nothing: a reading past a cap raises no wall (R3).
MAX_BOLT_K_MM = 1e5
# Bolt `thread_length`: `ceiling-bolt-thread-100000` ok in 5 of 5. The lifted reading at 1e6 was
# `capped` in 5 of 5 and awards nothing.
MAX_BOLT_THREAD_LENGTH_MM = 1e5
# Nut `m`: `ceiling-nut-m-10000` ok in 5 of 5; `ceiling-nut-m-100000` killed (cost) in 5 of 5, which
# cannot raise a wall.
MAX_NUT_M_MM = 1e4
# Nut `clearance`: `ceiling-nut-clearance-1000` (d 6, s 1e3, clearance 496.999, the largest 6-figure
# value under (1e3 - 6) / 2) ok in 5 of 5; `ceiling-nut-clearance-10000` refused in 5 of 5.
MAX_NUT_CLEARANCE_MM = 496.999


def _f[T](default: T, *, gt: float, le: float | None = None, title: str, group: str,
          unit: str = "", step: float | None = None, help: str = "") -> T:
    # allow_inf_nan=False is what refuses `inf`: with `gt=0` alone, d=inf passes
    # (verified against pydantic 2.13.5, 01-RESEARCH.md Pattern 1); with it, inf and nan
    # are a 422 `finite_number`.
    extra: JsonDict = {"group": group, "unit": unit}
    if step is not None:
        extra["step"] = step
    return Field(default, gt=gt, le=le, allow_inf_nan=False, title=title, description=help,
                 json_schema_extra=extra)


def _diameter(le: float) -> float:
    """The nominal diameter field, with its own wall. Bolt `d` is redeclared with `MAX_BOLT_D_MM`,
    so the field is one definition and the shared base keeps `MAX_FIELD_MM`."""
    return _f(6.0, gt=0, le=le, title="Diameter", group="Size", unit="mm", step=0.1,
              help="Nominal (major) diameter of the shank.")


def _free(default: float, *, le: float, title: str, group: str, unit: str = "",
          step: float | None = None, help: str = "") -> float:
    # The sibling of `_f` for a field with a default and no lower bound: a nominal or interference
    # fit is a value the user may ask for (D-04), so any finite value up to `le` is a legal input
    # and the schema carries `default` but no `exclusiveMinimum`, which `_f`'s `gt` would add (and
    # the form would turn into a `min`). `allow_inf_nan=False` refuses inf and nan as in `_f`.
    extra: JsonDict = {"group": group, "unit": unit}
    if step is not None:
        extra["step"] = step
    free: float = Field(default, le=le, allow_inf_nan=False, title=title, description=help,
                        json_schema_extra=extra)
    return free     # typed here: `Field` returns Any, which --strict refuses to return


def _angle(default: float, *, ge: float, lt: float, title: str, group: str, unit: str = "",
           step: float | None = None, help: str = "") -> float:
    # The sibling of `_f` for a bounded angle: `_f`'s `gt` would refuse 0, which is the sharp head
    # (06.1 D-01), and `_free` has no bound. `ge` and `lt` put `minimum` and `exclusiveMaximum` in
    # the schema; the form turns `minimum` into an inclusive HTML min (0 is valid) and ignores
    # `exclusiveMaximum`, the 422 speaks for it. Verified on pydantic 2.13.5 (06.1-RESEARCH
    # boundary detail 3). `allow_inf_nan=False` refuses inf and nan as in `_f`.
    extra: JsonDict = {"group": group, "unit": unit}
    if step is not None:
        extra["step"] = step
    angle: float = Field(default, ge=ge, lt=lt, allow_inf_nan=False, title=title,
                         description=help, json_schema_extra=extra)
    return angle    # typed here: `Field` returns Any, which --strict refuses to return


def _b(default: bool, *, title: str, group: str, help: str = "") -> bool:
    # The sibling of `_f` for a yes/no field: no bound, no step, no unit. The schema still
    # carries `unit` (empty) because the parity test and the form read it on every property.
    return Field(default, title=title, description=help,
                 json_schema_extra={"group": group, "unit": ""})


class FastenerParams(BaseModel):
    """What every fastener kind shares: a nominal diameter, a pitch and a hand.

    `extra="forbid"` is what makes a field the kind does not define a 422 naming it
    (FRNT-01) instead of a silently ignored one (L02).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ClassVar[str]

    # The defaults are the ISO 4017 M6 x 20 row, asserted by
    # tests/test_params.py::test_the_frozen_defaults_are_the_iso_4017_m6_x_20_row (D-07). They
    # are frozen all the same: every shareable link omits fields at default, so moving one
    # silently rebuilds a different part from an old link (L02).
    d: float = _diameter(MAX_FIELD_MM)
    pitch: float = _f(1.0, gt=0, title="Pitch", group="Size", unit="mm", step=0.05,
                      help="Thread pitch: the axial distance from one crest to the next.")
    # D-09: on the base, not on BoltParams, because the thread is every part's (THRD-01) and a
    # nut's hand derives from the same d, pitch and hand (TYPE-04). Frozen like d and pitch:
    # a link that omits it means right-hand on every front end, forever (L02).
    left_hand: bool = _b(False, title="Left-hand thread", group="Thread",
                         help="Cut the thread left-handed. Off: right-hand.")

    @model_validator(mode="after")
    def _root_radius(self) -> Self:
        # Imported here: `screw/calc/__init__.py` imports this module, so a top-level import of
        # anything under `screw.calc` is circular (the 01 pattern). The message names both
        # fields because the CLI prints no loc for a model-level error (D-04).
        from screw.calc.thread import root_radius_refusal

        if (msg := root_radius_refusal(self.d, self.pitch)) is not None:
            raise PydanticCustomError("pitch_too_coarse", msg, {"fields": ["d", "pitch"]})
        return self

    def slug(self) -> str:
        """Short, filename-safe identifier: the kind plus every field as name and %g value.

        Built from validated floats only, so it can contain nothing but letters, digits
        and `_.+-` (T-01-06).
        """
        fields = "_".join(f"{name}{getattr(self, name):g}" for name in type(self).model_fields)
        return f"{self.kind}_{fields}"


class BoltParams(FastenerParams):
    """The bolt: a hex head bolt or screw of diameter d, pitch, nominal length, across flats s
    and head height k."""

    kind: ClassVar[str] = "bolt"

    # Redeclared for its own wall (MAX_BOLT_D_MM), in the base's place in the field order.
    d: float = _diameter(MAX_BOLT_D_MM)
    length: float = _f(20.0, gt=0, le=MAX_BOLT_LENGTH_MM, title="Length", group="Size", unit="mm",
                       step=0.5, help="Nominal length l: from the tip of the thread to the "
                                      "underside of the head.")
    # D-07, L02: the ISO 4017:2022 M6 row (grade A) as the owner read it on 2026-10-11 from the
    # purchased copy and confirmed in 04-OWNER-READS.md. Frozen: every shareable link that omits
    # s or k means these values forever. Plan 04-08's row test asserts them against the cited row.
    s: float = _f(10.0, gt=0, le=MAX_FIELD_MM, title="Across flats", group="Head", unit="mm",
                  step=0.1, help="Width across flats of the hexagon head (ISO symbol s).")
    k: float = _f(4.0, gt=0, le=MAX_BOLT_K_MM, title="Head height", group="Head", unit="mm",
                  step=0.1, help="Height of the hexagon head along the axis (ISO symbol k).")
    # D-07, L02: the ISO 4017 M6 x 20 row fills this with the full length, and the default 20.0 is
    # frozen: every shareable link that omits it means 20 forever. Measured from the tip (D-08)
    # and never rewritten: `built_thread_length` derives the thread the builder makes, so a
    # length below this default builds a full-thread screw and the info document says so.
    thread_length: float = _f(20.0, gt=0, le=MAX_BOLT_THREAD_LENGTH_MM, title="Thread length",
                              group="Thread", unit="mm", step=0.5,
                              help="Length of the thread from the tip (ISO 4014: b; ISO 4017: "
                                   "the whole length); the rest of the length is a plain shank "
                                   "of diameter d.")
    # Owner ruling 2026-10-24 (L19): 30 is the top of the 15 to 30 degree band read for the nut
    # (R4 a, a stated model). Frozen: every link that omits it means 30 forever (L02), and it is
    # declared last so `slug()` keeps the old name as its prefix (D-16). No model validator: a
    # depth over k / 2 is capped and warned (D-04, D-06), and the 422 for an explicit value is the
    # request boundary's (D-05).
    head_chamfer: float = _angle(
        30.0, ge=0, lt=90, title="Head chamfer", group="Head", unit="°", step=0.5,
        help="The chamfer on the top corners of the hex head, in degrees from the top face: a "
             "cone from the inscribed circle s / 2, cut no deeper than k / 2. 0 leaves the "
             "corners sharp. The standards draw this chamfer as a 15 to 30 degree band; 30 is "
             "the model's choice.")

    @model_validator(mode="after")
    def _turn_cap(self) -> Self:
        # Needs the built thread, which only the bolt has (D-01, D-22). No `thread_length` is
        # refused against `length` here: the owner's D-25 ruling accepts a direct
        # BoltParams(length=10, thread_length=30), built to the length and warned by `derive`,
        # and puts the 422 for two explicit values at the request boundary (plan 04-05).
        from screw.calc.thread import built_thread_length, turn_cap_refusal

        t = built_thread_length(self.thread_length, self.length)
        if (msg := turn_cap_refusal(t, self.pitch)) is not None:
            raise PydanticCustomError(
                "turn_cap", msg, {"fields": ["thread_length", "length", "pitch"]})
        return self

    @model_validator(mode="after")
    def _head_too_small(self) -> Self:
        # Product policy, not a kernel necessity (D-26): the research probe fused s < d and
        # s == d into one valid solid inside the gate. A head no wider than the shank is not a
        # hex head, so it is a 422 naming both fields rather than a silently different part (L02).
        from screw.calc.thread import head_too_small_refusal

        if (msg := head_too_small_refusal(self.s, self.d)) is not None:
            raise PydanticCustomError("head_too_small", msg, {"fields": ["s", "d"]})
        return self


class NutParams(FastenerParams):
    """The nut: a hex nut of nominal diameter d and pitch, across flats s, height m and the radial
    clearance of its thread against a bolt of the same d."""

    kind: ClassVar[str] = "nut"

    # D-15, L02: the ISO 4032:2023 M6 values (grade A, coarse pitch 1.0) recorded in
    # 05-OWNER-READS.md: s the `s` max column, which is the nominal width across flats, and m the
    # `m` max column. The source is secondary: Claude read them on 2026-10-14 from a print of the
    # GlobalFastener.com page that transcribes ISO 4032:2023, not from the purchased standard, and
    # the owner approved that source and typed `permanent: accepted` for these two values. Both were
    # cross-checked against GOST ISO 4032-2014 Table 1, M6, on 2026-10-20 and are pinned to that
    # row by `tests/test_params.py` (L14, 05-OWNER-READS.md). Frozen:
    # every shareable link that omits s or m means these values forever.
    s: float = _f(10.0, gt=0, le=MAX_FIELD_MM, title="Across flats", group="Nut", unit="mm",
                  step=0.1, help="Width across flats of the hexagon nut (ISO 4032 symbol s).")
    m: float = _f(5.2, gt=0, le=MAX_NUT_M_MM, title="Height", group="Nut", unit="mm", step=0.1,
                  help="Height of the nut along the axis (ISO 4032 symbol m).")
    # D-07, PAIR-02, L02, L17: 0.15 mm is the smallest Phase 6 ladder step from which every printed
    # M6 to M12 product nut threaded by hand onto its printed product bolt (run 06-print-run-1,
    # record sha256 f76753ded41726daec0a11ec4c5eabc5f4d2afb094cbe258d5e9d915aa6db725; the owner's
    # print profile is in 06-PRINT-PROTOCOL.md). It is the value `bench.print_rules.default_from`
    # reads from that pinned record, and `tests/test_print_rules.py` re-derives it. The owner
    # accepted it as permanent on 2026-10-23.
    # Frozen: every shareable link that omits clearance means 0.15 forever, so a later reading is a
    # new decision and never an edit here. No lower bound; the two refusals below stay as they were.
    clearance: float = _free(
        0.15, le=MAX_NUT_CLEARANCE_MM, title="Clearance (radial)", group="Pair", unit="mm",
        step=0.01,
        help="Radial clearance c in mm: both thread radii of the nut grow by c, so a positive "
             "value enlarges the nut's thread and 0 is the nominal profile. The diametral value "
             "(2 c) is on the info panel.")

    @model_validator(mode="after")
    def _root_radius(self) -> Self:
        # Same name as the base rule on purpose (RESEARCH F6): pydantic keeps one validator per
        # name, so this replaces the inherited c-free rule instead of running beside it. The
        # nut's void grows by the clearance, so the root radius swept is d/2 - 5H/8 + c (D-04).
        from screw.calc.thread import void_root_radius_refusal

        if (msg := void_root_radius_refusal(self.d, self.pitch, self.clearance)) is not None:
            raise PydanticCustomError(
                "pitch_too_coarse", msg, {"fields": ["d", "pitch", "clearance"]})
        return self

    @model_validator(mode="after")
    def _nut_too_thin(self) -> Self:
        # D-13: a void wider than the flats is a direct conflict between values the user typed,
        # so it is a 422 naming the three fields, not a trimmed part (L02).
        from screw.calc.thread import nut_too_thin_refusal

        if (msg := nut_too_thin_refusal(self.s, self.d, self.clearance)) is not None:
            raise PydanticCustomError("nut_too_thin", msg, {"fields": ["s", "d", "clearance"]})
        return self

    @model_validator(mode="after")
    def _turn_cap(self) -> Self:
        # P11: judged on the void the builder makes (m + 2 pitch), not on m alone.
        from screw.calc.thread import nut_turn_cap_refusal

        if (msg := nut_turn_cap_refusal(self.m, self.pitch)) is not None:
            raise PydanticCustomError("turn_cap", msg, {"fields": ["m", "pitch"]})
        return self


KINDS: dict[str, type[FastenerParams]] = {
    BoltParams.kind: BoltParams, NutParams.kind: NutParams}

# Frozen forever: a link that omits `kind` means bolt, so the default can never move to
# whatever the registry happens to list first (L02, D-09). A test asserts the literal.
DEFAULT_KIND = "bolt"
