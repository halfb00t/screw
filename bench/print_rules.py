"""The rules of Phase 6's printed test, committed before the first print (PAIR-02, INFO-04).

The clearance default and the printability threshold are readings of the owner's record, never
typed: this module is the reading, written and controlled by synthetic records before any real
record exists, and re-run by `make verify` tests afterwards (D-07, D-10). The record is read
strictly. A cell the reader cannot read exactly is a refusal naming the line, not an
interpretation (L02): a number someone will cut metal to must not rest on a guess at what a blank
or a misspelt cell meant.

The record digests are added as constants after the owner's last edit of each record, and those
constants are the only lines of this module that may change once the protocol has landed. A
change to the ladder, the sizes, the pass definition or a rule after a record row exists is a new
change that visibly post-dates the protocol, never an edit of it (02 D-19).

Kernel-free and product-free: it imports no `screw` module and no CAD kernel (the import-linter
contract of the spike's kernel-free modules lists it).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# D-03. The 0.05 floor is the smallest clearance the fine mesh was sized against (L15 D-21).
LADDER: tuple[float, ...] = (0.05, 0.1, 0.15, 0.2, 0.25)
# D-04. The main matrix: coarse pitch, one size per row of the default's reading.
SIZES = ("M6", "M8", "M10", "M12")
# D-10. The second run, at the default, that sets the printability threshold.
SMALL_SIZES = ("M3", "M4", "M5")
# D-04, D-10: every cell is three samples; a cell passes only when all three do.
SAMPLES = 3
# ISO 262 coarse (d, pitch) of the seven sizes. Literal because this module imports no product
# code; tests/test_print_rules.py pins it to `screw.tables.iso262.SIZES`.
COARSE: dict[str, tuple[float, float]] = {
    "M3": (3.0, 0.5),
    "M4": (4.0, 0.7),
    "M5": (5.0, 0.8),
    "M6": (6.0, 1.0),
    "M8": (8.0, 1.25),
    "M10": (10.0, 1.5),
    "M12": (12.0, 1.75),
}

MATRIX_COLUMNS = ("size", "clearance", "sample", "plate", "order", "result", "turns", "note")
SMALL_COLUMNS = ("size", "sample", "plate", "result", "turns", "note")

RESULTS_DIR = ROOT / "bench" / "results" / "phase-06"
RUN_1 = RESULTS_DIR / "print-run-1.tsv"
RUN_2 = RESULTS_DIR / "print-run-2.tsv"
RUN_1_ID = "06-print-run-1"
RUN_2_ID = "06-print-run-2"

_TURNS = re.compile(r"[0-9]+(\.[0-9]+)?")
_SAMPLE_CELLS = {str(n): n for n in range(1, SAMPLES + 1)}
# Exact spellings only: "0.10" is a different string from the template's "0.1", and a reader that
# accepted both would be interpreting the cell.
_CLEARANCE_CELLS = {repr(c): c for c in LADDER}
# R3: the five nuts of one bolt are fitted loosest first, so the order a clearance must carry is
# fixed: 0.25 is 1 and 0.05 is 5. The record states the order a nut took; a nut fitted out of turn
# is refused, not corrected, because the record is the owner's observation.
FIT_ORDER: dict[float, int] = {c: len(LADDER) - i for i, c in enumerate(LADDER)}

type _Cells = list[tuple[int, dict[str, str]]]


def matrix_keys() -> list[tuple[str, float, int]]:
    """Every pre-registered (size, clearance, sample) of run 1, in the record's row order."""
    return [(s, c, n) for s in SIZES for n in range(1, SAMPLES + 1) for c in LADDER]


def small_keys() -> list[tuple[str, int]]:
    """Every pre-registered (size, sample) of run 2, in row order."""
    return [(s, n) for s in SMALL_SIZES for n in range(1, SAMPLES + 1)]


def load(path: Path, sha256: str) -> str:
    """The text of the record at `path`, refused unless its bytes are the pinned ones.

    A record edited after its digest was pinned would make every derived number a reading of
    something nobody pre-registered, so the digest is checked before a byte is parsed.
    """
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != sha256:
        raise ValueError(f"{path} is not the pinned record: sha256 {digest}, expected {sha256}")
    return data.decode("utf-8")


def _cells(text: str, columns: tuple[str, ...]) -> _Cells:
    """The rows of `text` as (line number, cells by column), each cell checked to be readable.

    Checks everything the two records share: the exact header, the cell count, no blank or
    padded cell, and the closed vocabulary of `result`, `turns` and `note`.
    """
    lines = text.split("\n")
    if lines[0] != "\t".join(columns):
        raise ValueError(f"line 1: the header is not {'/'.join(columns)} separated by tabs")
    rows: _Cells = []
    for number, line in enumerate(lines[1:], start=2):
        if line == "":
            continue
        values = line.split("\t")
        if len(values) != len(columns):
            raise ValueError(f"line {number}: {len(values)} cells, expected {len(columns)}")
        row = dict(zip(columns, values, strict=True))
        for column, value in row.items():
            if value == "" or value != value.strip():
                raise ValueError(f"line {number}: the {column} cell is blank or padded")
        if row["result"] not in ("pass", "bind"):
            raise ValueError(f"line {number}: result must be exactly pass or bind")
        is_pass = row["result"] == "pass"
        if is_pass and row["turns"] != "-":
            raise ValueError(f"line {number}: a pass has no turns; write -")
        if not is_pass and not _TURNS.fullmatch(row["turns"]):
            raise ValueError(f"line {number}: a bind needs its turns as a non-negative decimal")
        if row["note"] == "loose" and not is_pass:
            raise ValueError(f"line {number}: loose describes a pass, not a bind")
        rows.append((number, row))
    return rows


