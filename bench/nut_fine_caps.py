"""The R16 run of Phase 5: how tall a nut may be before its fine STL breaks the export budget.

THE RULE (stated here, in the commit that adds this module, before any row is run; R16, T-05-47):

    For every key (d, pitch, left_hand) of `KEYS` -- the 15 ISO 262 coarse sizes of
    `screw.tables.iso262.SIZES`, right hand then left hand, 30 keys -- take the nut
    `NutParams(d, pitch, s=S_MM, m, clearance=CLEARANCE_MM, left_hand)` for m = 1, 2, 3, ... mm in
    ascending order, and, when 248 pitches (`ladder_end`: the turn cap's largest m, as an exact
    decimal) is not a whole number of mm, for that m too. Each row is built and meshed by the
    shipped `screw.solid.export(p, "stl", "fine")`; its bytes are the STL's length plus the length
    of its gzip level-1 copy (`bench.thread_spike.measure.gzip1`). A row FITS when that sum is at
    most `BUDGET_BYTES`, the object `bench.thread_spike.verdict` judged the rods against (64 MiB).
    The ladder of a key stops at its first row over budget, at its first failed row, or after its
    last rung. The key's CAP is the largest measured m that fits, below the smallest m over
    budget; a key that fits through `ladder_end` has the cap `math.inf` (the turn cap binds first).

    Checks, at each finite cap: m = cap, s = S_MM, clearance in CHECK_CLEARANCES = (-0.05, 0.0,
    0.1, CLEARANCE_MM / 2); and m = cap, clearance = CLEARANCE_MM, s = d + 2 CLEARANCE_MM + 1 (the
    slimmest s the model admits there).

    STOP CONDITIONS. Any of these means NO CAP SHIPS and the executor commits the record and
    stops (L02): a check row over budget or failed; a ladder row that failed below the key's first
    over-budget m; a key with no fitting m (m = 1 already over, or no row at all); a ladder that
    ended before `ladder_end` without crossing the budget; a finite cap below the key's GOST ISO
    4032-2014 m_max (`screw.tables.iso4032.NUTS`; M7 has no row); a missing check row.

THE CONSTANTS. `CLEARANCE_MM` (C) is 5.0 mm, the owner's answer to R16 (`.planning/phases/
05-hex-nut-and-kernel-pair-proof/05-OWNER-READS.md`, "Rulings": `option-a`, the largest clearance
any GOST ISO 4032-2014 row's own s admits, (30 - 20) / 2 at M20 since s > d + 2 c). The product
refuses a fine STL above C on a measured key; this run measures nothing above C. `S_MM` is 1e5 mm,
the largest s the parameter model admits (`INTERIM_MAX_MM`): the planner's probe (05-19 Task 1)
found that s adds a near-constant number of bytes that does not grow with m, so a cap measured at
the largest s holds for every s. The agent chose neither number. The ladder, C, s, the checks and
the budget are fixed here: none may change once a row has been run.

WHAT A SINGLE RUN DOES NOT SHOW. It is one run on one host (macOS arm64, not the linux/amd64 the
service ships on; Phase 7 re-measures, OPER-02). The bytes are geometry and do not depend on load;
the seconds are recorded and the rule never reads them. The checks are samples: they do not prove
that the bytes are monotonic in clearance or in s, only that the five sampled points at each cap
fit.

AMENDMENT. An instrument defect is amended here, in this docstring and in the RESULTS.md entry,
with the rule, the ladder, C, s and the checks untouched, and a re-run gets a new `RUN_ID`. A run
is never repeated toward a pass.

Kernel side (it imports `screw.solid`), run by hand: `python -m bench.nut_fine_caps`. The rule
itself (`ladder_end`, `ladder_ms`, `total`, `caps`) is arithmetic only and reads no kernel object,
so a test can feed it hand-built rows.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import TextIO

import cadquery as cq

from bench import machine_facts
from bench.quiet import Reading, read_now
from bench.thread_spike.measure import gzip1
from bench.thread_spike.verdict import BUDGET_BYTES as BUDGET_BYTES
from screw import solid
from screw.calc.thread import MAX_TURNS
from screw.params import NutParams
from screw.solid import TESSELLATION
from screw.tables.iso262 import SIZES
from screw.tables.iso4032 import NUTS

RUN_ID = "2026-10-20-nut-fine-caps"
RECORDS = Path("bench/results/phase-05/nut-fine-caps.jsonl")

CLEARANCE_MM = 5.0    # C, R16 option-a
S_MM = 1e5            # equal to params INTERIM_MAX_MM
CHECK_CLEARANCES = (-0.05, 0.0, 0.1, CLEARANCE_MM / 2)

Key = tuple[float, float, bool]
KEYS: tuple[Key, ...] = tuple(
    (z.d, z.pitch, hand) for hand in (False, True) for z in SIZES)


@dataclass(frozen=True)
class Row:
    role: str            # "ladder" or "check"
    d: float
    pitch: float
    left_hand: bool
    m: float
    clearance: float
    s: float
    outcome: str         # "built" or "failed"
    error: str | None
    raw_bytes: int | None
    gzip1_bytes: int | None
    seconds: float

    @property
    def key(self) -> Key:
        return (self.d, self.pitch, self.left_hand)


@dataclass(frozen=True)
class Verdict:
    caps: dict[Key, float]    # a key with no cap is absent
    stops: list[str]


def total(r: Row) -> int | None:
    """The row's bytes against the budget: the STL plus its gzip level-1 copy, None if not built."""
    if r.outcome != "built" or r.raw_bytes is None or r.gzip1_bytes is None:
        return None
    return r.raw_bytes + r.gzip1_bytes


