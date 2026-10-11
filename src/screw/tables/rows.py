"""The row types: per-size records of numbers, each carrying the page it was read from.

Rows are never the printed layout of a standard. Tolerance columns (the printed `l` min and max
cells, `ls,min` and the like) are not stored: the nominal length is the number the product uses,
so there is nothing to double-enter (RESEARCH Pitfall 10).

Every dataclass is keyword-only with no defaults, so a row built without `source=` is a
`mypy --strict` error naming `source` (TABL-02): the citation cannot be forgotten, only written.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["verified", "unverified"]


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

    def cite(self) -> str:
        """`ISO 4017:2022 Table 2, column M6`."""
        return f"{self.standard}:{self.edition} {self.table}, column {self.column}"


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
class SeriesLength:
    """One standard length of a size, with the product grade it is made in."""

    size: str
    length: float
    grade: Literal["A", "B"]
    source: Source
