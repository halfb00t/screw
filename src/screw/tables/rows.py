"""The row types: per-size records of numbers, each carrying the page it was read from.

Rows are never the printed layout of a standard. Tolerance columns (the printed `l` min and max
cells) are not stored: the nominal length is the number the product uses, so there is nothing to
double-enter (RESEARCH Pitfall 10). The one exception is the ISO 4014 shank cell, whose printed
`ls,min` and `lg,max` are stored as printed so the relation test has something to test against
(RESEARCH Pitfall 5).

Every dataclass is keyword-only with no defaults, so a row built without `source=` is a
`mypy --strict` error naming `source` (TABL-02): the citation cannot be forgotten, only written.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["verified", "unverified"]

# The ISO edition a GOST designation adopts, for the citation (L14,
# docs/requirements/standards-sources.md). Closed on purpose: a GOST text not listed here has no
# recorded ISO equivalent, so citing it as one would be a guess.
ADOPTED_ISO: dict[str, str] = {
    "GOST ISO 4032-2014": "ISO 4032:2012",
    "GOST R ISO 4014-2013": "ISO 4014:2011",
    "GOST 24705-2004": "ISO 724:1993, MOD",
    "GOST 16093-2004": "based on ISO 965-1:1998 and ISO 965-3:1998",
}


@dataclass(frozen=True, slots=True, kw_only=True)
class Source:
    """Where a row was read: identifiers only, never the standard's wording (D-16).

    `status` is `unverified` only while a row is in progress in a worktree; `make verify`
    refuses it, so it cannot reach `main` (D-15).
    """

    standard: str
    edition: str
    table: str
    column: str
    status: Status

    def document(self) -> str:
        """`ISO 4017:2022`, or `GOST ISO 4032-2014 (ISO 4032:2012)` for a GOST text."""
        if self.standard.startswith("ISO "):
            return f"{self.standard}:{self.edition}"
        if self.standard.startswith("GOST "):
            designation = f"{self.standard}-{self.edition}"
            if designation in ADOPTED_ISO:
                return f"{designation} ({ADOPTED_ISO[designation]})"
        raise ValueError(f"no citation form for the standard {self.standard!r}:{self.edition!r}")

    def cite(self) -> str:
        """`ISO 4017:2022 Table 2, column M6`."""
        return f"{self.document()} {self.table}, column {self.column}"


@dataclass(frozen=True, slots=True, kw_only=True)
class Size:
    """One ISO 262 size: the nominal diameter and its coarse pitch."""

    label: str  # "M6", with a decimal point: "M3.5"
    d: float
    pitch: float
    choice: Literal[1, 2]
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class HexHead:
    """The head values of one size in one product grade (the row key is size and grade)."""

    size: str
    grade: Literal["A", "B"]
    pitch: float  # the pitch the head table prints, a second source for ISO 262's
    s: float
    s_min: float
    e_min: float
    k: float
    k_min: float
    k_max: float
    dw_min: float
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class HexNut:
    """The values of one hex nut size: every column the standard prints, `s` nominal = max."""

    size: str
    grade: Literal["A", "B"]  # not a printed column: the scope clause's rule
    pitch: float
    s: float
    s_min: float
    e_min: float
    m_max: float
    m_min: float
    mw_min: float
    dw_min: float
    c_max: float
    c_min: float
    da_max: float
    da_min: float
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class SeriesLength:
    """One standard length of a size, with the product grade it is made in."""

    size: str
    length: float
    grade: Literal["A", "B"]
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class ThreadBand:
    """The thread length `b` (ref.) of one ISO 4014 size: for l <= 125, and for 125 < l <= 200.

    `b_long` is None where the standard prints no second row, which is every size whose longest
    length is not above 125 mm.
    """

    size: str
    b_short: float
    b_long: float | None
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class ShankCell:
    """One white cell of the ISO 4014 length block: a standard length with its printed
    `ls,min` and `lg,max`."""

    size: str
    length: float
    grade: Literal["A", "B"]
    ls_min: float
    lg_max: float
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class FilletRadius:
    """The under-head fillet radius `r` (minimum) of one ISO 4014 size, in millimetres (R1)."""

    size: str
    pitch: float
    r_min: float
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class BasicDiameters:
    """The basic diameters of one coarse size as GOST 24705-2004 Table 1 prints them, in mm.

    `d2` is the one printed column for D2 and d2, `d1` the one for D1 and d1.
    """

    size: str
    pitch: float
    d: float
    d2: float
    d1: float
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class Tolerance:
    """One printed GOST 16093-2004 deviation or tolerance, in the unit the table prints.

    `quantity` is `es`, `EI`, `Td`, `TD1`, `Td2` or `TD2`; `grade` is the tolerance position
    (`g`, `H`) for a deviation and the tolerance grade (`6`) for a tolerance. `d_over` and
    `d_upto` are the "over X up to Y" bounds of a diameter range (Tables 5 and 6), None where the
    table is keyed by pitch alone.
    """

    quantity: str
    grade: str
    pitch: float
    d_over: float | None
    d_upto: float | None
    value: int
    unit: str
    source: Source


@dataclass(frozen=True, slots=True, kw_only=True)
class BoltLimits:
    """The 6g limits of one coarse size in mm, derived (L14): printed basic value plus printed
    deviation and tolerance. `sources` are the addends' Sources, the basic row's first."""

    size: str
    pitch: float
    d_max: float
    d_min: float
    d2_max: float
    d2_min: float
    sources: tuple[Source, ...]

    def citation(self) -> str:
        return _derived(self.sources)


@dataclass(frozen=True, slots=True, kw_only=True)
class NutLimits:
    """The 6H limits of one coarse size in mm, derived (L14), as `BoltLimits`."""

    size: str
    pitch: float
    D1_min: float
    D1_max: float
    D2_min: float
    D2_max: float
    sources: tuple[Source, ...]

    def citation(self) -> str:
        return _derived(self.sources)


def _derived(sources: tuple[Source, ...]) -> str:
    """`derived: ` and the addends' distinct citations, in order, so both GOST texts are named."""
    return "derived: " + " + ".join(dict.fromkeys(source.cite() for source in sources))
