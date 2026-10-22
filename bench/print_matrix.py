"""What Phase 6 prints, from which product command, and the shape of every record (D-02).

Every STL is the product's own fine `screw export`, so the printed test checks what a user
downloads, not a bench-only mesh. The matrix is data: the export lists, the blank records and the
manifest all read the ladder, the sizes and the column lists of `bench.print_rules`, so the 60,
12 and 9 samples cannot drift between them.

Run 1 is 4 bolts and 20 nuts (four sizes at five clearances); run 2 is the three small sizes at
the shipped default; the acceptance set is the M8 pair at the shipped default (D-10, D-16). No
run-2 or acceptance argument list carries a clearance, so those nuts can only be built at the
default the product ships: the export refuses until it exists, which is the order the protocol
needs. STLs are never committed (`*.stl` is ignored); a manifest of name, bytes and sha256 is
what a record can cite.

Kernel-free: the product is reached through a child `python -m screw`, never an import (the
import-linter contract of the spike's kernel-free modules lists this module).

    python -m bench.print_matrix templates
    python -m bench.print_matrix export {run-1,run-2,acceptance} -o DIR
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from bench.print_rules import (
    BOUGHT,
    BOUGHT_COLUMNS,
    LADDER,
    MATRIX_COLUMNS,
    RESULTS_DIR,
    RUN_1,
    RUN_2,
    SIZES,
    SMALL_COLUMNS,
    SMALL_SIZES,
    bought_keys,
    matrix_keys,
    small_keys,
)

# The shortest ISO 4017 row of each size in `screw presets bolt`, read 2026-10-22: least filament,
# and each still runs a nut of height m along its thread to the head.
BOLT_PRESETS: dict[str, str] = {
    "M3": "iso4017:M3x6",
    "M4": "iso4017:M4x8",
    "M5": "iso4017:M5x10",
    "M6": "iso4017:M6x12",
    "M8": "iso4017:M8x16",
    "M10": "iso4017:M10x20",
    "M12": "iso4017:M12x25",
}
NUT_PRESETS: dict[str, str] = {size: f"iso4032:{size}" for size in (*SMALL_SIZES, *SIZES)}
RUNS = ("run-1", "run-2", "acceptance")


def _part(kind: str, preset: str, clearance: float | None = None) -> list[str]:
    """One `screw export` argument list, without `-o`: the fine STL of one catalogue row."""
    given = [] if clearance is None else ["--clearance", repr(clearance)]
    return ["export", kind, "--preset", preset, *given, "--format", "stl", "--quality", "fine"]


def exports(run: str) -> list[list[str]]:
    """The `screw` argument lists that make the STLs of `run`: its bolts, then its nuts."""
    if run == "run-1":
        return [*(_part("bolt", BOLT_PRESETS[s]) for s in SIZES),
                *(_part("nut", NUT_PRESETS[s], c) for s in SIZES for c in LADDER)]
    sizes = {"run-2": SMALL_SIZES, "acceptance": ("M8",)}.get(run)
    if sizes is None:
        raise ValueError(f"unknown run {run!r}; choose one of {', '.join(RUNS)}")
    return [*(_part("bolt", BOLT_PRESETS[s]) for s in sizes),
            *(_part("nut", NUT_PRESETS[s]) for s in sizes)]


def template(record: str) -> str:
    """The blank record `record` (run-1, bought or run-2): every pre-registered sample, key cells
    written, every other cell empty for the owner to fill."""
    columns: tuple[str, ...]
    keys: list[tuple[str, ...]]
    if record == "run-1":
        columns = MATRIX_COLUMNS
        keys = [(s, repr(c), str(n)) for s, c, n in matrix_keys()]
    elif record == "bought":
        columns = BOUGHT_COLUMNS
        keys = [(s, str(n)) for s, n in bought_keys()]
    elif record == "run-2":
        columns = SMALL_COLUMNS
        keys = [(s, str(n)) for s, n in small_keys()]
    else:
        raise ValueError(f"unknown record {record!r}; choose one of run-1, bought, run-2")
    lines = ["\t".join(columns),
             *("\t".join([*key, *([""] * (len(columns) - len(key)))]) for key in keys)]
    return "\n".join(lines) + "\n"


def write_template(path: Path, text: str) -> None:
    """Write `text` to `path`, refusing to replace a file that differs: a filled record is data."""
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise ValueError(f"{path} exists and differs from the blank record; not overwriting it")
    path.write_text(text, encoding="utf-8")


def export(run: str, out: Path, results: Path = RESULTS_DIR) -> Path:
    """Export the STLs of `run` into the empty directory `out`; return the manifest it wrote.

    Everything that can refuse does so before the first export, which takes minutes. The manifest
    is created exclusively, so a second run cannot replace the digests a record cites.
    """
    lists = exports(run)
    manifest = results / f"manifest-{run}.tsv"
    if manifest.exists():
        raise ValueError(f"{manifest} exists; a manifest is written once")
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"{out} is not empty; export into a new directory")
    out.mkdir(parents=True, exist_ok=True)
    for args in lists:
        subprocess.run([sys.executable, "-m", "screw", *args, "-o", str(out)], check=True)
    files = sorted(out.glob("*.stl"))
    if len(files) != len(lists):
        raise ValueError(f"{out} holds {len(files)} STL files after {len(lists)} exports; "
                         "two parts share a file name")
    lines = ["name\tbytes\tsha256"]
    for f in files:
        data = f.read_bytes()
        lines.append(f"{f.name}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}")
    with manifest.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m bench.print_matrix", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("templates", help="write the three blank records")
    e = sub.add_parser("export", help="export the STLs of one run and write its manifest")
    e.add_argument("run", choices=RUNS)
    e.add_argument("-o", "--output", type=Path, required=True,
                   help="a new or empty directory for the STLs")
    ns = ap.parse_args(argv)
    if ns.command == "templates":
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        for record, path in (("run-1", RUN_1), ("bought", BOUGHT), ("run-2", RUN_2)):
            write_template(path, template(record))
    else:
        print(export(ns.run, ns.output))


if __name__ == "__main__":
    main()
