"""Fastener parameters: one validated, hashable model per kind, shared by the API, web UI
and CLI.

All lengths are millimetres. Field metadata (group, unit, step) is exported through the
JSON schema and drives the web form and the CLI flags, so a field added here shows up in
both automatically. Each kind is a class registered in `KINDS`; adding a kind is one class
and one registry entry, never an edit to the form or the flag generator.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.config import JsonDict

# INTERIM (D-01, D-14): the largest diameter or length a request may ask for, in mm. Not a
# physical limit and not measured for screw's finished parts: it is the corner of the
# 01-RESEARCH.md F1 table below which a plain cylinder stays cheap, taken so one valid-looking
# request cannot outgrow compose's interim `mem_limit: 4g` (D-03) before the 30 s timeout
# fires. F1 (macOS arm64, Apple M2 Max, one run per row, preview tessellation 0.08/0.5):
#   d=1e5  9,932 triangles  0.10 s   553 MiB
#   d=1e6  31,412 triangles 1.2 s  1,159 MiB
#   d=1e7  99,344 triangles 25.1 s 6,036 MiB   <- above the interim 4g
# The corner this bound admits, measured 2026-10-06 on the same host with `uptime` read
# first (load averages 3.73 2.89 3.37): a cylinder with d=1e5 and length=1e5, exported
# under `/usr/bin/time -l`: preview STL 0.107 s, 576,585,728 B (550 MiB) max RSS, 9,932
# triangles; fine STL 0.934 s, 1,103,183,872 B (1,052 MiB), 28,096 triangles; STEP 0.017 s,
# 472,973,312 B (451 MiB). Each run includes the interpreter and cadquery import, so the
# floor is ~450 MiB. All under 30 s and 2 GiB, the thresholds chosen before measuring.
# macOS, not linux/container (A9). A value above the bound is a 422 naming the field, never a clamp
# (L02). Phase 7 re-sweeps (OPER-02) and sets the real cap (OPER-03).
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


class FastenerParams(BaseModel):
    """What every fastener kind shares: a nominal diameter and a pitch.

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
                      help="Thread pitch. The walking skeleton builds no thread, so pitch "
                           "does not change the solid (D-04).")

    def slug(self) -> str:
        """Short, filename-safe identifier: the kind plus every field as name and %g value.

        Built from validated floats only, so it can contain nothing but letters, digits
        and `_.+-` (T-01-06).
        """
        fields = "_".join(f"{name}{getattr(self, name):g}" for name in type(self).model_fields)
        return f"{self.kind}_{fields}"


class BoltParams(FastenerParams):
    """The walking-skeleton bolt: a plain unthreaded cylinder of diameter d and length."""

    kind: ClassVar[str] = "bolt"

    length: float = _f(20.0, gt=0, le=INTERIM_MAX_MM, title="Length", group="Size", unit="mm",
                       step=0.5, help="Length of the cylinder along its axis.")


KINDS: dict[str, type[FastenerParams]] = {BoltParams.kind: BoltParams}

# Frozen forever: a link that omits `kind` means bolt, so the default can never move to
# whatever the registry happens to list first (L02, D-09). A test asserts the literal.
DEFAULT_KIND = "bolt"
