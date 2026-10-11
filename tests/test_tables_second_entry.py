"""The double-entry diff (D-14, TABL-04): the owner's typed copy against the shipped rows.

`tests/data/owner/` holds the owner's lines verbatim, typed from the purchased standards; the
shipped rows in `screw.tables` were transcribed independently from page images, before the
owner copy was opened. Every disagreement is "go read the standard": never a majority vote and
never an edit of either copy to make them agree.
"""

from __future__ import annotations

import csv
from pathlib import Path

from screw.tables.iso262 import SIZES
from screw.tables.iso4017 import HEADS, SERIES

OWNER_DIR = Path(__file__).parent / "data" / "owner"

Cells = dict[str, float | str]
Rows = dict[tuple[str, ...], Cells]

# Per file: the columns that are the row key, the columns that are numbers.
_SHAPE: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "iso262.tsv": (("size",), ("d", "pitch", "choice")),
    "iso4017_heads.tsv": (
        ("size", "grade"),
        ("pitch", "s", "s_min", "e_min", "k", "k_min", "k_max", "dw_min"),
    ),
    "iso4017_lengths.tsv": (("size", "length"), ()),
}


def _key(key_columns: tuple[str, ...], cells: dict[str, str]) -> tuple[str, ...]:
    # A length is a number on both sides, so it is keyed by its value, not its spelling.
    return tuple(
        f"{float(cells[c]):g}" if c == "length" else cells[c] for c in key_columns
    )


def read_owner(directory: Path, name: str) -> Rows:
    """The owner's TSV: header first, tab-separated, decimal point; numbers read as floats."""
    key_columns, number_columns = _SHAPE[name]
    rows: Rows = {}
    with (directory / name).open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle, delimiter="\t"):
            cells: Cells = {
                column: (float(value) if column in number_columns else value)
                for column, value in record.items()
                if column not in key_columns
            }
            rows[_key(key_columns, record)] = cells
    return rows


def shipped() -> dict[str, Rows]:
    """The shipped rows flattened to the owner's columns, standard and edition implied."""
    return {
        "iso262.tsv": {
            (size.label,): {
                "d": size.d,
                "pitch": size.pitch,
                "choice": float(size.choice),
                "table": size.source.table,
                "column": size.source.column,
            }
            for size in SIZES
        },
        "iso4017_heads.tsv": {
            (head.size, head.grade): {
                "pitch": head.pitch,
                "s": head.s,
                "s_min": head.s_min,
                "e_min": head.e_min,
                "k": head.k,
                "k_min": head.k_min,
                "k_max": head.k_max,
                "dw_min": head.dw_min,
                "table": head.source.table,
                "column": head.source.column,
            }
            for head in HEADS
        },
        "iso4017_lengths.tsv": {
            (entry.size, f"{entry.length:g}"): {
                "grade": entry.grade,
                "table": entry.source.table,
                "column": entry.source.column,
            }
            for entry in SERIES
        },
    }


def diff(name: str, owner: Rows, ours: Rows) -> list[str]:
    """Every disagreement between the two copies of one file, one line each."""
    found: list[str] = []
    for key in sorted(owner.keys() | ours.keys()):
        where = f"{name} ({', '.join(key)})"
        if key not in ours:
            found.append(f"{where}: only in the owner copy; go read the standard")
        elif key not in owner:
            found.append(f"{where}: only in the shipped rows; go read the standard")
        else:
            for column in sorted(owner[key].keys() | ours[key].keys()):
                a, b = owner[key].get(column), ours[key].get(column)
                if a != b:
                    found.append(
                        f"{where} column {column}: owner {a!r}, shipped {b!r}; "
                        "go read the standard"
                    )
    return found


def test_the_owner_copy_and_the_shipped_rows_agree_cell_by_cell() -> None:
    ours = shipped()
    disagreements = [
        line for name in _SHAPE for line in diff(name, read_owner(OWNER_DIR, name), ours[name])
    ]
    assert disagreements == []


def test_one_changed_cell_is_one_disagreement_naming_file_key_column_and_both_values() -> None:
    owner = read_owner(OWNER_DIR, "iso4017_heads.tsv")
    changed = {key: dict(cells) for key, cells in owner.items()}
    original = changed["M6", "A"]["s_min"]
    assert isinstance(original, float)
    changed["M6", "A"]["s_min"] = original + 0.01

    (line,) = diff("iso4017_heads.tsv", changed, shipped()["iso4017_heads.tsv"])

    assert line.startswith("iso4017_heads.tsv (M6, A) column s_min: ")
    assert repr(original + 0.01) in line
    assert repr(original) in line
    assert "go read the standard" in line


def test_a_row_on_one_side_only_is_a_disagreement() -> None:
    owner = read_owner(OWNER_DIR, "iso4017_lengths.tsv")
    ours = shipped()["iso4017_lengths.tsv"]
    del owner["M6", "12"]
    del ours["M6", "20"]

    assert diff("iso4017_lengths.tsv", owner, ours) == [
        "iso4017_lengths.tsv (M6, 12): only in the shipped rows; go read the standard",
        "iso4017_lengths.tsv (M6, 20): only in the owner copy; go read the standard",
    ]
