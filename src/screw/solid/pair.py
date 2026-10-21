"""The kernel pair proof: does this nut mate with the nominal rod of its own size and hand?

The measured bodies moved here from `bench/thread_spike/pair.py` unchanged (02 D-18, 05 D-05:
what was measured is what ships), and the spike imports them back. A pair is a rod piece, the
thread at clearance 0 over m + 2P from z = -P, and a blank, a plain cylinder of radius d and
height m (the hex adds nothing to a thread proof and its dimensions would be invented) less the
void thread of the nut's clearance over the same span. Poses are screw motions, so every matched
pose is the same physical configuration with the seam moved (RESEARCH Pattern 5). `prove` reads
the three matched poses and their half-pitch controls and judges them with `screw.calc.pair`,
the rule the spike measured.

The boolean is parked in `_KEEP` because freeing it segfaults at teardown (exit 139, RESEARCH
F5, provoked once), so any process that runs `common` must end with `os._exit` after flushing,
and tests run it in a child process only. Nothing here is reachable from the serving process
(import-linter, and the runtime probe in `tests/test_import_boundaries.py`, D-24); no kernel
type escapes: `prove` returns a pydantic document of plain numbers.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from fractions import Fraction

import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.TopTools import TopTools_ListOfShape
from pydantic import BaseModel, ConfigDict

from screw.calc.pair import (
    CONTROL_OFFSET_PITCHES,
    MATCHED_POSES,
    PAIR_BAND,
    PairCell,
    PairRecord,
    PairVerdict,
    ReadingOutcome,
    cell_judgement,
)
from screw.calc.pair import PairReading as PairReadingRow
from screw.calc.presets import counterpart_for
from screw.calc.thread import TIP_ANGLE_DEG, tip_cone_length
from screw.params import BoltParams, NutParams
from screw.solid import build, helical, precise_volume

# The boolean and its filler are kept for the life of the process: freeing them segfaulted at
# teardown (exit 139, RESEARCH Pitfall 4, provoked once), which is also why a process that ends
# normally after `common` dies at teardown and a CLI ends with `os._exit` after flushing.
# For the same reason tests call `common` only in a child process, never in pytest's own.
_KEEP: list[object] = []

# What `common` returns and a test's fake must too: (precise volume, solid count, filler had
# errors, filler had warnings, seconds).
Boolean = Callable[[cq.Shape, cq.Shape], tuple[float, int, bool, bool, float]]


def _span(pitch: float, m: float) -> float:
    """The m + 2P span in mm, exactly: float arithmetic on the decimals drifts ((1.6 + 2 * 0.4)
    is not 2.4), and `str` of a float is its shortest round trip, so the sum is taken on the
    decimals the protocol wrote."""
    return float(Fraction(str(m)) + 2 * Fraction(str(pitch)))


def rod_piece(d: float, pitch: float, m: float, left_hand: bool, k: int) -> cq.Solid:
    """The rod over z in [-P, m + P]: a pad of one pitch each side covers every placed nut as
    long as a pose slides it by no more than P (RESEARCH Pitfall 2)."""
    rod = helical.thread(d, pitch, _span(pitch, m), clearance=0.0, left_hand=left_hand, k=k)
    return rod.translate(cq.Vector(0, 0, -pitch))


def blank(d: float, pitch: float, m: float, clearance: float, left_hand: bool,
          k: int) -> cq.Solid:
    """A plain blank of radius d and height m over z in [0, m], less the void thread of this
    clearance through all of it. One solid or a raised error: a nut body in pieces is a defect of
    the build, and its volume would not be the closed form's. This is the verdict body, not the
    shipped nut (`screw.solid.nut`)."""
    void = helical.thread(d, pitch, _span(pitch, m), clearance=clearance, left_hand=left_hand,
                          k=k).translate(cq.Vector(0, 0, -pitch))
    solids = cq.Solid.makeCylinder(d, m).cut(void).Solids()
    if len(solids) != 1:
        raise ValueError(f"the nut body has {len(solids)} solids, not 1")
    return solids[0]


def place(blank: cq.Solid, theta: float, offset_pitches: float, pitch: float,
          left_hand: bool) -> cq.Solid:
    """The nut turned by `theta` about z and slid by sign * theta * P / 2 pi (sign -1 for left
    hand: a left-hand thread advances the other way) plus `offset_pitches` pitches. The screw
    motion keeps a matched pose physically identical; half a pitch more is the control."""
    sign = -1.0 if left_hand else 1.0
    slide = sign * theta * pitch / (2 * math.pi) + offset_pitches * pitch
    turned = blank.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), math.degrees(theta))
    return turned.translate(cq.Vector(0, 0, slide))


def check_cover(rod: cq.Shape, placed: cq.Shape) -> None:
    """Raise unless the rod's z range covers the placed nut's. A nut hanging off the rod shrinks
    the engaged length and the control reads below its closed form, silently, so a violated
    cover is a defect of this harness, never a measurement."""
    rod_box, nut_box = rod.BoundingBox(), placed.BoundingBox()
    if rod_box.zmin > nut_box.zmin or rod_box.zmax < nut_box.zmax:
        raise ValueError(
            f"the rod covers z in [{rod_box.zmin:.4f}, {rod_box.zmax:.4f}] but the placed nut "
            f"spans [{nut_box.zmin:.4f}, {nut_box.zmax:.4f}]: the pose slides past the pad")


def common(a: cq.Shape, b: cq.Shape) -> tuple[float, int, bool, bool, float]:
    """The boolean intersection of `a` and `b`: (precise volume, solid count, filler had errors,
    filler had warnings, seconds). An empty result has volume 0.0 and 0 solids.

    The two flags are columns for the reader and never a verdict input: in research they were
    False on every false-empty control (RESEARCH Pitfall 4).
    """
    t0 = time.perf_counter()
    op = BRepAlgoAPI_Common()
    first, second = TopTools_ListOfShape(), TopTools_ListOfShape()
    first.Append(a.wrapped)
    second.Append(b.wrapped)
    op.SetArguments(first)
    op.SetTools(second)
    op.Build()
    filler = op.DSFiller()
    _KEEP.append((op, filler))
    shape = op.Shape()
    solids = [] if shape.IsNull() else cq.Shape.cast(shape).Solids()
    volume = precise_volume(cq.Shape.cast(shape)) if solids else 0.0
    return (volume, len(solids), bool(filler.HasErrors()), bool(filler.HasWarnings()),
            time.perf_counter() - t0)


class PairReading(BaseModel):
    """One pose's boolean, as `calc.pair.PairReading` records it. `offset_pitches` is 0 at a
    matched pose and 0.5 at a control; a `failure` reading carries no measurement."""

    model_config = ConfigDict(frozen=True)

    theta: float
    offset_pitches: float
    outcome: ReadingOutcome
    solids: int | None
    volume: float | None
    diag_errors: bool | None
    diag_warnings: bool | None
    seconds: float | None


class ShippedReading(BaseModel):
    """The shipped bolt against the shipped nut at one matched pose: evidence, never a verdict
    input. A `failure` carries no measurement and says why in `error`."""

    model_config = ConfigDict(frozen=True)

    theta: float
    outcome: ReadingOutcome
    solids: int | None
    volume: float | None
    seconds: float | None
    error: str | None


class PairReport(BaseModel):
    """What `prove` found, the document the CLI prints (D-06): the verdict and every reason, the
    pair it judged, each pose's reading in the order taken (matched poses, then controls), the
    control's closed form and the band around it, the shipped-solid evidence row and the seconds
    the proof took.

    `closed_control` is present where the rule judged the control readings against it, or found it
    at or below `EMPTY_MM3` and so a control that cannot fire; it is then the number every reason
    that quotes a closed form quotes. It is `None` where the rule ended before the controls:
    nothing was read (c <= 0), a mixed-hand pair, a cell that did not finish, a nut body off its
    closed form, or a non-empty matched pose (L02: a closed form nobody compared against is not
    printed). `shipped` is `None` where the row was not taken: it was not asked for, nothing was
    read (c <= 0) or the cell did not finish.
    """

    model_config = ConfigDict(frozen=True)

    verdict: PairVerdict
    reasons: list[str]
    d: float
    pitch: float
    m: float
    clearance: float
    rod_left_hand: bool
    nut_left_hand: bool
    readings: list[PairReading]
    closed_control: float | None
    band: float
    engagement_turns: float
    shipped: list[ShippedReading] | None
    seconds: float


def _echo(row: PairReadingRow) -> PairReading:
    return PairReading.model_validate(row)


def _finite(volume: float, what: str) -> float:
    """`volume`, or a `ValueError` naming `what` when it is NaN or infinite. A kernel `Mass()` on a
    degenerate boolean can be NaN, and a NaN compares as inside every tolerance, so it is refused
    where it is read, as the spike's record parser refuses one at its boundary
    (`bench/thread_spike/verdict.py` `_num`, L02)."""
    if not math.isfinite(volume):
        raise ValueError(f"{what} read {volume!r}, not a finite number")
    return volume


def _record(cell: PairCell, poses: list[tuple[float, float]], boolean: Boolean) -> PairRecord:
    """Build the rod and the blank once, record the blank's precise volume, then read every
    (theta, offset) as a placed blank, a cover check and one boolean. A Python exception ends the
    cell as a `failure` that keeps the readings taken so far, the last of them the pose that
    raised; nothing is retried toward a result. Nothing is judged here."""
    readings: list[PairReadingRow] = []
    nut_volume: float | None = None
    pose: tuple[float, float] | None = None
    try:
        rod = rod_piece(cell["d"], cell["pitch"], cell["m"], cell["rod_left_hand"], cell["k"])
        body = blank(cell["d"], cell["pitch"], cell["m"], cell["clearance"],
                     cell["nut_left_hand"], cell["k"])
        nut_volume = _finite(precise_volume(body), "the nut body's precise volume")
        for pose in poses:
            theta, offset = pose
            placed = place(body, theta, offset, cell["pitch"], cell["nut_left_hand"])
            check_cover(rod, placed)
            volume, solids, errors, warnings, seconds = boolean(rod, placed)
            _finite(volume, f"the boolean at theta {theta:+.4f}, {offset:g} pitches")
            readings.append({
                "theta": theta, "offset_pitches": offset, "outcome": "built", "solids": solids,
                "volume": volume, "diag_errors": errors, "diag_warnings": warnings,
                "seconds": seconds})
    except Exception as exc:  # any kernel exception is one recorded cell, not a dead process
        if pose is not None:
            readings.append({
                "theta": pose[0], "offset_pitches": pose[1], "outcome": "failure", "solids": None,
                "volume": None, "diag_errors": None, "diag_warnings": None, "seconds": None})
        return {**cell, "outcome": "failure", "error": f"{type(exc).__name__}: {exc}",
                "nut_volume": nut_volume, "readings": readings}
    return {**cell, "outcome": "built", "error": None, "nut_volume": nut_volume,
            "readings": readings}


def _shipped(p: NutParams, rod_hand: bool, boolean: Boolean) -> list[ShippedReading]:
    """`build(BoltParams)` against `build(NutParams)` at the three matched poses: the counterpart
    bolt (`counterpart_for`'s fields, the rod's hand, length = thread_length = tip cone length +
    m + 2 pitch, so the thread fills the bolt and the head sits past it) and the shipped nut.

    The nut starts a whole number of pitches up, the least that clears the tip cone by a pitch:
    the thread has phase 2 pi z / P on both parts, so a start that is not a multiple of the pitch
    would put every "matched" pose half a thread out of step (measured on M6, c = 0.10, 2026-10-20:
    start at the cone length + P reads 8.747 mm3 at all three poses, start at 2 P reads empty).
    A build or a boolean that raises is a `failure` reading, never a retry and never a zero.
    """
    try:
        counterpart, _ = counterpart_for(p)
        tip = tip_cone_length(p.pitch, TIP_ANGLE_DEG)
        length = tip + p.m + 2 * p.pitch
        bolt = build(BoltParams.model_validate({
            **counterpart.fields, "left_hand": rod_hand, "length": length,
            "thread_length": length}))
        nut = build(p)
    except Exception as exc:  # a bolt that cannot be built is one recorded failure, not a crash
        error = f"{type(exc).__name__}: {exc}"
        return [ShippedReading(theta=theta, outcome="failure", solids=None, volume=None,
                               seconds=None, error=error) for theta in MATCHED_POSES]
    start = math.ceil((tip + p.pitch) / p.pitch)
    readings: list[ShippedReading] = []
    for theta in MATCHED_POSES:
        try:
            volume, solids, _, _, seconds = boolean(bolt, place(nut, theta, start, p.pitch,
                                                                p.left_hand))
            _finite(volume, f"the shipped boolean at theta {theta:+.4f}")
        except Exception as exc:  # as above, per pose
            readings.append(ShippedReading(
                theta=theta, outcome="failure", solids=None, volume=None, seconds=None,
                error=f"{type(exc).__name__}: {exc}"))
        else:
            readings.append(ShippedReading(theta=theta, outcome="built", solids=solids,
                                           volume=volume, seconds=seconds, error=None))
    return readings


def prove(p: NutParams, *, rod_left_hand: bool | None = None, shipped: bool = True,
          common: Boolean = common) -> PairReport:
    """Whether the nut `p` mates with the nominal rod of its own d, pitch and hand: the spike's
    bodies read at the three matched poses and their half-pitch controls, judged by
    `screw.calc.pair.cell_judgement`.

    `rod_left_hand` is the rod's hand when it differs from the nut's (owner ruling R7): internal,
    for the rule's mixed-hand cells, never a CLI flag or a model field. A mixed pair is read at
    the matched poses only, as the rule requires. At c <= 0 `prove` reads nothing (R8, D-11): the
    verdict is inconclusive by definition, the readings are empty and `common` is not called.
    `shipped` adds the evidence row: the shipped bolt and nut intersected at the matched poses,
    printed in `PairReport.shipped` beside the verdict. It is evidence and never a verdict input,
    until a later campaign pre-registers expectations for it (D-05); it is taken after the
    verdict's own readings and only from a cell that finished.
    `common` is the boolean, a seam so the orchestration is tested without the kernel; the real
    one parks its operation in `_KEEP` (see the module docstring for the exit rule).
    """
    start = time.perf_counter()
    rod_hand = p.left_hand if rod_left_hand is None else rod_left_hand
    mixed = rod_hand != p.left_hand
    cell: PairCell = {
        "size": f"d{p.d:g}xP{p.pitch:g}", "d": p.d, "pitch": p.pitch, "m": p.m,
        "clearance": p.clearance, "rod_left_hand": rod_hand, "nut_left_hand": p.left_hand,
        "k": helical.DEFAULT_K}
    readings: list[PairReading] = []
    closed: float | None = None
    evidence: list[ShippedReading] | None = None
    if p.clearance <= 0:
        verdict: PairVerdict = "inconclusive"
        reasons: tuple[str, ...] = (f"c = {p.clearance:g} mm: inconclusive by definition (D-11)",)
    else:
        poses = [(theta, 0.0) for theta in MATCHED_POSES]
        if not mixed:
            poses += [(theta, CONTROL_OFFSET_PITCHES) for theta in MATCHED_POSES]
        record = _record(cell, poses, common)
        verdict, reasons, closed = cell_judgement(record)
        readings = [_echo(row) for row in record["readings"]]
        if shipped and record["outcome"] == "built":
            evidence = _shipped(p, rod_hand, common)
    return PairReport(
        verdict=verdict, reasons=list(reasons), d=p.d, pitch=p.pitch, m=p.m,
        clearance=p.clearance, rod_left_hand=rod_hand, nut_left_hand=p.left_hand,
        readings=readings, closed_control=closed, band=PAIR_BAND,
        engagement_turns=p.m / p.pitch, shipped=evidence, seconds=time.perf_counter() - start)
