"""The pair rule: what a boolean reading of a nut against a rod proves, kernel-free.

The rule `02-SPIKE.md` Rules write down (owner ruling R1 and the WR-04 amendment: the Phase 2
spike's rule, D-12 and D-14, left exactly as written), moved here from `bench/thread_spike`
unchanged so the product runs the rule the spike measured (D-05). It is kernel-free so the CLI,
the tiers and the spike share one copy: it reads plain numbers a kernel process took and never
imports the kernel itself (RESEARCH, "Where the verdict rule lives"). `bench.thread_spike.verdict`
and `maths` import every name below back.

Symbols: `d` major diameter, `P` pitch, `c` radial clearance, `m` nut height.
"""

from __future__ import annotations

import functools
import math
from typing import Literal, TypedDict

from screw.calc.thread import section_area, section_radius

# Relative tolerance of the precise volume against the closed form. The research maximum was
# 7.6e-6 over 576 sewn rows (R10) and the naive construction's defect is about 0.76, so 1e-4
# neither flaps nor hides a 1e-3 defect. Fixed before any data (D-09); never tuned toward a pass.
T_PASS = 1e-4

# Relative band of a control reading around the closed form: 100x the research's worst agreement
# of a non-empty reading (1e-5, RESEARCH R7), fixed before any data (D-14).
PAIR_BAND = 1e-3
# A pair reading is empty when it has 0 solids or abs(volume) <= this: the c = 0 garbage read
# -0.0000 in one solid (RESEARCH R4), which a plain `volume == 0` would call non-empty.
EMPTY_MM3 = 1e-6

# Midpoints over one turn: the integral below matched the kernel to 4-5 significant figures
# whenever the kernel returned a non-empty result (RESEARCH R5, R7: 1e-5 relative at M10 and
# M20), so it is the band's centre.
INTEGRATION_POINTS = 400_000

# Radial clearance of the nut's void in mm, the proof bracket (D-11): the upper end brackets
# Phase 6's printed matrix.
PAIR_CLEARANCES: tuple[float, ...] = (0.05, 0.10, 0.15, 0.20)
# The diagnostic rows (D-11): c = 0 reads inconclusive by definition (the boolean's answer at
# contact is recorded, not trusted: garbage in 3 of 3 research readings), c = -0.05 is the
# sensitivity check, where interference must appear near the closed form.
DIAGNOSTIC_CLEARANCES: tuple[float, ...] = (0.0, -0.05)
# Three screw-motion poses equally spaced over one turn and centred on the seam. The seam pose
# stays in: dropping it would be a pose picked after the probes saw false-empty readings near
# it (RESEARCH Pitfall 3). Every |theta| <= 2 pi / 3 keeps the matched slide at P / 3 and the
# control slide at 5 P / 6, inside the rod's pad of P (Pitfall 2).
MATCHED_POSES: tuple[float, ...] = (-2 * math.pi / 3, 0.0, 2 * math.pi / 3)
# The control: the nut slid half a pitch from the matched pose, so crest meets root (D-12).
CONTROL_OFFSET_PITCHES = 0.5

Outcome = Literal["built", "failure", "timeout", "worker_died"]
ReadingOutcome = Literal["built", "failure"]
PairVerdict = Literal["proven", "violated", "inconclusive"]


class PairReading(TypedDict):
    """One pose's boolean. `offset_pitches` is 0 for a matched pose and `CONTROL_OFFSET_PITCHES`
    for a control. `outcome` is "failure" when the boolean raised, and then every measurement is
    `None`; the diagnostics are columns, never verdict inputs (they missed every false-empty in
    research, Pitfall 4)."""

    theta: float
    offset_pitches: float
    outcome: ReadingOutcome
    solids: int | None
    volume: float | None
    diag_errors: bool | None
    diag_warnings: bool | None
    seconds: float | None


class PairCell(TypedDict):
    """What names a pair cell: the rod of one hand against a nut of one hand at one clearance."""

    size: str
    d: float
    pitch: float
    m: float
    clearance: float
    rod_left_hand: bool
    nut_left_hand: bool
    k: int


