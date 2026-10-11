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

# INTERIM (D-01, D-14): the largest diameter or length a request may ask for, in mm. Not a
# physical limit and not measured for screw's finished parts: it was taken from the
# 01-RESEARCH.md F1 table, measured on the skeleton's plain cylinder, so one valid-looking
# request could not outgrow compose's interim `mem_limit: 4g` (D-03) before the 30 s timeout
# fires. F1 (macOS arm64, Apple M2 Max, one run per row, preview tessellation 0.08/0.5):
#   d=1e5  9,932 triangles  0.10 s   553 MiB
#   d=1e6  31,412 triangles 1.2 s  1,159 MiB
#   d=1e7  99,344 triangles 25.1 s 6,036 MiB   <- above the interim 4g
# Those numbers do not carry over to a thread, whose cost is set by turns and size and is
# unmeasured at this corner: planner probe 2026-10-10, d=1e5, pitch=1, length=1 builds in
# 0.01 s and its preview STL did not finish in 120 s. The 250-turn cap (MAX_TURNS) bounds the
# turns; this bound stays as the INTERIM ceiling on size, and Phase 7 re-sweeps (OPER-02) and
# sets the real cap (OPER-03). A value above it is a 422 naming the field, never a clamp (L02).
INTERIM_MAX_MM = 1e5


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

    # ASSUMPTION (D-05): 1.0 mm is the ISO 262 coarse pitch for M6. Phase 4's ISO 262 row
    # test must assert the default (d, pitch) equals a row; Phase 5's `defaults mate` test
    # guards the pair. These defaults are frozen: every shareable link omits fields at
    # default, so moving one silently rebuilds a different part from an old link (L02).
    d: float = _f(6.0, gt=0, le=INTERIM_MAX_MM, title="Diameter", group="Size", unit="mm",
                  step=0.1, help="Nominal (major) diameter of the shank.")
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

    length: float = _f(20.0, gt=0, le=INTERIM_MAX_MM, title="Length", group="Size", unit="mm",
                       step=0.5, help="Nominal length l: from the tip of the thread to the "
                                      "underside of the head.")
    # D-07, L02: the ISO 4017:2022 M6 row (grade A) as the owner read it on 2026-10-11 from the
    # purchased copy and confirmed in 04-OWNER-READS.md. Frozen: every shareable link that omits
    # s or k means these values forever. Plan 04-08's row test asserts them against the cited row.
    s: float = _f(10.0, gt=0, le=INTERIM_MAX_MM, title="Across flats", group="Head", unit="mm",
                  step=0.1, help="Width across flats of the hexagon head (ISO symbol s).")
    k: float = _f(4.0, gt=0, le=INTERIM_MAX_MM, title="Head height", group="Head", unit="mm",
                  step=0.1, help="Height of the hexagon head along the axis (ISO symbol k).")

    @model_validator(mode="after")
    def _turn_cap(self) -> Self:
        # Needs `length`, which only the bolt has (D-01).
        from screw.calc.thread import turn_cap_refusal

        if (msg := turn_cap_refusal(self.length, self.pitch)) is not None:
            raise PydanticCustomError("turn_cap", msg, {"fields": ["length", "pitch"]})
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


KINDS: dict[str, type[FastenerParams]] = {BoltParams.kind: BoltParams}

# Frozen forever: a link that omits `kind` means bolt, so the default can never move to
# whatever the registry happens to list first (L02, D-09). A test asserts the literal.
DEFAULT_KIND = "bolt"