def ladder_end(pitch: float) -> float:
    """The turn cap's largest m for this pitch: (MAX_TURNS - 2) pitches, as exact decimals."""
    return float(Fraction(MAX_TURNS - 2) * Fraction(repr(pitch)))


def ladder_ms(pitch: float) -> list[float]:
    """m = 1, 2, 3, ... to the turn cap's last whole mm, then the cap's own m if it is not whole."""
    end = Fraction(MAX_TURNS - 2) * Fraction(repr(pitch))
    out = [float(m) for m in range(1, int(end) + 1)]
    if end.denominator != 1:
        out.append(float(end))
    return out


def check_points(d: float) -> list[tuple[float, float]]:
    """(clearance, s) of the five checks at a finite cap."""
    return [(c, S_MM) for c in CHECK_CLEARANCES] + [(CLEARANCE_MM, d + 2 * CLEARANCE_MM + 1)]


def _iso_m_max(d: float, pitch: float) -> float | None:
    for z in SIZES:
        if z.d == d and z.pitch == pitch:
            for nut in NUTS:
                if nut.size == z.label:
                    return nut.m_max
    return None


def _label(key: Key) -> str:
    return f"d {key[0]:g} pitch {key[1]:g} {'left' if key[2] else 'right'}"


def caps(rows: Sequence[Row], keys: Sequence[Key] = KEYS) -> Verdict:
    """THE RULE: each key's cap and every stop condition met. A key with a stop gets no cap."""
    found: dict[Key, float] = {}
    stops: list[str] = []
    for key in keys:
        mine = [r for r in rows if r.key == key]
        ladder = sorted((r for r in mine if r.role == "ladder"), key=lambda r: r.m)
        first_over = min((r.m for r in ladder
                          if (t := total(r)) is not None and t > BUDGET_BYTES), default=math.inf)
        fits = [r.m for r in ladder
                if (t := total(r)) is not None and t <= BUDGET_BYTES and r.m < first_over]
        bad = False
        for r in ladder:
            if r.outcome != "built" and r.m < first_over:
                stops.append(f"{_label(key)}: ladder row m {r.m:g} failed: {r.error}")
                bad = True
        if first_over == 1.0:
            stops.append(f"{_label(key)}: m = 1 is already over budget")
            bad = True
        elif not fits and not bad:
            stops.append(f"{_label(key)}: no fitting m")
            bad = True
        end = ladder_end(key[1])
        if not bad and first_over == math.inf and end not in fits:
            stops.append(f"{_label(key)}: the ladder ended before the turn cap (m {end:g}) "
                         "without crossing the budget")
            bad = True
        if bad:
            continue
        cap = math.inf if first_over == math.inf else max(fits)
        found[key] = cap
        if cap == math.inf:
            continue
        m_max = _iso_m_max(key[0], key[1])
        if m_max is not None and cap < m_max:
            stops.append(f"{_label(key)}: cap {cap:g} is below the ISO 4032 m_max {m_max:g}")
        checks = [r for r in mine if r.role == "check"]
        for clearance, s in check_points(key[0]):
            hit = [r for r in checks if r.m == cap and r.clearance == clearance and r.s == s]
            if not hit:
                stops.append(f"{_label(key)}: check row (clearance {clearance:g}, s {s:g}) "
                             "is missing")
                continue
            t = total(hit[0])
            if t is None:
                stops.append(f"{_label(key)}: check row (clearance {clearance:g}, s {s:g}) "
                             f"failed: {hit[0].error}")
            elif t > BUDGET_BYTES:
                stops.append(f"{_label(key)}: check row (clearance {clearance:g}, s {s:g}) "
                             f"is over budget: {t} bytes")
    return Verdict(found, stops)


