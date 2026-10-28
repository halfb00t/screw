"""The point sets of the phase 7 runner sweep, written once and checked ever after (07 D-04, D-05,
D-08, D-17, D-18).

The sets are pre-registered in `07-SWEEP-PROTOCOL.md` (R4) and this file is their only
definition: `python -m bench.oper_sets` writes `bench/points/{explore,spread,walls,controls}.json`
and `--check` (run by `tests/test_oper.py`, so by `make verify`) fails when a committed file is
not what this code writes, so a point file cannot drift from its generator or be edited by hand
after a reading exists (R30).

Kernel-free: a point is validated with the parameter model (`KINDS[kind].model_validate`) and
never built. A combination the model refuses is not measured and is not hidden: it goes in the
file's `dropped` array with the pydantic error type. Floats are written with `repr`, which reads
back exactly; the same code writes the same bytes, in the order it lists the points.

Symbols: `d` major diameter, `P` pitch, `L` length, `t` thread length, `s` across flats, `k` head
height, `m` nut height, `c` radial clearance, `r` root radius `d/2 - 5H/8` (plus `c` for a nut).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Context, Decimal
from fractions import Fraction
from pathlib import Path

from pydantic import ValidationError

from bench import oper_lift
from bench.oper import DEADLINE_S, POINTS_DIR, _read_records
from bench.thread_spike.maths import PITCH, SAMPLE_SIZES, standard_max
from screw.calc.thread import _exact, thread_depth
from screw.tables.presets import catalogue, expand, expand_nut, nut_catalogue

type Params = Mapping[str, float | bool]
type Lift = Mapping[str, float]

ARTIFACTS = ("stl-preview", "stl-fine", "step")
PREVIEW = ("stl-preview",)
FINE = ("stl-fine",)
RULE = "07-SWEEP-PROTOCOL.md R4"
SIGNIFICANT_FIGURES = 6
DEFAULT_NUT_CLEARANCE = 0.15  # NutParams.clearance, frozen (L02, L17)


def _hand(left_hand: bool) -> str:
    return "left" if left_hand else "right"


def _round_sig(x: Decimal, rounding: str = ROUND_HALF_UP) -> float:
    """`x` to 6 significant figures. A decimal in and a decimal out, so `1.6 * 3` is 4.8 and not
    4.800000000000001 (float noise would land in the file and in the label)."""
    exponent = x.adjusted() - SIGNIFICANT_FIGURES + 1
    return float(x.quantize(Decimal(1).scaleb(exponent), rounding=rounding))


def _below(bound: Decimal) -> float:
    """The largest number of 6 significant figures strictly below `bound`: 1e5 gives 99999.9 and
    497 gives 496.999. The most a field can be when a rule demands it stay under `bound`."""
    return float(Context(prec=SIGNIFICANT_FIGURES).next_minus(bound))


def _scaled(x: float, factor: str) -> float:
    """`factor * x` to 6 significant figures, computed as decimals."""
    return _round_sig(Decimal(factor) * Decimal(repr(x)))


def _dec(x: Fraction) -> float:
    """The float whose shortest `repr` is exactly the decimal `x`. A length that is a whole
    number of turns must stay one: float multiplication drifts (168 of 3000 float k * P products
    fail (k * P) / P == k, thread_spike/maths.py), so every turn product is formed as a fraction
    and checked on the way back. A fraction that is not a short decimal is a bug in this file."""
    value = float(x)
    if _exact(value) != x:
        raise ValueError(f"{x} is not a decimal that a float carries exactly")
    return value


def _frac(text: str) -> Fraction:
    return Fraction(text)


def _refusal(kind: str, params: Params, lift: Lift | None = None) -> str | None:
    """The pydantic error type with which the parameter model refuses `params` (with the one
    guard `lift` names lifted, if any), or `None`."""
    try:
        oper_lift.validate(kind, params, lift)
    except ValidationError as exc:
        return str(exc.errors()[0]["type"])
    return None


class _Set:
    """One point file being written: the points in the order they are added, and what the model
    refused."""

    def __init__(self, name: str, *, reps: int, shards: int, notes: list[str],
                 rule: str = RULE) -> None:
        self.name, self.reps, self.shards, self.notes, self.rule = name, reps, shards, notes, rule
        self.shard_sizes: list[int] | None = None  # only the sets generated from records (R6)
        self.sources: list[str] | None = None
        self.points: list[dict[str, object]] = []
        self.dropped: list[dict[str, object]] = []
        self._seen: set[tuple[str, str]] = set()

    def _add(self, point: dict[str, object]) -> None:
        key = (str(point["label"]), str(point.get("artifact", point.get("probe"))))
        if key in self._seen:
            raise ValueError(f"set {self.name}: {key} is listed twice")
        self._seen.add(key)
        self.points.append(point)

    def part(self, label: str, kind: str, params: Params, artifacts: tuple[str, ...] = ARTIFACTS,
             preset: str | None = None, lift: Lift | None = None) -> None:
        """`params` of `kind` at each of `artifacts`, or one `dropped` entry if the model
        refuses them (the model does not look at the artifact, so a part is judged once). A
        `lift` is the one guard a past-the-cap point lifts (`bench.oper_lift`)."""
        error = _refusal(kind, params, lift)
        if error is not None:
            refused: dict[str, object] = {"label": label, "kind": kind, "params": dict(params),
                                          "artifacts": list(artifacts), "error": error}
            if lift is not None:
                refused["lift"] = dict(lift)
            self.dropped.append(refused)
            return
        for artifact in artifacts:
            point: dict[str, object] = {"label": label, "kind": kind, "params": dict(params),
                                        "artifact": artifact}
            if preset is not None:
                point["preset"] = preset
            if lift is not None:
                point["lift"] = dict(lift)
            self._add(point)

    def probe(self, label: str, probe: str, args: Params) -> None:
        self._add({"label": label, "kind": "probe", "probe": probe, "args": dict(args)})

    def copy(self, point: Mapping[str, object]) -> None:
        """A point of another set, verbatim: params, artifact and `lift` are not rebuilt."""
        self._add(dict(point))

    def sharded(self, table: Mapping[tuple[str, str], float], sources: list[str]) -> None:
        """Cut the set into R6's consecutive shards from the explore charges and name the record
        directories it was derived from, so `--check` can write it again."""
        self.shard_sizes = shard_sizes(charges(self.points, table, DEADLINE_S), HALF_JOB_S)
        self.shards, self.sources = len(self.shard_sizes), sources

    def text(self) -> str:
        document: dict[str, object] = {
            "set": self.name, "rule": self.rule, "reps": self.reps, "shards": self.shards,
            "deadline_s": DEADLINE_S, "points": self.points, "dropped": self.dropped,
            "notes": self.notes}
        if self.shard_sizes is not None:
            document["shard_sizes"] = self.shard_sizes
        if self.sources is not None:
            document["sources"] = self.sources
        return json.dumps(document, indent=1) + "\n"


# --- explore -------------------------------------------------------------------------------------

BOLT_D = ("1", "3", "10", "30", "100", "300", "1000")
BOLT_PITCH = ("0.1", "0.35", "1", "3", "10")
BOLT_TURNS = (3, 30, 240)
NUT_D = ("3", "10", "30", "100")
NUT_PITCH = ("0.35", "1", "3.5")
NUT_M_FACTORS = ("0.8", "3")
NUT_S_FACTORS = ("1.6", "4")
NUT_CLEARANCES = (0.15, 5.0)


def _bolt_factorial(out: _Set) -> None:
    """d x P x turns x hand off the catalogue rows, with t = L = turns x P as exact decimals, so
    d and P are no longer collinear (the catalogue's d fixes P) and L / P is an integer."""
    for d in BOLT_D:
        for pitch in BOLT_PITCH:
            for turns in BOLT_TURNS:
                for left in (False, True):
                    length = _dec(turns * _frac(pitch))
                    out.part(f"bolt-d{d}-p{pitch}-n{turns}-{_hand(left)}", "bolt",
                             {"d": float(d), "pitch": float(pitch), "length": length,
                              "s": _scaled(float(d), "1.6"), "k": _scaled(float(d), "0.6"),
                              "thread_length": length, "left_hand": left})


def _nut_factorial(out: _Set) -> None:
    def add(d: str, pitch: str, m: str, s: str, clearance: float, left: bool) -> None:
        out.part(f"nut-d{d}-p{pitch}-m{m}d-s{s}d-c{clearance:g}-{_hand(left)}", "nut",
                 {"d": float(d), "pitch": float(pitch), "m": _scaled(float(d), m),
                  "s": _scaled(float(d), s), "clearance": clearance, "left_hand": left})

    for d in NUT_D:
        for pitch in NUT_PITCH:
            for m in NUT_M_FACTORS:
                for s in NUT_S_FACTORS:
                    for clearance in NUT_CLEARANCES:
                        add(d, pitch, m, s, clearance, False)
    for d in NUT_D:  # the left-hand copy of the default-clearance, 1.6 d subset
        for pitch in NUT_PITCH:
            for m in NUT_M_FACTORS:
                add(d, pitch, m, "1.6", DEFAULT_NUT_CLEARANCE, True)


def _corners(out: _Set) -> None:
    """The four corners CONTEXT records (macOS arm64 single runs), each at the artifact it was
    recorded with. The fourth cannot be requested: d = 1e5 needs s above d and s is bounded by
    the same 1e5, so the model refuses it and `dropped` says so (interim-runtime-bounds)."""
    out.part("corner-d100-L200", "bolt",
             {"d": 100.0, "length": 200.0, "s": 200.0, "k": 50.0, "thread_length": 200.0}, FINE)
    out.part("corner-d100-p5-L1250", "bolt",
             {"d": 100.0, "pitch": 5.0, "length": 1250.0, "s": 160.0, "k": 60.0,
              "thread_length": 1250.0}, FINE)
    out.part("corner-d6-p0.1-L25", "bolt", {"d": 6.0, "pitch": 0.1, "length": 25.0,
                                            "thread_length": 25.0}, FINE)
    out.part("corner-d1e5-p1-L1", "bolt",
             {"d": 1e5, "pitch": 1.0, "length": 1.0, "s": 160000.0, "k": 60000.0,
              "thread_length": 1.0}, PREVIEW)


def explore() -> _Set:
    out = _Set("explore", reps=1, shards=40, notes=[
        "(a) every ISO 4017 and ISO 4014 catalogue row and (b) every ISO 4032 row, at all three "
        "artifacts, with the row's expanded fields and its id as `preset`",
        "(c) bolt factorial d x P x turns x hand with t = L = turns x P as exact decimals, s = "
        "1.6 d and k = 0.6 d to 6 significant figures; (d) nut factorial d x P x m x s x c, "
        "right hand, plus the left-hand copy of the c 0.15, s 1.6 d subset",
        "(e) the four recorded corners; the fourth is refused by the model (s must exceed d "
        "and is bounded by 1e5) and is listed in `dropped`, not measured; `walls` walks the "
        "largest d the 1e5 ceiling allows",
        "a combination the parameter model refuses is not measured and is in `dropped` with "
        "the pydantic error type",
    ])
    for row in catalogue():
        out.part(row.id, "bolt", dict(expand(row.id) or {}), preset=row.id)
    for nut_row in nut_catalogue():
        out.part(nut_row.id, "nut", dict(expand_nut(nut_row.id) or {}), preset=nut_row.id)
    _bolt_factorial(out)
    _nut_factorial(out)
    _corners(out)
    return out


def integer_turn_rows() -> tuple[int, int]:
    """(rows whose length / pitch is a whole number of turns, rows) over the bolt catalogue,
    decided on exact decimals and never on floats (`calc.thread._exact`)."""
    rows = catalogue()
    whole = 0
    for row in rows:
        fields = dict(row.fields)
        if (_exact(fields["length"]) / _exact(fields["pitch"])).denominator == 1:
            whole += 1
    return whole, len(rows)


# --- spread --------------------------------------------------------------------------------------


def spread() -> _Set:
    out = _Set("spread", reps=5, shards=12, notes=[
        "the default bolt, the default nut and the last bolt and nut catalogue rows at the three "
        "artifacts, five repetitions each: the spread of repeated cold readings sets the margin "
        "of R5"])
    out.part("default-bolt", "bolt", {})
    out.part("default-nut", "nut", {})
    last, last_nut = catalogue()[-1], nut_catalogue()[-1]
    out.part(last.id, "bolt", dict(expand(last.id) or {}), preset=last.id)
    out.part(last_nut.id, "nut", dict(expand_nut(last_nut.id) or {}), preset=last_nut.id)
    return out


# --- walls ---------------------------------------------------------------------------------------

CEILINGS = (1e3, 1e4, 1e5)
MAX_TURNS_NOW = 250  # calc.thread.MAX_TURNS as R7 measures it
BEYOND_TURNS = 260  # one 10-turn step past it (R7's walk-down step)
BEYOND_CEILINGS = (1e6,)  # one decade past the 1e5 field ceiling (R8's grid)
NUT_CLEARANCE_D = 6.0  # NutParams.d, frozen (L02): the default nut, so only s and clearance move
TAIL_SIZES = ((6.0, 1.0), (2.0, 0.4), (20.0, 2.5))
TAIL_DECADES = tuple(range(2, 10))
ROOT_RADII = (1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6, 1e-6)
# R4 (d) and R10: the nut voids walked above group (d) after every group (d) void was refused. Every
# pitch it solves is positive; the smallest is M2 at 1 mm, 0.277 mm.
VOID_RADII = (3e-2, 1e-1, 3e-1, 1.0)
LEAD_IN_NUTS = (("M2", 2.0, 0.4, 12.0), ("M8", 8.0, 1.25, 38.0), ("M14", 14.0, 2.0, 46.0))
LEAD_IN_CEILINGS = (1e3, 1e4, 1e5)
COUNTERSINK_NUTS = ((0.05, 1.5), (0.05, 1.8), (0.01, 1.5))


def _turn_cell(kind: str, size: str, left: bool, turns: int) -> dict[str, float | bool]:
    """The rod (t = L = turns x P) or the void (`m` two pitches short of `turns`, as the builder
    adds them) of one size and hand. Shared by the walls set (250 and 260 turns), the R7 walk-down
    (240 down to 10) and the walls confirm set, so a cell is the same part at every step."""
    d_exact, pitch_exact = PITCH[size]
    d, pitch = _dec(d_exact), _dec(pitch_exact)
    if kind == "bolt":
        thread = _dec(turns * pitch_exact)
        return {"d": d, "pitch": pitch, "length": thread, "thread_length": thread,
                "s": _scaled(d, "1.6"), "k": _scaled(d, "0.6"), "left_hand": left}
    return {"d": d, "pitch": pitch, "m": _dec((turns - 2) * pitch_exact),
            "s": _scaled(d, "1.6"), "left_hand": left}


def _turn_walls(out: _Set, turns: int = MAX_TURNS_NOW, prefix: str = "turns",
                lift: Lift | None = None) -> None:
    """The rod and the void at `turns` turns at each size and hand."""
    for size in PITCH:
        for left in (False, True):
            for kind in ("bolt", "nut"):
                out.part(f"{prefix}-{kind}-{size}-{_hand(left)}", kind,
                         _turn_cell(kind, size, left, turns), PREVIEW, lift=lift)


def _ceiling_walls(out: _Set, decades: tuple[float, ...] = CEILINGS, prefix: str = "ceiling",
                   lift: Lift | None = None) -> None:
    """The field ceiling corners at each decade X of `decades`. A `lift` is the guard a decade
    past the validator's own bound needs (`bench.oper_lift`)."""

    def part(label: str, kind: str, params: Params) -> None:
        out.part(label, kind, params, PREVIEW, lift=lift)

    for x in decades:
        tag = f"{x:.0f}"
        # The head rule is s > d, so with s = X the largest d is the largest value under X.
        d_max = _below(Decimal(repr(x)))
        part(f"{prefix}-bolt-d-{tag}", "bolt",
             {"d": d_max, "s": x, "k": _scaled(d_max, "0.6"), "thread_length": 1.0})
        part(f"{prefix}-bolt-length-{tag}", "bolt", {"length": x})
        part(f"{prefix}-bolt-s-{tag}", "bolt", {"s": x})
        part(f"{prefix}-bolt-k-{tag}", "bolt", {"k": x})
        pitch = _dec(Fraction(repr(x)) / 250)
        d = _round_sig(Decimal(repr(2 * pitch)), ROUND_CEILING)
        part(f"{prefix}-bolt-thread-{tag}", "bolt",
             {"d": d, "pitch": pitch, "length": x, "thread_length": x,
              "s": _scaled(d, "1.6"), "k": _scaled(d, "0.6")})
        part(f"{prefix}-nut-s-{tag}", "nut", {"s": x})
        # nut_too_thin is s > d + 2 c, so at s = X the largest clearance is the largest value
        # under (X - d) / 2. Success at a large s alone says nothing about a large clearance.
        part(f"{prefix}-nut-clearance-{tag}", "nut",
             {"d": NUT_CLEARANCE_D, "s": x,
              "clearance": _below((Decimal(repr(x)) - Decimal(repr(NUT_CLEARANCE_D))) / 2)})
        # The same rule gives the nut's d: s = X and the default clearance leave d under X - 2 c.
        # The nut's own d bound is as high as s's, so without this probe the d ceiling would rest
        # on nothing a reading tested.
        part(f"{prefix}-nut-d-{tag}", "nut",
             {"d": _below(Decimal(repr(x)) - 2 * Decimal(repr(DEFAULT_NUT_CLEARANCE))), "s": x})
        # Pitch rounded up so m + 2 P stays at or under 250 turns of the rounded pitch.
        nut_pitch = _round_sig(Decimal(repr(x)) / Decimal(248), ROUND_CEILING)
        nut_d = _scaled(nut_pitch, "2.5")
        part(f"{prefix}-nut-m-{tag}", "nut",
             {"d": nut_d, "pitch": nut_pitch, "m": x, "s": _scaled(nut_d, "1.6")})


def _beyond_walls(out: _Set) -> None:
    """The confirmation probes of R3: the readings one step past each validator cap, the turn cap
    and the field bound, each with only that guard lifted, so they reach the kernel."""
    _turn_walls(out, BEYOND_TURNS, "beyond-turns", {"max_turns": BEYOND_TURNS})
    for x in BEYOND_CEILINGS:
        _ceiling_walls(out, (x,), "beyond", {"max_mm": x})


def _tail_label(d: float, pitch: float, left: bool, decade: int) -> str:
    return f"tail-d{d:g}-p{pitch:g}-{_hand(left)}-1e-{decade}"


def _tail_walls(out: _Set) -> None:
    for d, pitch in TAIL_SIZES:
        for left in (False, True):
            for decade in TAIL_DECADES:
                out.probe(_tail_label(d, pitch, left, decade), "tail",
                          {"d": d, "pitch": pitch, "turns": 3, "tail": float(f"1e-{decade}"),
                           "left_hand": left})


def _pitch_for_root(d: float, root: float) -> float:
    """The pitch whose root radius `d/2 - thread_depth(pitch)` is `root`, to full float
    precision. Rounded to 6 figures it would be off by up to 5e-6 mm at pitch 3.7, which is
    more than the 1e-6 mm end of the walk."""
    return (d / 2 - root) / thread_depth(1.0)


def _root_label(kind: str, size: str, left: bool, root: float) -> str:
    return f"root-{kind}-{size}-{_hand(left)}-r{root:g}"


def _void_cell(size: str, left: bool, root: float) -> dict[str, float | bool]:
    """The nut whose void has root radius `root` (3 turns). Shared by walls group (d) and the R10
    void walk, so a void is the same part in both sets."""
    d = _dec(PITCH[size][0])
    pitch = _pitch_for_root(d, root - DEFAULT_NUT_CLEARANCE)
    return {"d": d, "pitch": pitch, "m": 3 * pitch, "s": _scaled(d, "1.6"), "left_hand": left}


def _root_walls(out: _Set) -> None:
    for size, (d_exact, _) in PITCH.items():
        d = _dec(d_exact)
        for left in (False, True):
            for root in ROOT_RADII:
                pitch = _pitch_for_root(d, root)
                thread = 3 * pitch
                out.part(_root_label("bolt", size, left, root), "bolt",
                         {"d": d, "pitch": pitch, "length": thread, "thread_length": thread,
                          "s": _scaled(d, "1.6"), "k": _scaled(d, "0.6"), "left_hand": left},
                         PREVIEW)
                out.part(_root_label("nut", size, left, root), "nut",
                         _void_cell(size, left, root), PREVIEW)


def _nut_debt_walls(out: _Set) -> None:
    for size, d, pitch, m in LEAD_IN_NUTS:
        for s in LEAD_IN_CEILINGS:
            out.part(f"nutlead-{size}-s{s:g}", "nut",
                     {"d": d, "pitch": pitch, "m": m, "s": s, "clearance": 0.1}, PREVIEW)
    for clearance, pitch in COUNTERSINK_NUTS:
        out.part(f"nutcsk-d2-s4-m3-c{clearance:g}-p{pitch:g}", "nut",
                 {"d": 2.0, "pitch": pitch, "m": 3.0, "s": 4.0, "clearance": clearance}, PREVIEW)


def walls() -> _Set:
    out = _Set("walls", reps=1, shards=20, notes=[
        "preview STL unless a probe; (a) turns: 250 turns at the 15 L11 sizes, both hands, bolt "
        "(t = L = 250 P) and nut (m = 248 P, so the void m + 2 P is 250 turns), exact decimals",
        "(b) field ceilings at 1e3, 1e4 and 1e5 mm: bolt d at the largest value of 6 significant "
        "figures under X with s = X (the head rule is s > d), length, s, k, thread_length with "
        "L = t = X at 250 turns, nut s, "
        "nut m at 250 turns of void (pitch rounded up so the void stays at or under the cap)",
        "nut clearance: the default nut at s = X with the largest clearance of 6 significant "
        "figures under (X - d) / 2, the most nut_too_thin (s > d + 2 c) admits at that s",
        "nut d: s = X at the default clearance and the largest d of 6 significant figures under "
        "X - 2 c, the most nut_too_thin admits at that s",
        "(c) tails: the `tail` probe at 3 sizes, both hands, 1e-2 down to 1e-9 mm with the "
        "builder's guard lowered in the probe only, 3 whole turns before the tail",
        "(d) root radius walk: for each size and hand, r from 1e-2 down to 1e-6 mm for the "
        "bolt (d/2 - 5H/8 = r) and the nut void (d/2 - 5H/8 + 0.15 = r); the pitch is solved to "
        "full float precision, 3 turns",
        "(e) the nuts the lead-in and countersink debt items name, at s 1e3, 1e4 and 1e5 and at "
        "the countersink item's d 2, s 4, m 3 pitches and clearances",
        "(f) the confirmation probes of R3, one step past each validator cap with only that guard "
        "lifted (`lift`): 260 turns for the rod and the void of (a) with MAX_TURNS lifted to "
        "260, and the corners of (b) at 1e6 mm with the le bound of every field lifted to 1e6",
    ])
    _turn_walls(out)
    _ceiling_walls(out)
    _tail_walls(out)
    _root_walls(out)
    _nut_debt_walls(out)
    _beyond_walls(out)
    return out


# --- controls ------------------------------------------------------------------------------------


def controls() -> _Set:
    """The thread spike's `_block_controls` positions on the sample sizes, right hand: the naive
    sweep and fuse at 10 turns, 10 mm, 20 mm and the standard maximum, the one-pipe twist at the
    standard maximum and at 100, 160, 200 and 250 turns. Natively in the production image, since
    five of these rows differ between macOS and linux/amd64 (L11 platform note)."""
    out = _Set("controls", reps=1, shards=4, notes=[
        "naive_sweep_fuse and one_pipe at the positions thread_spike._block_controls uses, "
        "right hand; the ruled-surface reference needs a package and is out of this set",
        "no gate is applied: each reading records the solid count, isValid() and the precise "
        "volume as a ratio to the closed form, or the kernel's error text",
    ])
    one_pipe_turns = (100, 160, 200, 250)
    for size in SAMPLE_SIZES:
        d, pitch = PITCH[size]
        top = standard_max(d)
        for length in sorted({10 * pitch, Fraction(10), Fraction(20), top}):
            out.probe(f"naive-{size}-L{float(length):g}", "naive",
                      {"d": float(d), "pitch": float(pitch), "length": float(length)})
        for length in sorted({top, *(Fraction(t) * pitch for t in one_pipe_turns)}):
            turns = float(length / pitch)
            out.probe(f"one_pipe-{size}-t{turns:g}", "one_pipe",
                      {"d": float(d), "pitch": float(pitch), "turns": turns, "left_hand": False})
    return out


# --- the sets and decisions that come from runner records ----------------------------------------
#
# Below this line the code applies R5 to R10 to committed records: the margin, R6's charges and
# shards, the R7 walk-down set, the R10 void walk, the pre-confirm wall decisions and the walls
# confirm set. Each
# derived set carries `sources` (the record directories it came from), so `--check` writes it
# again and a hand edit fails. Every place a rule says "the phase stops and asks the owner" is a
# `ProtocolStop`, which the command line turns into exit 3: no value is chosen past it (R30).

MEASURE_TIMEOUT_MIN = 350  # `timeout-minutes` of the `measure` job; a test pins it to the workflow
HALF_JOB_S = MEASURE_TIMEOUT_MIN * 60 / 2  # R6: the other half is setup, image build and upload
REPO_ROOT = POINTS_DIR.parents[1]
GENERATED = ("walls-down", "walls-voids", "walls-confirm")
CELL_KINDS = ("bolt", "nut")
TURN_STEPS = tuple(range(240, 0, -10))  # R7, G2: the walk-down from 240 turns to 10
FAILED = frozenset({"refused", "crashed"})  # a kernel wall; killed and capped are cost (R7, R8)
CONFIRM_REPS = 5

type Reading = Mapping[str, object]
type Table = Mapping[tuple[str, str], float]


class ProtocolStop(ValueError):  # noqa: N818 - named by the plan and the rules, not an "error"
    """A rule's "the phase stops and asks the owner": `rule` names it, `reason` the readings."""

    def __init__(self, rule: str, reason: str) -> None:
        super().__init__(f"({rule}): {reason}")
        self.rule, self.reason = rule, reason


def read_readings(directory: Path) -> list[Reading]:
    """Every reading of a directory `gh run download -p 'oper-*'` wrote (one subdirectory per
    artifact, one JSONL in each), in path order."""
    files = sorted(str(path) for path in directory.glob("*/*.jsonl"))
    if not files:
        raise ValueError(f"no *.jsonl records under {directory}")
    return list(_read_records(files)[1])


def _number(reading: Reading, key: str) -> float:
    value = reading.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ProtocolStop("R2", f"the reading of {reading.get('label')} has no number {key}")
    return float(value)


def _index(readings: Iterable[Reading], rule: str) -> dict[str, Reading]:
    """Readings by label. A label read twice is not a boundary reading of either (R3)."""
    found: dict[str, Reading] = {}
    for reading in readings:
        label = str(reading["label"])
        if label in found:
            raise ProtocolStop(rule, f"{label} was read twice")
        found[label] = reading
    return found


def _need(index: Mapping[str, Reading], label: str, rule: str) -> Reading:
    if label not in index:
        raise ProtocolStop(rule, f"the reading of {label} is missing")
    return index[label]


# --- R5: the margin ------------------------------------------------------------------------------


@dataclass(frozen=True)
class SpreadPoint:
    label: str
    artifact: str
    median: float
    maximum: float

    @property
    def ratio(self) -> float:
        return self.maximum / self.median - 1


@dataclass(frozen=True)
class Margin:
    """`m`, the point that sets it, and every point's figures for the record."""

    m: float
    label: str
    artifact: str
    points: tuple[SpreadPoint, ...]


def margin(readings: Iterable[Reading],
           expected: Iterable[tuple[str, str]] | None = None) -> Margin:
    """R5: the largest `max / median - 1` of the cold wall (`build_s + export_s`) over the spread
    points, from their 5 repetitions. A point with a repetition that is not `ok`, or whose
    repetitions are not 1 to 5 each once (R3), or that is absent, has no median, so `m` has no
    number: `ProtocolStop` (G3). No figure is taken over the rest."""
    groups: dict[tuple[str, str], list[Reading]] = {}
    for reading in readings:
        groups.setdefault((str(reading["label"]), str(reading["artifact"])), []).append(reading)
    for key in expected or ():
        if key not in groups:
            raise ProtocolStop("R5", f"spread point {key[0]} at {key[1]} has no readings, so no "
                                     "median (G3)")
    points: list[SpreadPoint] = []
    for (label, artifact), group in groups.items():
        reps = sorted(str(r.get("rep")) for r in group)
        statuses = sorted({str(r["status"]) for r in group})
        if reps != ["1", "2", "3", "4", "5"] or statuses != ["ok"]:
            raise ProtocolStop("R5", f"spread point {label} at {artifact} has no median: "
                                     f"repetitions {reps}, statuses {statuses} (G3)")
        walls = [_number(r, "build_s") + _number(r, "export_s") for r in group]
        points.append(SpreadPoint(label, artifact, statistics.median(walls), max(walls)))
    if not points:
        raise ProtocolStop("R5", "there are no spread readings, so no median (G3)")
    worst = points[0]
    for point in points[1:]:
        if point.ratio > worst.ratio:
            worst = point
    return Margin(worst.ratio, worst.label, worst.artifact, tuple(points))


# --- R6: charges and shards ----------------------------------------------------------------------


def charge_table(explore_readings: Iterable[Reading]) -> dict[tuple[str, str], float]:
    """R6, G4: per (kind, artifact) the largest `wall_s` of any explore reading of the group,
    whatever its status: a reading killed at 600.4 s charges 600.4 (`wall_s` is kept for all)."""
    table: dict[tuple[str, str], float] = {}
    for reading in explore_readings:
        key = (str(reading["kind"]), str(reading["artifact"]))
        table[key] = max(table.get(key, 0.0), _number(reading, "wall_s"))
    return table


def _group(point: Mapping[str, object]) -> tuple[str, str]:
    return str(point["kind"]), str(point.get("artifact", point.get("probe")))


def charges(points: Iterable[Mapping[str, object]], table: Table,
            deadline_s: float) -> list[float]:
    """The seconds each point is charged: its group's largest explore wall, or, for a group with
    no explore reading (a probe), its `deadline_s`: no figure is invented for it (G4)."""
    return [table.get(_group(point), deadline_s) for point in points]


def shard_sizes(charged: Sequence[float], half_s: float) -> list[int]:
    """R6: the sizes of consecutive shards, each the longest prefix of the points not yet placed
    whose summed charge stays strictly under `half_s`. A charge that is not under it alone stops
    the phase: the job timeout also counts setup, the image build and the upload."""
    sizes: list[int] = []
    running = 0.0
    for index, charge in enumerate(charged):
        if charge >= half_s:
            raise ProtocolStop("R6", f"point {index + 1} is charged {charge:g} s, not under half "
                                     f"the job timeout ({half_s:g} s)")
        if sizes and running + charge < half_s:
            sizes[-1] += 1
            running += charge
        else:
            sizes.append(1)
            running = charge
    return sizes


# --- R7: the walk-down ---------------------------------------------------------------------------


def _cells() -> list[tuple[str, str, bool]]:
    """(kind, size, left) of the 60 cells, in the order the turn walls list them."""
    return [(kind, size, left) for size in PITCH for left in (False, True) for kind in CELL_KINDS]


def _stem(kind: str, size: str, left: bool) -> str:
    return f"{kind}-{size}-{_hand(left)}"


def _walk_down_set(walls_readings: Iterable[Reading]) -> _Set:
    """The walk-down set (empty when every 250-turn reading is ok): every cell whose 250-turn
    reading is refused or crashed, at every step from 240 to 10 turns, built as `walls` builds the
    250 (G2). Any other reading of a cell, or none, is a gap and a stop (R7)."""
    index = _index(walls_readings, "R7")
    out = _Set("walls-down", reps=1, shards=1, rule="07-SWEEP-PROTOCOL.md R7 (G2)", notes=[
        "every cell (size, hand, kind) whose 250-turn reading in `walls` is refused or crashed, at "
        "every step of 10 turns from 240 down to 10, 1 repetition, read in one dispatch",
        "a cell's readings below its first ok step are recorded and used for nothing (R7, G2)"])
    for kind, size, left in _cells():
        label = f"turns-{_stem(kind, size, left)}"
        status = str(_need(index, label, "R7")["status"])
        if status in FAILED:
            for turns in TURN_STEPS:
                out.part(f"turns{turns}-{_stem(kind, size, left)}", kind,
                         _turn_cell(kind, size, left, turns), PREVIEW)
        elif status != "ok":
            raise ProtocolStop("R7", f"{label} is {status}, which is cost or a gap and not a "
                                     "kernel wall: no turn bound is awarded, 250 included")
    return out


def walk_down_points(walls_readings: Iterable[Reading]) -> list[dict[str, object]]:
    """The points of the walk-down set, in file order."""
    return _walk_down_set(walls_readings).points


# --- R10: the void walk --------------------------------------------------------------------------


def _void_walk_set() -> _Set:
    """The group (d) nut at the four radii above group (d), for each size and hand (G25)."""
    out = _Set("walls-voids", reps=1, shards=1, rule="07-SWEEP-PROTOCOL.md R10 (G25)", notes=[
        "the walls group (d) nut at r in {3e-2, 1e-1, 3e-1, 1} mm for each of the 15 sizes and "
        "both hands, 3 turns, the pitch solved to full float precision (d/2 - 5H/8 + 0.15 = r), "
        "1 repetition",
        "walls run 40646134133 refused every group (d) nut void at every radius from 1e-2 mm "
        "down, so R10 walks the voids upward; the walk is not extended past 1 mm (G25)"])
    for size in PITCH:
        for left in (False, True):
            for root in VOID_RADII:
                out.part(_root_label("nut", size, left, root), "nut",
                         _void_cell(size, left, root), PREVIEW)
    return out


def void_walk_points() -> list[dict[str, object]]:
    """The points of the void walk, in file order."""
    return _void_walk_set().points


# --- R7 to R10: the candidate walls --------------------------------------------------------------

# The readings that bear on each R8 field, by stem; `ceiling-<stem>-<X>` is the reading at X mm,
# `beyond-<stem>-1000000` the lifted one a decade past the last (R3), and `nutlead-<size>-s<X>`
# the nuts the lead-in debt item names, which have no point past 1e5.
FIELD_STEMS: dict[tuple[str, str], tuple[str, ...]] = {
    ("bolt", "d"): ("bolt-d",),
    ("bolt", "length"): ("bolt-length", "bolt-thread"),
    ("bolt", "s"): ("bolt-s", "bolt-d"),
    ("bolt", "k"): ("bolt-k",),
    ("bolt", "thread_length"): ("bolt-thread",),
    ("nut", "s"): ("nut-s", *(f"nutlead-{size}" for size, *_ in LEAD_IN_NUTS)),
    ("nut", "d"): ("nut-d",),
    ("nut", "m"): ("nut-m",),
    ("nut", "clearance"): ("nut-clearance",),
}


def _bearing(stems: tuple[str, ...], x: float) -> list[str]:
    """The labels of `stems` at X mm."""
    labels: list[str] = []
    for stem in stems:
        if stem.startswith("nutlead-"):
            if x <= CEILINGS[-1]:
                labels.append(f"{stem}-s{x:g}")
        else:
            labels.append(f"{'ceiling' if x <= CEILINGS[-1] else 'beyond'}-{stem}-{x:.0f}")
    return labels


@dataclass(frozen=True)
class Ceiling:
    """A field's decided decade, its tested value (what the readings held, not always X) and the
    labels that bear on it at that decade."""

    decade: float
    value: float
    labels: tuple[str, ...]


@dataclass(frozen=True)
class Floor:
    """R9 or R10: V, or `None` for "above 0"; the readings that failed and how many were read."""

    v: float | None
    failing: tuple[str, ...]
    read: int


@dataclass(frozen=True)
class Decision:
    t: int
    first_ok: dict[str, int]
    turn_labels: tuple[str, ...]
    ceilings: dict[tuple[str, str], Ceiling]
    max_field_mm: float
    tail: Floor
    root: Floor


def _power_of_ten_at_or_above(x: Decimal) -> Decimal:
    exponent = x.adjusted()
    return Decimal(1).scaleb(exponent if x == Decimal(1).scaleb(exponent) else exponent + 1)


def _decide_turns(walls: Mapping[str, Reading],
                  down: Mapping[str, Reading]) -> tuple[int, dict[str, int], tuple[str, ...]]:
    """R7: each cell's first ok step, 250 or the highest ok step of its walk-down, and T, the
    smallest. The evidence is every reading down to a cell's first ok step; a reading in it that
    is not ok or refused or crashed, or is missing, is a stop."""
    first_ok: dict[str, int] = {}
    evidence: list[str] = []
    for kind, size, left in _cells():
        stem = _stem(kind, size, left)
        steps = [("turns", 250), *((f"turns{n}", n) for n in TURN_STEPS)]
        for position, (prefix, turns) in enumerate(steps):
            label = f"{prefix}-{stem}"
            reading = _need(walls if position == 0 else down, label, "R7")
            evidence.append(label)
            status = str(reading["status"])
            if status == "ok":
                first_ok[stem] = turns
                break
            if status not in FAILED:
                raise ProtocolStop("R7", f"{label} is {status}: cost or a gap in the boundary "
                                         "evidence, not a kernel wall; no turn bound is awarded")
        else:
            raise ProtocolStop("R7", f"cell {stem} has no ok step from 240 down to 10 turns (G2)")
    return min(first_ok.values()), first_ok, tuple(evidence)


def _decide_ceilings(walls: Mapping[str, Reading]) -> dict[tuple[str, str], Ceiling]:
    """R8: per field the largest decade at which every bearing reading is ok. A decade with a
    refused, crashed, killed or capped reading is not confirmed; a lifted reading past 1e5 is
    not among the decades (R3), so no ceiling is written above a tested value."""
    found: dict[tuple[str, str], Ceiling] = {}
    for (kind, field), stems in FIELD_STEMS.items():
        for x in reversed(CEILINGS):
            labels = _bearing(stems, x)
            readings = [_need(walls, label, "R8") for label in labels]
            if all(r["status"] == "ok" for r in readings):
                params = readings[0]["params"]
                assert isinstance(params, dict)
                found[(kind, field)] = Ceiling(x, _number(params, field), tuple(labels))
                break
        else:
            raise ProtocolStop("R8", f"{kind} {field} has no ok decade in 1e3, 1e4, 1e5 mm")
    return found


def _decide_floor(rule: str, walk: list[tuple[float, list[str]]], walls: Mapping[str, Reading],
                  factor: int) -> Floor:
    """R9 and R10 over a walk listed from its largest value down. F is the largest value with a
    refused or crashed reading; V is the smallest power of ten at or above `factor` x F, and
    must be a value the walk holds, with every reading at V or more ok. With no failure the
    floor is "above 0" and every reading must be ok. Killed and capped readings set no F and
    cannot support a bound (R8)."""
    status = {label: str(_need(walls, label, rule)["status"])
              for _, labels in walk for label in labels}
    failing = [label for label, state in status.items() if state in FAILED]
    read = len(status)
    if not failing:
        unreadable = [label for label, state in status.items() if state != "ok"]
        if unreadable:
            raise ProtocolStop(rule, f"no reading fails, but {unreadable[0]} is "
                                     f"{status[unreadable[0]]}: 'above 0' needs every reading ok")
        return Floor(None, (), read)
    f = max(value for value, labels in walk if any(status[label] in FAILED for label in labels))
    v = float(_power_of_ten_at_or_above(Decimal(repr(f)) * factor))
    if v > walk[0][0]:
        raise ProtocolStop(rule, f"the largest failing value is {f:g}, so V is {v:g}, which "
                                 f"lies outside the walk (it holds at most {walk[0][0]:g})")
    for value, labels in walk:
        for label in labels:
            if value >= v and status[label] != "ok":
                raise ProtocolStop(rule, f"{label} at or above V = {v:g} is {status[label]}, "
                                         "not ok")
    return Floor(v, tuple(failing), read)


def _tail_walk() -> list[tuple[float, list[str]]]:
    return [(float(f"1e-{k}"), [_tail_label(d, pitch, left, k)
                                for d, pitch in TAIL_SIZES for left in (False, True)])
            for k in TAIL_DECADES]


def _root_walk() -> list[tuple[float, list[str]]]:
    """R10's walk from its largest radius down: the void walk (nuts only), then group (d)."""
    voids = [(r, [_root_label("nut", size, left, r) for size in PITCH for left in (False, True)])
             for r in sorted(VOID_RADII, reverse=True)]
    group_d = [(r, [_root_label(kind, size, left, r)
                    for size in PITCH for left in (False, True) for kind in CELL_KINDS])
               for r in ROOT_RADII]
    return [*voids, *group_d]


def decide_walls(walls_readings: Iterable[Reading], down_readings: Iterable[Reading] = (),
                 voids_readings: Iterable[Reading] = ()) -> Decision:
    """R7 to R10 before the confirm: T, each field's decade and tested value, V (or "above 0")
    for the tail and the root, each with the labels it rests on. A reading that a rule needs and
    that is missing, or that is cost where a wall is needed, is a `ProtocolStop`. R10 reads
    group (d) and the void walk as one walk, so a label in both is a stop."""
    walls = _index(walls_readings, "R7")
    down = _index(down_readings, "R7")
    roots = _index([*walls.values(), *voids_readings], "R10")
    t, first_ok, turn_labels = _decide_turns(walls, down)
    ceilings = _decide_ceilings(walls)
    decades = [c.decade for c in ceilings.values()]
    shared = max(sorted(set(decades)), key=decades.count)  # a tie goes to the lower value
    return Decision(t, first_ok, turn_labels, ceilings, shared,
                    _decide_floor("R9", _tail_walk(), walls, 100),
                    _decide_floor("R10", _root_walk(), roots, 10))


# --- R3: the walls confirm set -------------------------------------------------------------------


def _walls_points() -> list[dict[str, object]]:
    return walls().points


def _confirm_floor(add: Callable[[str], None], v: float | None,
                   walk: list[tuple[float, list[str]]]) -> None:
    """R9 and R10: every cell at V and at the next smaller walked value, or, for "above 0", only
    the smallest walked value (G1). V is a value the walk holds."""
    values = [value for value, _ in walk]
    chosen = [walk[-1]] if v is None else walk[values.index(v):values.index(v) + 2]
    for _, labels in chosen:
        for label in labels:
            add(label)


def _confirm_set(decision: Decision) -> _Set:
    """The walls confirm set at 5 repetitions, generated only once T and the other candidates
    exist (R3). Points past the turn cap and the field bound are the walls set's own lifted
    ones, copied verbatim with their `lift`; every other point is built by the walls' own
    constructors, so a cell is the same part in every set."""
    source = {str(point["label"]): point for point in [*_walls_points(), *void_walk_points()]}
    out = _Set("walls-confirm", reps=CONFIRM_REPS, shards=1, rule="07-SWEEP-PROTOCOL.md R3 (G1)",
               notes=[
                   "R7: all 60 cells at T and at T + 10 turns; R8: each field's bearing readings "
                   "at its decided decade and at the next; R9 and R10: V and the next smaller "
                   "walked value, or only the smallest walked value for 'above 0'",
                   "5 repetitions taken fresh: a reading of an earlier run is not one of the 5 "
                   "(R7)"])
    seen: set[str] = set()

    def add(label: str) -> None:
        if label not in source:
            raise ProtocolStop("R3", f"{label} is not a point of the walls set or the void walk "
                                     "(the parameter model refused it)")
        if label not in seen:
            seen.add(label)
            out.copy(source[label])

    for turns in (decision.t, decision.t + 10):
        for kind, size, left in _cells():
            stem = _stem(kind, size, left)
            if turns == MAX_TURNS_NOW:
                add(f"turns-{stem}")
            elif turns == BEYOND_TURNS:
                add(f"beyond-turns-{stem}")
            else:
                out.part(f"turns{turns}-{stem}", kind, _turn_cell(kind, size, left, turns), PREVIEW)
    for key, ceiling in decision.ceilings.items():
        for x in (ceiling.decade, ceiling.decade * 10):
            for label in _bearing(FIELD_STEMS[key], x):
                add(label)
    _confirm_floor(add, decision.tail.v, _tail_walk())
    _confirm_floor(add, decision.root.v, _root_walk())
    return out


def confirm_points(decision: Decision) -> list[dict[str, object]]:
    """The points of the walls confirm set, in file order."""
    return _confirm_set(decision).points


# --- building the files from record directories --------------------------------------------------


def _relative(directory: str) -> str:
    return Path(directory).resolve().relative_to(REPO_ROOT).as_posix()


def _read(directory: str) -> list[Reading]:
    return read_readings(REPO_ROOT / directory)


def build_walk_down(walls_dir: str, explore_dir: str) -> _Set | None:
    """The walk-down set from a walls run, or `None` when every 250-turn reading is ok."""
    out = _walk_down_set(_read(walls_dir))
    if not out.points:
        return None
    out.sharded(charge_table(_read(explore_dir)), [f"walls={walls_dir}", f"explore={explore_dir}"])
    return out


def build_void_walk(explore_dir: str) -> _Set:
    """The void walk, sharded by R6 from an explore run."""
    out = _void_walk_set()
    out.sharded(charge_table(_read(explore_dir)), [f"explore={explore_dir}"])
    return out


def build_confirm(walls_dir: str, down_dir: str | None, voids_dir: str, explore_dir: str) -> _Set:
    decision = decide_walls(_read(walls_dir), _read(down_dir) if down_dir else (),
                            _read(voids_dir))
    out = _confirm_set(decision)
    sources = [f"walls={walls_dir}", *([f"walls-down={down_dir}"] if down_dir else []),
               f"walls-voids={voids_dir}", f"explore={explore_dir}"]
    out.sharded(charge_table(_read(explore_dir)), sources)
    return out


def _regenerate(path: Path) -> str:
    """The text a derived point file would have if written again from its own `sources`."""
    raw = json.loads(path.read_text())
    sources = dict(str(entry).split("=", 1) for entry in raw.get("sources", []))
    needs = {"walls-down": ("walls", "explore"), "walls-voids": ("explore",),
             "walls-confirm": ("walls", "walls-voids", "explore")}[path.stem]
    missing = [name for name in needs if name not in sources]
    if missing:
        raise ValueError(f"it names no {' and '.join(missing)} source")
    if path.stem == "walls-down":
        out = build_walk_down(sources["walls"], sources["explore"])
    elif path.stem == "walls-voids":
        out = build_void_walk(sources["explore"])
    else:
        out = build_confirm(sources["walls"], sources.get("walls-down"), sources["walls-voids"],
                            sources["explore"])
    if out is None:
        raise ValueError("its sources need no such set")
    return out.text()


# --- the command ---------------------------------------------------------------------------------


def generate() -> dict[str, str]:
    """The text of every point file, by set name, in the order the files are checked."""
    return {s.name: s.text() for s in (explore(), spread(), walls(), controls())}


def _print_margin(result: Margin) -> None:
    print("point | artifact | median cold wall s | max cold wall s | max / median - 1")
    for point in result.points:
        print(f"{point.label} | {point.artifact} | {point.median!r} | {point.maximum!r} | "
              f"{point.ratio!r}")
    print(f"m = {result.m!r}, set by {result.label} at {result.artifact}")


def _print_charges(table: Table) -> None:
    print("kind | artifact | largest explore wall_s (every status)")
    for (kind, artifact), wall in sorted(table.items()):
        print(f"{kind} | {artifact} | {wall!r}")


def _print_decision(decision: Decision) -> None:
    print(f"T = {decision.t} turns (smallest first ok step over 60 cells)")
    for stem, first in decision.first_ok.items():
        if first != MAX_TURNS_NOW:
            print(f"  cell {stem}: first ok step {first}")
    print(f"readings T rests on: {len(decision.turn_labels)}")
    for (kind, field), ceiling in decision.ceilings.items():
        print(f"{kind} {field}: decade {ceiling.decade:g}, tested value {ceiling.value!r}, "
              f"rests on {', '.join(ceiling.labels)}")
    print(f"MAX_FIELD_MM candidate: {decision.max_field_mm:g}")
    for name, floor in (("tail (R9)", decision.tail), ("root (R10)", decision.root)):
        value = "above 0" if floor.v is None else f"V = {floor.v:g} mm"
        print(f"{name}: {value}; {floor.read} readings read, failing: "
              f"{', '.join(floor.failing) or 'none'}")


def _run(args: argparse.Namespace) -> int:
    walls_dir = _relative(args.walls) if hasattr(args, "walls") else ""
    explore_dir = _relative(args.explore) if hasattr(args, "explore") else ""
    down_dir = _relative(args.down) if getattr(args, "down", None) else None
    voids_dir = _relative(args.voids) if getattr(args, "voids", None) else ""
    if args.command == "margin":
        spread_set = spread()
        expected = {(str(p["label"]), str(p["artifact"])) for p in spread_set.points}
        _print_margin(margin(_read(_relative(args.spread)), expected))
    elif args.command == "charges":
        _print_charges(charge_table(_read(explore_dir)))
    elif args.command == "walk-down":
        down = build_walk_down(walls_dir, explore_dir)
        if down is None:
            print("no walk-down: every 250-turn reading is ok")
            return 0
        Path(args.out).write_text(down.text())
        print(f"{len(down.points)} points in shards of {down.shard_sizes}")
    elif args.command == "void-walk":
        voids = build_void_walk(explore_dir)
        Path(args.out).write_text(voids.text())
        print(f"{len(voids.points)} points in shards of {voids.shard_sizes}")
    elif args.command == "decide-walls":
        _print_decision(decide_walls(_read(walls_dir), _read(down_dir) if down_dir else (),
                                     _read(voids_dir)))
    else:
        confirm = build_confirm(walls_dir, down_dir, voids_dir, explore_dir)
        Path(args.out).write_text(confirm.text())
        print(f"{len(confirm.points)} points in shards of {confirm.shard_sizes}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bench.oper_sets", description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 naming the first committed file that is not what this writes")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("margin", help="R5 over a spread run").add_argument("--spread", required=True)
    sub.add_parser("charges", help="R6 charges over an explore run").add_argument(
        "--explore", required=True)
    void_walk = sub.add_parser("void-walk", help="write the R10 void walk")
    void_walk.add_argument("--explore", required=True)
    void_walk.add_argument("--out", required=True)
    for name, helptext in (("walk-down", "write the R7 walk-down set"),
                           ("decide-walls", "R7 to R10 before the confirm"),
                           ("confirm", "write the walls confirm set")):
        command = sub.add_parser(name, help=helptext)
        command.add_argument("--walls", required=True)
        if name != "walk-down":
            command.add_argument("--down")
            command.add_argument("--voids", required=True)
        if name != "decide-walls":
            command.add_argument("--explore", required=True)
            command.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command is not None:
        try:
            return _run(args)
        except ProtocolStop as exc:
            print(f"oper_sets: stop {exc}", file=sys.stderr)
            return 3
        except ValueError as exc:
            print(f"oper_sets: {exc}", file=sys.stderr)
            return 2
    whole, rows = integer_turn_rows()
    print(f"integer L/P: {whole} of {rows}")
    texts = generate()
    if args.check:
        for name, text in texts.items():
            path = POINTS_DIR / f"{name}.json"
            if not path.is_file() or path.read_text() != text:
                print(f"oper_sets: {path} is not what the generator writes", file=sys.stderr)
                return 1
        for name in GENERATED:
            path = POINTS_DIR / f"{name}.json"
            if not path.is_file():
                continue
            try:
                same = path.read_text() == _regenerate(path)
            except ValueError as exc:  # a stop is a ValueError: the sources no longer give a set
                print(f"oper_sets: {path} cannot be written again from its sources: {exc}",
                      file=sys.stderr)
                return 1
            if not same:
                print(f"oper_sets: {path} is not what the generator writes from its sources",
                      file=sys.stderr)
                return 1
        return 0
    for name, text in texts.items():
        (POINTS_DIR / f"{name}.json").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
