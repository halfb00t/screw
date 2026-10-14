"""The M18 control probe: the 36 readings of `05-M18-DIAGNOSIS.md` and no others (D-08).

Protocol: `.planning/phases/05-hex-nut-and-kernel-pair-proof/05-M18-DIAGNOSIS.md`, which must be
on `origin/main`, byte for byte, before this runs. Each reading is one boolean of the recorded
M18 cell in a fresh child process (`python -m bench.m18_probe --one JSON`), so a hung or
crashing boolean costs one reading. The parent never imports the kernel: `read_one` does, and
only the children call it.

    python -m bench.m18_probe          # run all 36 readings, write the JSONL, print a table
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from bench import machine_facts, quiet
from bench.thread_spike import maths
from bench.thread_spike.verdict import (
    EMPTY_MM3,
    PAIR_BAND,
    closed_control,
    parse_pair_result_row,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ".planning/phases/05-hex-nut-and-kernel-pair-proof/05-M18-DIAGNOSIS.md"
PROTOCOL = ROOT / PROTOCOL_PATH
RECORD = ROOT / "bench" / "results" / "thread-spike" / "2026-10-08-a-pair.jsonl"
OUT = ROOT / "bench" / "results" / "phase-05" / "m18-diagnosis.jsonl"

# The recorded M18 cell (`2026-10-08-a-pair`): the height is the recorded UNVERIFIED preview
# value, so the probe reads the recorded cell and not the product's. K = 3 is
# `screw.solid.helical.DEFAULT_K`, not imported because that package loads the kernel.
SIZE, D, PITCH, M, K = "M18", 18.0, 2.5, 15.8, 3

REPEATS = 5
# Radians either side of the failing pose (P2).
DELTAS = (-0.1, -0.01, -0.001, -0.0001, 0.0001, 0.001, 0.01, 0.1)
# `screw.solid.helical.SEWING_TOLERANCE`, the builder's own tolerance (P4a).
FUZZY_MM = 1e-4
CLEARANCE = 0.10
SENSITIVITY_CLEARANCE = -0.05

# 4 x 30.964 s, the slowest M18 k = 3 boolean in the recorded jsonl, rounded up to a multiple of
# 10 s. `verdict.PAIR_TIMEOUT_S` (600 s) is a whole-cell figure and is not reused (IN-02).
DEADLINE_S = 130.0
MAX_CHILDREN = 4


@dataclass(frozen=True)
class Reading:
    probe: str
    left_hand: bool
    clearance: float
    theta: float
    offset_pitches: float
    fuzzy: float | None
    swapped: bool


def _failing_theta(left_hand: bool) -> float:
    """The half-pitch control that read empty: the first matched pose on the right hand, the
    last on the left (a left-hand thread advances the other way)."""
    return maths.MATCHED_POSES[2] if left_hand else maths.MATCHED_POSES[0]


def _readings() -> tuple[Reading, ...]:
    control = maths.CONTROL_OFFSET_PITCHES
    out: list[Reading] = []
    for left in (False, True):
        out += [Reading("P1", left, CLEARANCE, _failing_theta(left), control, None, False)
                for _ in range(REPEATS)]
    for left in (False, True):
        out += [Reading("P2", left, CLEARANCE, _failing_theta(left) + delta, control, None, False)
                for delta in DELTAS]
    for left in (False, True):
        out.append(Reading("P3", left, SENSITIVITY_CLEARANCE, _failing_theta(left), control,
                           None, False))
    for left in (False, True):
        out.append(Reading("P4a", left, CLEARANCE, _failing_theta(left), control, FUZZY_MM,
                           False))
    for left in (False, True):
        out.append(Reading("P4b", left, CLEARANCE, _failing_theta(left), control, None, True))
    for left in (False, True):
        out += [Reading("H", left, CLEARANCE, theta, control, None, False)
                for theta in maths.MATCHED_POSES if theta != _failing_theta(left)]
    return tuple(out)


READINGS = _readings()


def deadline_from_record(path: Path) -> float:
    """4 x the largest `seconds` of any M18 k = 3 reading in the recorded pair campaign, rounded
    up to a multiple of 10 s. Kernel-free."""
    slowest = max(
        reading["seconds"] or 0.0
        for record in map(parse_pair_result_row, path.read_text(encoding="utf-8").splitlines()[1:])
        if record["size"] == SIZE and record["k"] == K
        for reading in record["readings"])
    return math.ceil(4 * slowest / 10) * 10.0


def protocol_on_main(local: bytes, on_main: bytes | None) -> bool:
    """False when `origin/main` has no such file or its bytes differ from the local ones."""
    return on_main is not None and on_main == local


def child_refusal(r: Reading) -> str | None:
    """Why `--one` must not start this reading, or None. The child is the module's only way to
    reach the kernel, so it re-checks what the parent checked: the reading is one of the 36,
    the protocol is on origin/main byte for byte (the parent just fetched, so no fetch here),
    and the parent has claimed the output file, which stays empty until the run ends. A manual
    `--one` is therefore refused before a run, after one and for any pose off the list. It is
    not refused during a run, and then it has no deadline: closing that needs a secret the
    child cannot check, which is more than a diagnosis of 36 readings is worth."""
    if r not in READINGS:
        return "not one of the 36 registered readings"
    if not protocol_on_main(PROTOCOL.read_bytes(), _git("show", f"origin/main:{PROTOCOL_PATH}")):
        return f"{PROTOCOL_PATH} is not on origin/main byte for byte (D-08)"
    if not OUT.exists() or OUT.stat().st_size:
        return f"{OUT} is not an output file claimed by a run in progress"
    return None


def read_one(r: Reading) -> dict[str, object]:
    """Build the recorded bodies, place, cover-check and intersect with this reading's options.

    The kernel is imported here and nowhere else in the module: the parent process never pays
    for it nor holds its memory.
    """
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.TopTools import TopTools_ListOfShape

    from bench.thread_spike import measure, pair

    rod = pair.rod_piece(D, PITCH, M, r.left_hand, K)
    blank = pair.nut(D, PITCH, M, r.clearance, r.left_hand, K)
    placed = pair.place(blank, r.theta, r.offset_pitches, PITCH, r.left_hand)
    pair.check_cover(rod, placed)
    arguments, tools = (placed, rod) if r.swapped else (rod, placed)
    t0 = time.perf_counter()
    op = BRepAlgoAPI_Common()
    first, second = TopTools_ListOfShape(), TopTools_ListOfShape()
    first.Append(arguments.wrapped)
    second.Append(tools.wrapped)
    op.SetArguments(first)
    op.SetTools(second)
    if r.fuzzy is not None:
        op.SetFuzzyValue(r.fuzzy)
    op.Build()
    filler = op.DSFiller()
    pair._KEEP.append((op, filler))
    shape = op.Shape()
    solids = [] if shape.IsNull() else cq.Shape.cast(shape).Solids()
    volume = measure.precise_volume(cq.Shape.cast(shape)) if solids else 0.0
    return {"outcome": "built", "solids": len(solids), "volume": volume,
            "diag_errors": bool(filler.HasErrors()), "diag_warnings": bool(filler.HasWarnings()),
            "seconds": time.perf_counter() - t0}


def _closed_form(r: Reading) -> float:
    return closed_control({"size": SIZE, "d": D, "pitch": PITCH, "m": M, "clearance": r.clearance,
                           "rod_left_hand": r.left_hand, "nut_left_hand": r.left_hand, "k": K})


def _child(r: Reading) -> dict[str, object]:
    """One reading in a fresh process, under the deadline: never retried."""
    base: dict[str, object] = {**asdict(r), "closed_control": _closed_form(r)}
    try:
        done = subprocess.run(
            [sys.executable, "-m", "bench.m18_probe", "--one", json.dumps(asdict(r))],
            capture_output=True, text=True, timeout=DEADLINE_S, cwd=ROOT, check=False)
    except subprocess.TimeoutExpired:
        return {**base, "outcome": "timeout", "error": f"over the {DEADLINE_S:g} s deadline"}
    try:
        result: dict[str, object] = json.loads(done.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {**base, "outcome": "failure",
                "error": f"exit {done.returncode}, no result line: {done.stderr.strip()[-300:]}"}
    return {**base, **result}


def _git(*args: str, cwd: Path = ROOT) -> bytes | None:
    """Git's stdout as raw bytes (text mode would fold CRLF into LF and the guard compares
    bytes), or None when git failed."""
    done = subprocess.run(["git", *args], capture_output=True, cwd=cwd, check=False)
    return done.stdout if done.returncode == 0 else None


def _rev(spec: str) -> str | None:
    out = _git("rev-parse", spec)
    return None if out is None else out.decode().strip()


def harness_void(rows: list[dict[str, object]]) -> str | None:
    """Prediction H: the four harness controls must each read non-empty within `PAIR_BAND` of
    their closed form, else the probe is void on this host. None when it is not void."""
    controls = [row for row in rows if row["probe"] == "H"]
    failed = []
    for row in controls:
        volume, closed = row.get("volume"), row["closed_control"]
        ok = (row.get("outcome") == "built" and isinstance(volume, int | float)
              and isinstance(closed, float) and abs(volume) > EMPTY_MM3
              and abs(volume / closed - 1.0) <= PAIR_BAND)
        if not ok:
            failed.append(f"{'left' if row['left_hand'] else 'right'} hand theta {row['theta']:g}")
    if len(controls) != 4:
        return f"{len(controls)} harness controls ran, not 4"
    if failed:
        return ("harness controls not non-empty within PAIR_BAND of the closed form: "
                + "; ".join(failed))
    return None


def _table(rows: list[dict[str, object]]) -> str:
    head = ("probe", "hand", "clearance", "theta", "fuzzy", "swapped", "outcome", "solids",
            "volume", "closed_control", "seconds")
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    for row in rows:
        hand = "left" if row["left_hand"] else "right"
        cells = [row["probe"], hand, *(row.get(k, "") for k in head[2:])]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    return "\n".join(lines)


def main() -> int:
    local = PROTOCOL.read_bytes()
    # A stale local ref would pass or fail on old text, so fetch first and fail closed.
    fetched = _git("fetch", "--quiet", "origin", "main") is not None
    on_main = _git("show", f"origin/main:{PROTOCOL_PATH}") if fetched else None
    if not protocol_on_main(local, on_main):
        print(f"refusing to run: {PROTOCOL_PATH} is not on origin/main byte for byte; the "
              "protocol PR must land first (D-08)", file=sys.stderr)
        return 2
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Claimed before any reading, so a second launch is refused instead of running all 36
        # and losing them, and an interrupted run leaves an empty file that blocks a repeat:
        # no reading is retried.
        claim = OUT.open("x", encoding="utf-8")
    except FileExistsError:
        print(f"refusing to run: {OUT} exists (an empty one is an interrupted run) and no "
              "reading is retried", file=sys.stderr)
        return 2
    with claim:
        before = quiet.read_now()
        with ThreadPoolExecutor(max_workers=MAX_CHILDREN) as pool:
            rows = list(pool.map(_child, READINGS))
        after = quiet.read_now()
        void = harness_void(rows)
        header = {
            "run_id": f"{datetime.now(UTC):%Y-%m-%d}-m18-diagnosis",
            "head": _rev("HEAD"),
            "protocol_blob": _rev(f"origin/main:{PROTOCOL_PATH}"),
            "host": machine_facts(),
            "load_before": asdict(before),
            "load_after_includes_the_runs_own_load": asdict(after),
            "void": void,
        }
        claim.write(json.dumps(header) + "\n")
        claim.writelines(json.dumps(row) + "\n" for row in rows)
    if void is not None:
        print(f"VOID: {void}; the probe says nothing on this host (prediction H)")
    print(_table(rows))
    return 0 if void is None else 1


def _one_line(raw: str) -> str:
    """The `--one` child's single result line for the reading in `raw`."""
    try:
        reading = Reading(**json.loads(raw))
        refusal = child_refusal(reading)
        if refusal is not None:
            return json.dumps({"outcome": "failure", "error": f"refusing to run: {refusal}"})
        return json.dumps(read_one(reading))
    except Exception as exc:  # one reading's failure is one recorded line, not a dead probe
        return json.dumps({"outcome": "failure", "error": f"{type(exc).__name__}: {exc}"})


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--one":
        line = _one_line(sys.argv[2])
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        # The boolean is parked in `pair._KEEP`; a normal exit frees it and segfaults (exit 139,
        # RESEARCH F5). The parent has its line.
        os._exit(0)
    sys.exit(main())