def measure(role: str, key: Key, m: float, clearance: float, s: float) -> Row:
    """One row, the shipped way: the validated params, the shipped fine export, gzip level 1."""
    d, pitch, left_hand = key
    t0 = time.perf_counter()
    try:
        p = NutParams(d=d, pitch=pitch, s=s, m=m, clearance=clearance, left_hand=left_hand)
        data = solid.export(p, "stl", "fine")
        gz, _ = gzip1(data)
    except Exception as exc:
        return Row(role, d, pitch, left_hand, m, clearance, s, "failed",
                   f"{type(exc).__name__}: {exc}", None, None, time.perf_counter() - t0)
    finally:
        solid.clear_cache()
    return Row(role, d, pitch, left_hand, m, clearance, s, "built", None, len(data), gz,
               time.perf_counter() - t0)


def _load(reading: Reading) -> str:
    return f"load1 {reading.load1:.2f} at {reading.utc}"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def _emit(fh: TextIO, record: dict[str, object]) -> None:
    fh.write(json.dumps(record) + "\n")
    fh.flush()


def _row_record(r: Row) -> dict[str, object]:
    return {"kind": "row", "role": r.role, "d": r.d, "pitch": r.pitch, "left_hand": r.left_hand,
            "m": r.m, "clearance": r.clearance, "s": r.s, "outcome": r.outcome, "error": r.error,
            "raw_bytes": r.raw_bytes, "gzip1_bytes": r.gzip1_bytes, "seconds": r.seconds}


def _progress(r: Row) -> str:
    t = total(r)
    ratio = f"{t / BUDGET_BYTES:.3f}" if t is not None else r.error
    return (f"| {r.role} | {_label(r.key)} | {r.m:g} | {r.clearance:g} | {r.s:g} | {r.outcome} "
            f"| {t if t is not None else '-'} | {ratio} | {r.seconds:.1f} |")