class PairRequest(PairCell):
    """One cell to read: `poses` are (theta, offset in pitches), read in order."""

    poses: list[tuple[float, float]]


class PairRecord(PairCell):
    """The cell echoed plus what happened. A built cell has an `nut_volume` and no error; any
    other outcome has an error and no readings unless the worker itself reported them (a
    "failure" keeps the readings taken so far, the last of them the one that raised)."""

    outcome: Outcome
    error: str | None
    nut_volume: float | None
    readings: list[PairReading]


@functools.cache
def interference_area(d: float, pitch: float, clearance: float, phase: float) -> float:
    """Transverse area in mm2 where a rod of the pinned profile overlaps a void of the same
    profile grown by `clearance` and turned by `phase`: 0.5 * max(0, r_b(t)^2 - (r_b(t + phase)
    + c)^2) integrated over one turn. Times the engaged length m it is the volume of the
    interference. Hand-independent: a symmetric profile's transverse section is the same for
    both hands (RESEARCH R4 read left = right).

    `phase` 0 is a matched pose, pi the half-pitch control. M6, m = 5.2: control 12.213 at
    c = 0.10, 14.1335 at 0.05, 16.1427 at 0; matched 4.3627 at c = -0.05 and exactly 0 at
    every c > 0 (RESEARCH Pattern 5). Cached: 400 000 midpoints take about 0.35 s, and the
    verdict asks for the same (size, c, phase) once per hand.
    """
    step = 2 * math.pi / INTEGRATION_POINTS
    total = math.fsum(
        max(0.0, section_radius(d, pitch, 0.0, theta) ** 2
            - section_radius(d, pitch, clearance, theta + phase) ** 2)
        for theta in ((i + 0.5) * step for i in range(INTEGRATION_POINTS)))
    return 0.5 * total * step


def closed_control(record: PairCell) -> float:
    """The closed-form volume in mm3 of the half-pitch control: engaged length times the
    interference area at phase pi. The band's centre for every control reading (D-14)."""
    return record["m"] * interference_area(record["d"], record["pitch"], record["clearance"],
                                           math.pi)


def _nut_body(record: PairCell) -> float:
    """pi d^2 m - A(c) m: the plain blank less the void thread through all of it (STACK § C:
    within 1.1e-6)."""
    d = record["d"]
    return (math.pi * d * d - section_area(d, record["pitch"], record["clearance"])) * record["m"]


def _is_empty(reading: PairReading) -> bool:
    volume = reading["volume"]
    return reading["solids"] == 0 or volume is None or abs(volume) <= EMPTY_MM3


def _off_by(reading: PairReading, closed: float) -> float:
    volume = reading["volume"]
    if volume is None:
        raise ValueError("a built reading must carry its volume")
    return abs(volume / closed - 1.0)


def _matched(record: PairRecord) -> list[PairReading]:
    return [r for r in record["readings"] if r["offset_pitches"] == 0.0]


def _controls(record: PairRecord) -> list[PairReading]:
    return [r for r in record["readings"] if r["offset_pitches"] == CONTROL_OFFSET_PITCHES]


def _is_mixed(record: PairCell) -> bool:
    return record["rod_left_hand"] != record["nut_left_hand"]


def _poses_ok(readings: list[PairReading]) -> bool:
    return tuple(r["theta"] for r in readings) == MATCHED_POSES


def cell_verdict(record: PairRecord) -> tuple[PairVerdict, tuple[str, ...]]:
    """The pre-registered rule for one cell, and why: `cell_judgement` less the closed form."""
    verdict, reasons, _ = cell_judgement(record)
    return verdict, reasons


