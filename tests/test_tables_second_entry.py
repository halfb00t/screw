"""The double-entry diff (D-14, TABL-04): the owner's typed copy against the shipped rows.

`tests/data/owner/` holds the owner's lines verbatim, typed from the purchased standards; the
shipped rows in `screw.tables` were transcribed independently from page images, before the
owner copy was opened. Every disagreement is "go read the standard": never a majority vote and
never an edit of either copy to make them agree.

Phase 5's rows are read from the free GOST texts L14 names, with the owner copy generated from
their text layer (05-OWNER-READS.md, 2026-10-20).
"""

from __future__ import annotations

import csv
from pathlib import Path

from screw.tables import gost16093, iso724, iso4014, iso4032
from screw.tables.iso262 import SIZES
from screw.tables.iso4017 import HEADS, SERIES

OWNER_DIR = Path(__file__).parent / "data" / "owner"

# `None` is the owner's `-` in a number column: a band the standard prints no second row for.
Cells = dict[str, float | str | None]
Rows = dict[tuple[str, ...], Cells]

# Per file: the columns that are the row key, the columns that are numbers.
_SHAPE: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "iso262.tsv": (("size",), ("d", "pitch", "choice")),
    "iso4017_heads.tsv": (
        ("size", "grade"),
        ("pitch", "s", "s_min", "e_min", "k", "k_min", "k_max", "dw_min"),
    ),
    "iso4017_lengths.tsv": (("size", "length"), ()),
    "iso4014_heads.tsv": (
        ("size", "grade"),
        ("pitch", "s", "s_min", "e_min", "k", "k_min", "k_max", "dw_min"),
    ),
    "iso4014_bands.tsv": (("size",), ("b_short", "b_long")),
    "iso4014_lengths.tsv": (("size", "length"), ("ls_min", "lg_max")),
    "iso4032.tsv": (
        ("size",),
        ("pitch", "c_max", "c_min", "da_max", "da_min", "dw_min", "e_min", "m_max", "m_min",
         "mw_min", "s", "s_min"),
    ),
    "iso724.tsv": (("size",), ("pitch", "d", "d2", "d1")),
    "gost16093.tsv": (("quantity", "grade", "pitch", "d_over", "d_upto"), ("value",)),
}


# A key column that is a number on both sides is keyed by its value, not its spelling; `-` is
# the owner's mark for a bound the table does not print.
_NUMERIC_KEYS = ("length", "pitch", "d_over", "d_upto")


def _number_key(value: float | None) -> str:
    return "-" if value is None else f"{value:g}"


def _key(key_columns: tuple[str, ...], cells: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        _number_key(None if cells[c] == "-" else float(cells[c])) if c in _NUMERIC_KEYS
        else cells[c]
        for c in key_columns
    )


def _cell(is_number: bool, value: str) -> float | str | None:
    if not is_number:
        return value
    return None if value == "-" else float(value)