def _tables(rows: list[Row], verdict: Verdict) -> list[str]:
    out = ["", "| Key | Cap m (mm) | Sum at cap (bytes) | Sum / 64 MiB | First over m | "
           "Sum there (bytes) | ISO 4032 m_max |", "|---|---|---|---|---|---|---|"]
    for key in KEYS:
        ladder = [r for r in rows if r.key == key and r.role == "ladder"]
        over = [r for r in ladder if (t := total(r)) is not None and t > BUDGET_BYTES]
        first = min(over, key=lambda r: r.m) if over else None
        cap = verdict.caps.get(key)
        at = next((r for r in ladder if r.m == cap), None)
        t_at = total(at) if at is not None else None
        m_max = _iso_m_max(key[0], key[1])
        shown = "none" if cap is None else ("inf" if cap == math.inf else f"{cap:g}")
        out.append(
            f"| {_label(key)} | {shown} "
            f"| {t_at if t_at is not None else '-'} "
            f"| {f'{t_at / BUDGET_BYTES:.3f}' if t_at is not None else '-'} "
            f"| {f'{first.m:g}' if first else '-'} "
            f"| {total(first) if first else '-'} | {m_max if m_max is not None else 'no row'} |")
    out += ["", "| Key | Cap m | Clearance | s | Sum (bytes) | Sum / 64 MiB |",
            "|---|---|---|---|---|---|"]
    for r in rows:
        if r.role == "check":
            t = total(r)
            out.append(f"| {_label(r.key)} | {r.m:g} | {r.clearance:g} | {r.s:g} "
                       f"| {t if t is not None else r.error} "
                       f"| {f'{t / BUDGET_BYTES:.3f}' if t is not None else '-'} |")
    return out


def main() -> int:
    if _git("status", "--porcelain", "--", "src", "bench", "tests"):
        print("refusing to start: src, bench or tests has an uncommitted change", file=sys.stderr)
        return 2
    if RECORDS.exists():
        print(f"refusing to start: {RECORDS} already exists", file=sys.stderr)
        return 2
    RECORDS.parent.mkdir(parents=True, exist_ok=True)
    head = _git("rev-parse", "HEAD")
    before = read_now()
    t_start = time.monotonic()
    print(f"run: {RUN_ID}")
    print(f"host: {machine_facts()}")
    print(f"HEAD: {head}")
    print(f"before: {_load(before)}")
    print(f"C: {CLEARANCE_MM:g} mm, s: {S_MM:g} mm, budget: {BUDGET_BYTES} bytes, "
          f"preset: {TESSELLATION['fine']}")
    print("| role | key | m | clearance | s | outcome | sum (bytes) | sum / 64 MiB | seconds |")
    print("|---|---|---|---|---|---|---|---|---|")
    rows: list[Row] = []
    with RECORDS.open("w", encoding="utf-8") as fh:
        _emit(fh, {"kind": "header", "run_id": RUN_ID, "head": head, "host": machine_facts(),
                   "python": sys.version.split()[0], "cadquery": cq.__version__,
                   "cadquery_ocp": version("cadquery-ocp"), "budget_bytes": BUDGET_BYTES,
                   "preset": list(TESSELLATION["fine"]), "clearance_mm": CLEARANCE_MM,
                   "s_mm": S_MM, "check_clearances": list(CHECK_CLEARANCES),
                   "load1_before": before.load1, "load_before_utc": before.utc})

        def take(row: Row) -> Row:
            rows.append(row)
            _emit(fh, _row_record(row))
            print(_progress(row), flush=True)
            return row

        for key in KEYS:
            for m in ladder_ms(key[1]):
                row = take(measure("ladder", key, m, CLEARANCE_MM, S_MM))
                t = total(row)
                if t is None or t > BUDGET_BYTES:
                    break
            cap = caps(rows, [key]).caps.get(key)
            if cap is not None and cap != math.inf:
                for clearance, s in check_points(key[0]):
                    take(measure("check", key, cap, clearance, s))
        verdict = caps(rows)
        after = read_now()
        wall = time.monotonic() - t_start
        _emit(fh, {"kind": "end", "load1_after": after.load1, "load_after_utc": after.utc,
                   "wall_seconds": wall,
                   "caps": [{"d": k[0], "pitch": k[1], "left_hand": k[2],
                             "cap_mm": None if v == math.inf else v,
                             "bound_by": "turn_cap" if v == math.inf else "budget"}
                            for k, v in verdict.caps.items()],
                   "stop_conditions": verdict.stops})
    print(f"after: {_load(after)} (includes the run's own meshing load)")
    print(f"wall: {wall:.1f} s")
    print("\n".join(_tables(rows, verdict)))
    print("\nstop conditions: " + ("none" if not verdict.stops else ""))
    for stop in verdict.stops:
        print(f"- {stop}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
