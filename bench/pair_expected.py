"""The expected verdict of every recorded pair cell, derived and never typed (D-07, kernel-free).

Phase 5 re-runs the pair proof on the product's own bodies and compares what the kernel says
with what the recorded campaign said. The table of expected verdicts is therefore the
pre-registration of that run: it is derived from `2026-10-08-a-pair` by the unmodified
`bench.thread_spike.verdict.cell_verdict`, committed before any Phase 5 pair run, and re-derived
by a `make verify` test, so a moved rule or a hand-edited verdict fails the gate instead of
quietly turning an inconclusive cell into a proven one (L11 revision direction).

Run `python -m bench.pair_expected` to write the table. It imports no kernel and no product
code (the import-linter contract of the spike's kernel-free modules lists it).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from bench.thread_spike.verdict import cell_verdict, parse_header, parse_pair_result_row

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "bench" / "results" / "thread-spike" / "2026-10-08-a-pair.jsonl"
# The digest `bench/RESULTS.md` `### 2026-10-08-a-pair` records for the JSONL.
RECORD_SHA256 = "1644650ed5b418fc2b43bfa8fd875d371f0fc4940018f67b5b3241df6c84d9f3"
TABLE = ROOT / "tests" / "data" / "pair_expected.tsv"
# L11 locks K = 3, `screw.solid.helical.DEFAULT_K`; not imported because the solid package
# loads the kernel and this module must not. A test pins the two together.
PRODUCT_K = 3
COLUMNS = ("size", "d", "pitch", "m", "clearance", "rod_left_hand", "nut_left_hand", "verdict")


def _flag(value: bool) -> str:
    return "true" if value else "false"


def derive(path: Path = RECORD) -> list[dict[str, str]]:
    """One row per K = 3 cell of the record, in record order, judged by `cell_verdict`.

    A record that is not the one L11 cites is refused before any row is read: a different file
    would make the table a derivation of something nobody pre-registered.
    """
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != RECORD_SHA256:
        raise ValueError(f"{path} is not the record L11 cites: sha256 {digest}, "
                         f"expected {RECORD_SHA256}")
    header, *cells = data.decode("utf-8").splitlines()
    parse_header(header)
    rows: list[dict[str, str]] = []
    for line in cells:
        record = parse_pair_result_row(line)
        if record["k"] != PRODUCT_K:
            continue
        rows.append({
            "size": record["size"],
            "d": repr(float(record["d"])),
            "pitch": repr(float(record["pitch"])),
            "m": repr(float(record["m"])),
            "clearance": repr(float(record["clearance"])),
            "rod_left_hand": _flag(record["rod_left_hand"]),
            "nut_left_hand": _flag(record["nut_left_hand"]),
            "verdict": cell_verdict(record)[0],
        })
    return rows


def render(rows: list[dict[str, str]]) -> str:
    """The table as tab-separated text: a header line, one line per row, a trailing newline."""
    lines = ["\t".join(COLUMNS), *("\t".join(row[c] for c in COLUMNS) for row in rows)]
    return "\n".join(lines) + "\n"


def main() -> None:
    TABLE.write_text(render(derive()), encoding="utf-8")


if __name__ == "__main__":
    main()