def read_owner(directory: Path, name: str) -> Rows:
    """The owner's TSV: header first, tab-separated, decimal point; numbers read as floats and
    a `-` in a number column as None."""
    key_columns, number_columns = _SHAPE[name]
    rows: Rows = {}
    with (directory / name).open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle, delimiter="\t"):
            cells: Cells = {
                column: _cell(column in number_columns, value)
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
        "iso4014_heads.tsv": {
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
            for head in iso4014.HEADS
        },
        "iso4014_bands.tsv": {
            (band.size,): {
                "b_short": band.b_short,
                "b_long": band.b_long,
                "table": band.source.table,
                "column": band.source.column,
            }
            for band in iso4014.BANDS
        },
        "iso4014_lengths.tsv": {
            (cell.size, f"{cell.length:g}"): {
                "grade": cell.grade,
                "ls_min": cell.ls_min,
                "lg_max": cell.lg_max,
                "table": cell.source.table,
                "column": cell.source.column,
            }
            for cell in iso4014.CELLS
        },
        "iso4032.tsv": {
            (nut.size,): {
                "pitch": nut.pitch,
                "c_max": nut.c_max,
                "c_min": nut.c_min,
                "da_max": nut.da_max,
                "da_min": nut.da_min,
                "dw_min": nut.dw_min,
                "e_min": nut.e_min,
                "m_max": nut.m_max,
                "m_min": nut.m_min,
                "mw_min": nut.mw_min,
                "s": nut.s,
                "s_min": nut.s_min,
                "table": nut.source.table,
                "column": nut.source.column,
            }
            for nut in iso4032.NUTS
        },
        "iso724.tsv": {
            (row.size,): {
                "pitch": row.pitch,
                "d": row.d,
                "d2": row.d2,
                "d1": row.d1,
                "table": row.source.table,
                "column": row.source.column,
            }
            for row in iso724.BASIC
        },
        "gost16093.tsv": {
            (
                term.quantity, term.grade, _number_key(term.pitch),
                _number_key(term.d_over), _number_key(term.d_upto),
            ): {
                "value": term.value,
                "unit": term.unit,
                "table": term.source.table,
                "column": term.source.column,
            }
            for term in gost16093.TOLERANCES
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


def test_the_owner_copy_is_not_vacuous() -> None:
    # An empty or truncated owner file would make the diff above pass for nothing.
    assert len(read_owner(OWNER_DIR, "iso262.tsv")) == 15
    assert len(read_owner(OWNER_DIR, "iso4017_heads.tsv")) == 18
    assert len(read_owner(OWNER_DIR, "iso4017_lengths.tsv")) == 186
    assert len(read_owner(OWNER_DIR, "iso4014_heads.tsv")) == 18
    assert len(read_owner(OWNER_DIR, "iso4014_bands.tsv")) == 15
    assert len(read_owner(OWNER_DIR, "iso4014_lengths.tsv")) == 108
    assert len(read_owner(OWNER_DIR, "iso4032.tsv")) == 14
    assert len(read_owner(OWNER_DIR, "iso724.tsv")) == 15
    assert len(read_owner(OWNER_DIR, "gost16093.tsv")) == 72


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


def test_a_dash_in_the_owner_band_file_is_none_and_one_changed_band_is_one_disagreement() -> None:
    owner = read_owner(OWNER_DIR, "iso4014_bands.tsv")
    assert owner["M12",]["b_long"] is None
    assert owner["M14",]["b_long"] == 40.0
    changed = {key: dict(cells) for key, cells in owner.items()}
    changed["M12",]["b_long"] = 36.0

    (line,) = diff("iso4014_bands.tsv", changed, shipped()["iso4014_bands.tsv"])

    assert line == (
        "iso4014_bands.tsv (M12) column b_long: owner 36.0, shipped None; go read the standard"
    )


def test_one_changed_basic_cell_names_the_file_the_size_the_column_and_both_values() -> None:
    owner = read_owner(OWNER_DIR, "iso724.tsv")
    changed = {key: dict(cells) for key, cells in owner.items()}
    changed["M7",]["d2"] = 6.351

    (line,) = diff("iso724.tsv", changed, shipped()["iso724.tsv"])

    assert line == "iso724.tsv (M7) column d2: owner 6.351, shipped 6.35; go read the standard"


def test_one_changed_tolerance_cell_names_the_file_the_key_the_column_and_both_values() -> None:
    owner = read_owner(OWNER_DIR, "gost16093.tsv")
    changed = {key: dict(cells) for key, cells in owner.items()}
    changed["Td2", "6", "1", "5.6", "11.2"]["value"] = 113.0

    (line,) = diff("gost16093.tsv", changed, shipped()["gost16093.tsv"])

    assert line == (
        "gost16093.tsv (Td2, 6, 1, 5.6, 11.2) column value: owner 113.0, shipped 112; "
        "go read the standard"
    )