def _sample(number: int, row: dict[str, str]) -> int:
    if row["sample"] not in _SAMPLE_CELLS:
        raise ValueError(f"line {number}: sample must be 1 to {SAMPLES}")
    return _SAMPLE_CELLS[row["sample"]]


def _size(number: int, row: dict[str, str], sizes: tuple[str, ...]) -> str:
    if row["size"] not in sizes:
        raise ValueError(f"line {number}: size {row['size']} is not pre-registered")
    return row["size"]


def _collect[K](
    keyed: list[tuple[int, K, bool]], expected: list[K], last_line: int
) -> dict[K, bool]:
    """The results by key, refusing a repeated key, a key nobody pre-registered or a missing one."""
    seen: dict[K, bool] = {}
    for number, key, is_pass in keyed:
        if key not in expected:
            raise ValueError(f"line {number}: {key} is not pre-registered")
        if key in seen:
            raise ValueError(f"line {number}: {key} appears more than once")
        seen[key] = is_pass
    missing = [key for key in expected if key not in seen]
    if missing:
        raise ValueError(f"line {last_line}: {len(missing)} pre-registered samples missing, "
                         f"first {missing[0]}")
    return seen


def _last_line(rows: _Cells) -> int:
    return rows[-1][0] if rows else 1


def read_matrix(text: str) -> dict[tuple[str, float, int], bool]:
    """Run 1's record as a pass (True) or bind (False) per (size, clearance, sample)."""
    rows = _cells(text, MATRIX_COLUMNS)
    keyed: list[tuple[int, tuple[str, float, int], bool]] = []
    orders: list[tuple[int, float, int]] = []
    for number, row in rows:
        size = _size(number, row, SIZES)
        if row["clearance"] not in _CLEARANCE_CELLS:
            raise ValueError(f"line {number}: clearance {row['clearance']} is not on the ladder")
        clearance = _CLEARANCE_CELLS[row["clearance"]]
        sample = _sample(number, row)
        if not (row["order"].isascii() and row["order"].isdigit()):
            raise ValueError(f"line {number}: order must be an integer")
        orders.append((number, clearance, int(row["order"])))
        keyed.append((number, (size, clearance, sample), row["result"] == "pass"))
    cells = _collect(keyed, matrix_keys(), _last_line(rows))
    for number, clearance, order in orders:
        if order != FIT_ORDER[clearance]:
            raise ValueError(f"line {number}: order {order} for clearance {clearance}, but R3 "
                             f"fits loosest first, so this nut is {FIT_ORDER[clearance]}")
    return cells


def _read_sized(
    text: str, columns: tuple[str, ...], sizes: tuple[str, ...], expected: list[tuple[str, int]]
) -> dict[tuple[str, int], bool]:
    rows = _cells(text, columns)
    keyed = [(number, (_size(number, row, sizes), _sample(number, row)), row["result"] == "pass")
             for number, row in rows]
    return _collect(keyed, expected, _last_line(rows))


def read_small(text: str) -> dict[tuple[str, int], bool]:
    """Run 2's record as a pass (True) or bind (False) per (size, sample)."""
    return _read_sized(text, SMALL_COLUMNS, SMALL_SIZES, small_keys())


def _require_keys[K](cells: Mapping[K, bool], expected: list[K]) -> None:
    """A rule given fewer or other keys than were pre-registered derives nothing."""
    if set(cells) != set(expected):
        raise ValueError(f"the record holds {len(cells)} samples, the protocol pre-registers "
                         f"{len(expected)} and the keys must be those")


def default_from(cells: Mapping[tuple[str, float, int], bool]) -> float | None:
    """D-07 and D-08: the clearance the product ships, or None when no default ships.

    A cell (size, clearance) passes when its 3 samples all pass. The default is the smallest
    ladder step from which every cell of every size passes. None when no step qualifies, and
    also when some size passes at a step below one that does not: the record is not monotone,
    so no one-way default can be read from it.
    """
    _require_keys(cells, matrix_keys())
    passing = {(s, c): all(cells[(s, c, n)] for n in range(1, SAMPLES + 1))
               for s in SIZES for c in LADDER}
    for s in SIZES:
        steps = [passing[(s, c)] for c in LADDER]
        if any(steps[i] and not steps[j]
               for i in range(len(steps)) for j in range(i + 1, len(steps))):
            return None
    for c in LADDER:
        if all(passing[(s, step)] for s in SIZES for step in LADDER if step >= c):
            return c
    return None


def threshold_from(cells: Mapping[tuple[str, int], bool]) -> str:
    """D-10: the smallest of M3, M4, M5 that passes 3/3 together with every larger of the three.

    M6 when there is none: the main matrix's M6 passed 3/3 at the default by D-07.
    """
    _require_keys(cells, small_keys())
    passing = {s: all(cells[(s, n)] for n in range(1, SAMPLES + 1)) for s in SMALL_SIZES}
    for i, size in enumerate(SMALL_SIZES):
        if all(passing[s] for s in SMALL_SIZES[i:]):
            return size
    return "M6"