def cell_judgement(
        record: PairRecord) -> tuple[PairVerdict, tuple[str, ...], float | None]:
    """The pre-registered rule for one cell, and why (D-12, D-14; owner ruling R1 left D-14
    exactly as written), with the closed form it judged the controls against.

    A cell that did not finish is inconclusive. So is a built cell, of either hand pairing,
    whose nut body (precise volume) misses pi d^2 m - A(c) m by more than `T_PASS`: a nut whose
    void cut failed reads non-empty at every pose, so no reading is believed, a violation
    included. A mixed-hand cell whose poses are exactly `MATCHED_POSES` and nothing else is
    `violated` when every matched pose reads non-empty, else inconclusive: an empty read at a
    pair that cannot thread proves nothing either way, and one reading at a pose chosen after the
    fact proves nothing at all. For a same-hand cell: c <= 0 is inconclusive by definition
    (D-11); poses other than the pre-registered ones are refused; any matched pose non-empty is
    `violated`; otherwise `proven` only when every matched pose is empty AND every control is
    non-empty within `PAIR_BAND` of the closed form. Anything else is inconclusive, with every
    reason. A volume that is not finite is never within `T_PASS` or `PAIR_BAND`. The diagnostic
    columns are never read.

    The third element is `closed_control(record)` where the rule got as far as the controls (a
    `proven` cell, an empty or off-band control, a control that cannot fire by geometry) and
    `None` where it ended before them: a cell that did not finish, a nut body off its closed
    form, a mixed-hand pair, c <= 0, poses that are not the pre-registered ones, a non-empty
    matched pose. A closed form nobody compared against is not reported (L02).
    """
    outcome = record["outcome"]
    if outcome != "built":
        return "inconclusive", (f"cell {outcome}: {record['error']}",), None
    nut_volume = record["nut_volume"]
    if nut_volume is None:
        raise ValueError("a built pair record must carry its nut_volume")
    body = _nut_body(record)
    # Negated `<=`, the `volume_check` pattern: every comparison with NaN is False, so the
    # positive form (`> T_PASS`) read a NaN body as on its closed form.
    if not abs(nut_volume / body - 1.0) <= T_PASS:
        return "inconclusive", (f"the nut body is {nut_volume:.6g} mm3, not the closed form "
                                f"{body:.6g} mm3 within {T_PASS:g}: no reading is believed",), None
    matched, controls = _matched(record), _controls(record)
    if _is_mixed(record):
        if controls or not _poses_ok(matched):
            return "inconclusive", ("the poses are not the pre-registered ones: a mixed-hand "
                                    "cell is read at the matched poses and nothing else "
                                    "(D-12)",), None
        reads = [r for r in matched if not _is_empty(r)]
        if len(reads) == len(matched):
            return ("violated", (f"mixed-hand pair: all {len(matched)} matched poses non-empty",),
                    None)
        return "inconclusive", (f"mixed-hand pair: {len(matched) - len(reads)} of "
                                f"{len(matched)} matched poses empty",), None
    clearance = record["clearance"]
    if clearance <= 0:
        return "inconclusive", (f"c = {clearance:g} mm: inconclusive by definition (D-11)",), None
    if not (_poses_ok(matched) and _poses_ok(controls)):
        return "inconclusive", ("the poses are not the pre-registered ones: no verdict is "
                                "drawn from poses chosen after the fact (D-12)",), None
    reads = [r for r in matched if not _is_empty(r)]
    if reads:
        return ("violated", tuple(f"matched pose theta {r['theta']:+.4f} reads "
                                  f"{r['volume']:.6g} mm3" for r in reads), None)
    closed = closed_control(record)
    if closed <= EMPTY_MM3:
        return "inconclusive", (f"control cannot fire by geometry: its closed form is "
                                f"{closed:.3g} mm3, at or below {EMPTY_MM3:g}",), closed
    reasons: list[str] = []
    for r in controls:
        if _is_empty(r):
            reasons.append(f"control at theta {r['theta']:+.4f} reads empty "
                           f"(closed form {closed:.6g} mm3)")
        elif not _off_by(r, closed) <= PAIR_BAND:  # negated, as above: a NaN control is outside
            reasons.append(f"control at theta {r['theta']:+.4f} reads {r['volume']:.6g} mm3, "
                           f"{_off_by(r, closed):.2e} off the closed form {closed:.6g} mm3: "
                           f"outside the band {PAIR_BAND:g}")
    return ("inconclusive", tuple(reasons), closed) if reasons else ("proven", (), closed)
