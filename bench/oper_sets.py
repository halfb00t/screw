"""The point sets of the phase 7 runner sweep, written once and checked ever after (07 D-04, D-05,
D-08, D-17, D-18).

The sets are pre-registered in `07-SWEEP-PROTOCOL.md` (R4) and this file is their only
definition: `python -m bench.oper_sets` writes `bench/points/{explore,spread,walls,controls}.json`
and `--check` (run by `tests/test_oper.py`, so by `make verify`) fails when a committed file is
not what this code writes, so a point file cannot drift from its generator or be edited by hand
after a reading exists (R30).

Kernel-free: a point is validated with the parameter model under the guards of the registration
(`bench.oper_lift.registered`, so the files do not move with the walls of L20) and never built. A
combination the model refuses is not measured and is not hidden: it goes in the file's `dropped`
array with the pydantic error type. Floats are written with `repr`, which reads back exactly; the
same code writes the same bytes, in the order it lists the points.

Symbols: `d` major diameter, `P` pitch, `L` length, `t` thread length, `s` across flats, `k` head
height, `m` nut height, `c` radial clearance, `r` root radius `d/2 - 5H/8` (plus `c` for a nut).
"""

from __future__ import annotations

import argparse
import dataclasses
import functools
import json
import math
import random
import statistics
import sys
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Context, Decimal
from fractions import Fraction
from pathlib import Path

from pydantic import ValidationError

from bench import oper_lift
from bench.oper import CONTENTION_WORKERS, DEADLINE_S, POINTS_DIR, _read_records
from bench.thread_spike.maths import PITCH, SAMPLE_SIZES, standard_max
from screw.calc import cost
from screw.calc.thread import _exact, built_thread_length, thread_depth
from screw.params import KINDS, BoltParams, FastenerParams
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
    """The pydantic error type with which the parameter model refuses `params` under the guards
    of the registration (with the one guard `lift` names lifted, if any), or `None`. Not the
    production guards: the point files are pre-registered (R30) and must not move when L20 sets
    the walls the sweep measured (`bench.oper_lift.registered`)."""
    try:
        oper_lift.registered(kind, params, lift)
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
        self.envelope: dict[str, dict[str, dict[str, float]]] | None = None  # Runs II (G6)
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
        if self.envelope is not None:
            document["envelope"] = self.envelope
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
# R4 (d): the nut voids walked above group (d) after every group (d) void was refused. They are
# recorded and bear on no R10 bound (G26). Every pitch is positive; the smallest is M2 at 1 mm,
# 0.277 mm.
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


def _floor_from_status(rule: str, walk: list[tuple[float, list[str]]],
                       status: Mapping[str, str], factor: int) -> Floor:
    """R9 and R10 over a walk listed from its largest value down, given the status of each label.
    F is the largest value with a refused or crashed reading; V is the smallest power of ten at or
    above `factor` x F, and must be a value the walk holds, with every reading at V or more ok.
    With no failure the floor is "above 0" and every reading must be ok. Killed and capped
    readings set no F and cannot support a bound (R8)."""
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


def _decide_floor(rule: str, walk: list[tuple[float, list[str]]], walls: Mapping[str, Reading],
                  factor: int) -> Floor:
    """R9 and R10 over the walls readings alone, before the confirm."""
    status = {label: str(_need(walls, label, rule)["status"])
              for _, labels in walk for label in labels}
    return _floor_from_status(rule, walk, status, factor)


def _tail_walk() -> list[tuple[float, list[str]]]:
    return [(float(f"1e-{k}"), [_tail_label(d, pitch, left, k)
                                for d, pitch in TAIL_SIZES for left in (False, True)])
            for k in TAIL_DECADES]


def _root_walk() -> list[tuple[float, list[str]]]:
    """R10's walk from its largest radius down, the rods of group (d) only. The nut readings of
    group (d) and the void walk are recorded and bear on no bound (G26): the voids failed up to a
    root radius that grows with d, so no floor in millimetres holds them."""
    return [(r, [_root_label("bolt", size, left, r) for size in PITCH for left in (False, True)])
            for r in ROOT_RADII]


def decide_walls(walls_readings: Iterable[Reading],
                 down_readings: Iterable[Reading] = ()) -> Decision:
    """R7 to R10 before the confirm: T, each field's decade and tested value, V (or "above 0")
    for the tail and the root, each with the labels it rests on. A reading that a rule needs and
    that is missing, or that is cost where a wall is needed, is a `ProtocolStop`. R10 reads the
    rods of group (d) only (G26)."""
    walls = _index(walls_readings, "R7")
    down = _index(down_readings, "R7")
    t, first_ok, turn_labels = _decide_turns(walls, down)
    ceilings = _decide_ceilings(walls)
    decades = [c.decade for c in ceilings.values()]
    shared = max(sorted(set(decades)), key=decades.count)  # a tie goes to the lower value
    return Decision(t, first_ok, turn_labels, ceilings, shared,
                    _decide_floor("R9", _tail_walk(), walls, 100),
                    _decide_floor("R10", _root_walk(), walls, 10))


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
    source = {str(point["label"]): point for point in _walls_points()}
    out = _Set("walls-confirm", reps=CONFIRM_REPS, shards=1, rule="07-SWEEP-PROTOCOL.md R3 (G1)",
               notes=[
                   "R7: all 60 cells at T and at T + 10 turns; R8: each field's bearing readings "
                   "at its decided decade and at the next; R9 and R10: V and the next smaller "
                   "walked value (R10: the rods of group (d) only), or only the smallest "
                   "walked value for 'above 0'",
                   "5 repetitions taken fresh: a reading of an earlier run is not one of the 5 "
                   "(R7)"])
    seen: set[str] = set()

    def add(label: str) -> None:
        if label not in source:
            raise ProtocolStop("R3", f"{label} is not a point of the walls set (the parameter "
                                     "model refused it)")
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


# --- R3, R7 to R10: the walls, decided with their confirm ----------------------------------------

# G27: the fields whose limit is cost and not a wall when the confirm reads `capped` at their one
# decade below the first refused one. They write no constant of their own and stay under the
# shared MAX_FIELD_MM, which must lie below that refused decade (R8).
COST_LIMITED = frozenset({("nut", "d")})


@dataclass(frozen=True)
class Derived:
    """The walls R3 and R7 to R10 decide from the walls, walk-down and confirm records: what to
    write into the code (`max_turns`, `max_field_mm`, `constants`, the two floors) and what each
    rests on, for the log (`past`, `notes`)."""

    candidate: Decision
    max_turns: int
    turn_labels: tuple[str, ...]
    ceilings: dict[tuple[str, str], Ceiling]
    cost_limited: dict[tuple[str, str], float]  # field -> its first refused decade, mm
    max_field_mm: float
    constants: dict[str, float]
    tail: Floor
    root: Floor
    past: dict[str, str]  # wall -> the confirm readings one step past it
    notes: tuple[str, ...]  # where the final value differs from the candidate


def _confirm_groups(readings: Iterable[Reading]) -> dict[str, list[Reading]]:
    found: dict[str, list[Reading]] = {}
    for reading in readings:
        found.setdefault(str(reading["label"]), []).append(reading)
    return found


def _five(confirm: Mapping[str, list[Reading]], label: str, rule: str) -> list[Reading]:
    """The 5 repetitions of a confirm point. The repetitions must be the ones asked for, 1 to 5
    each once (R3): a copy of one is `R3`'s stop, a gap is the stop of the rule that needs the
    point."""
    group = confirm.get(label)
    if not group:
        raise ProtocolStop(rule, f"the confirm reading of {label} is missing (R3)")
    wanted = list(range(1, CONFIRM_REPS + 1))
    reps = [r.get("rep") for r in group]
    if (len(set(map(str, reps))) != len(reps)
            or any(isinstance(rep, bool) or rep not in wanted for rep in reps)):
        raise ProtocolStop("R3", f"the confirm of {label} has repetitions "
                                 f"{sorted(map(str, reps))}, not 1 to 5 each once")
    gaps = [rep for rep in wanted if rep not in reps]
    if gaps:
        raise ProtocolStop(rule, f"the confirm of {label} lacks repetitions {gaps} of 1 to 5 (R3)")
    return group


def _worst(states: Iterable[str]) -> str:
    """A disagreement keeps the stricter outcome (R3): a kernel failure over cost over ok."""
    found = list(states)
    for state in found:
        if state in FAILED:
            return state
    return next((state for state in found if state != "ok"), "ok")


def _state(label: str, walls: Mapping[str, Reading], confirm: Mapping[str, list[Reading]],
           rule: str) -> str:
    """The status of a label: its walls reading, and where the confirm holds it, the 5 confirm
    repetitions, the stricter of them all."""
    state = str(_need(walls, label, rule)["status"])
    if label in confirm:
        return _worst([state, *(str(r["status"]) for r in _five(confirm, label, rule))])
    return state


def _turn_label(turns: int, stem: str) -> str:
    if turns == MAX_TURNS_NOW:
        return f"turns-{stem}"
    return f"beyond-turns-{stem}" if turns == BEYOND_TURNS else f"turns{turns}-{stem}"


def _summary(confirm: Mapping[str, list[Reading]], labels: Sequence[str]) -> str:
    """The confirm statuses of `labels` over their 5 repetitions, for the log: one clause per
    distinct outcome, with the labels when there are few and their number when there are many."""
    by_outcome: dict[str, list[str]] = {}
    for label in labels:
        if label not in confirm:
            by_outcome.setdefault("not read", []).append(label)
            continue
        counts: dict[str, int] = {}
        for reading in _five(confirm, label, "R3"):
            counts[str(reading["status"])] = counts.get(str(reading["status"]), 0) + 1
        outcome = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
        by_outcome.setdefault(outcome, []).append(label)
    return "; ".join(
        f"{', '.join(found)}: {outcome}" if len(found) <= 4
        else f"{len(found)} of {len(labels)} points: {outcome}"
        for outcome, found in by_outcome.items())


def _derive_turns(t: int, confirm: Mapping[str, list[Reading]]) -> tuple[str, ...]:
    """R7: `MAX_TURNS` is T only if every cell is ok in all 5 confirm repetitions at T. Anything
    else, a gap included, awards no turn bound, 250 included, and stops the phase."""
    labels: list[str] = []
    for kind, size, left in _cells():
        label = _turn_label(t, _stem(kind, size, left))
        group = _five(confirm, label, "R7")
        bad = [r for r in group if r["status"] != "ok"]
        if bad:
            raise ProtocolStop("R7", f"the confirm of {label} at T = {t} is {bad[0]['status']} in "
                                     f"{len(bad)} of 5 repetitions: no turn bound is awarded, "
                                     "250 included")
        labels.append(label)
    return tuple(labels)


def _derive_ceilings(
        candidate: Decision, walls: Mapping[str, Reading],
        confirm: Mapping[str, list[Reading]]) -> tuple[dict[tuple[str, str], Ceiling],
                                                      dict[tuple[str, str], float]]:
    """R8 over the walls readings and the confirm together: a field's ceiling is the largest
    decade at which every bearing reading is ok in both, the tested value that decade held. A
    candidate decade the confirm does not hold stops the phase; a decade the confirm lowered the
    candidate to is a stricter wall and needs none. A reading past 1e5 is lifted and is never a
    decade here (R3)."""
    ceilings: dict[tuple[str, str], Ceiling] = {}
    cost_limited: dict[tuple[str, str], float] = {}
    for key, stems in FIELD_STEMS.items():
        kind, field = key
        states_by_decade: dict[float, list[str]] = {}
        for x in reversed(CEILINGS):
            labels = _bearing(stems, x)
            states = [_state(label, walls, confirm, "R8") for label in labels]
            states_by_decade[x] = states
            if not all(state == "ok" for state in states):
                continue
            if x >= candidate.ceilings[key].decade:
                unheld = [label for label in labels if label not in confirm]
                if unheld:
                    raise ProtocolStop("R8", f"no confirm reading tested {kind} {field} at "
                                             f"{x:g} mm: {unheld[0]} is missing (R3)")
            params = _need(walls, labels[0], "R8")["params"]
            assert isinstance(params, dict)
            ceilings[key] = Ceiling(x, _number(params, field), tuple(labels))
            break
        else:
            refused = [x for x, states in states_by_decade.items()
                       if any(state in FAILED for state in states)]
            lowest = states_by_decade[CEILINGS[0]]
            if key in COST_LIMITED and refused and not any(s in FAILED for s in lowest):
                cost_limited[key] = min(refused)
                continue
            raise ProtocolStop("R8", f"{kind} {field} has no ok decade in 1e3, 1e4, 1e5 mm after "
                                     "the confirm")
    return ceilings, cost_limited


def _derive_floor(rule: str, walk: list[tuple[float, list[str]]], candidate: Floor,
                  walls: Mapping[str, Reading], confirm: Mapping[str, list[Reading]],
                  factor: int) -> Floor:
    """R9 or R10 over the walls readings and the confirm together. A confirm repetition that
    fails sets an F the walls did not (a stricter, higher floor), and V must then have been
    confirmed itself, never taken from one repetition (R3). "Above 0" stands only on the
    confirm at the smallest walked value for every cell, ok in all 5 repetitions (G1)."""
    status = {label: _state(label, walls, confirm, rule) for _, labels in walk for label in labels}
    if candidate.v is None:
        for label in walk[-1][1]:
            if label not in confirm:
                raise ProtocolStop(rule, f"'above 0' needs the confirm at {walk[-1][0]:g}, and "
                                         f"{label} is missing: no floor is awarded (G1)")
        bad = [label for label, state in status.items() if state != "ok"]
        if bad:
            raise ProtocolStop(rule, f"'above 0' needs every reading ok, and {bad[0]} is "
                                     f"{status[bad[0]]} after the confirm: no floor is awarded "
                                     "(G1)")
        return Floor(None, (), len(status))
    floor = _floor_from_status(rule, walk, status, factor)
    assert floor.v is not None
    held = [label for value, labels in walk if value == floor.v for label in labels]
    unheld = [label for label in held if label not in confirm]
    if unheld:
        raise ProtocolStop(rule, f"after the confirm V = {floor.v:g}, and no confirm reading "
                                 f"tested it: {unheld[0]} is missing (R3)")
    return floor


def derive_walls(walls_readings: Iterable[Reading], down_readings: Iterable[Reading],
                 confirm_readings: Iterable[Reading]) -> Derived:
    """R7 to R10 and R3: the candidate walls of `decide_walls`, then the walls confirm applied to
    them (07 D-08, D-18).

    R7: `MAX_TURNS` is T only when every one of the 60 cells has all 5 confirm repetitions at T
    ok. R8 to R10 are computed over the walls readings and the confirm readings together, so a
    confirm can only make a wall stricter. A reading past a cap is lifted and awards nothing: it
    never raises `MAX_TURNS` above 250 nor a ceiling above 1e5. Every place a rule stops the phase
    is a `ProtocolStop`; none of them picks a value.
    """
    walls_list, down_list = list(walls_readings), list(down_readings)
    walls = _index(walls_list, "R7")
    candidate = decide_walls(walls_list, down_list)
    confirm = _confirm_groups(confirm_readings)
    turn_labels = _derive_turns(candidate.t, confirm)
    ceilings, cost_limited = _derive_ceilings(candidate, walls, confirm)
    values = [ceiling.value for ceiling in ceilings.values()]
    shared = max(sorted(set(values)), key=values.count)  # a tie goes to the lower value
    for (kind, field), first_refused in cost_limited.items():
        if shared >= first_refused:
            raise ProtocolStop("R8", f"{kind} {field} has no confirmed decade and its first "
                                     f"refused decade is {first_refused:g} mm, and the shared "
                                     f"MAX_FIELD_MM {shared:g} is not below it (G27)")
    constants = {f"MAX_{kind.upper()}_{field.upper()}_MM": ceiling.value
                 for (kind, field), ceiling in ceilings.items() if ceiling.value != shared}
    tail = _derive_floor("R9", _tail_walk(), candidate.tail, walls, confirm, 100)
    root = _derive_floor("R10", _root_walk(), candidate.root, walls, confirm, 10)

    past: dict[str, str] = {}
    step = candidate.t + 10
    step_labels = [_turn_label(step, _stem(*cell)) for cell in _cells()]
    past["MAX_TURNS"] = f"{step} turns, {_summary(confirm, step_labels)}"
    for key, ceiling in ceilings.items():
        past[f"{key[0]} {key[1]}"] = _summary(confirm, _bearing(FIELD_STEMS[key],
                                                                ceiling.decade * 10))
    for key in cost_limited:
        past[f"{key[0]} {key[1]}"] = _summary(confirm, _bearing(FIELD_STEMS[key], CEILINGS[0]))
    for name, floor, walk in (("MIN_TAIL_MM", tail, _tail_walk()),
                              ("MIN_ROOT_RADIUS_MM", root, _root_walk())):
        values_walked = [value for value, _ in walk]
        if floor.v is not None and values_walked.index(floor.v) + 1 < len(walk):
            past[name] = _summary(confirm, walk[values_walked.index(floor.v) + 1][1])
    return Derived(candidate, candidate.t, turn_labels, ceilings, cost_limited, shared,
                   constants, tail, root, past, _differences(candidate, ceilings, cost_limited,
                                                             tail, root))


def _differences(candidate: Decision, ceilings: Mapping[tuple[str, str], Ceiling],
                 cost_limited: Mapping[tuple[str, str], float], tail: Floor,
                 root: Floor) -> tuple[str, ...]:
    """Where the final wall differs from the candidate of `decide_walls` (R3: the confirm
    decides)."""
    notes: list[str] = []
    for key, first in candidate.ceilings.items():
        final = ceilings.get(key)
        if final is None:
            notes.append(f"{key[0]} {key[1]}: candidate decade {first.decade:g} (tested "
                         f"{first.value!r}) is not confirmed (cost), so no constant of its own "
                         f"(first refused decade {cost_limited[key]:g} mm, G27)")
        elif (final.decade, final.value) != (first.decade, first.value):
            notes.append(f"{key[0]} {key[1]}: candidate decade {first.decade:g} (tested "
                         f"{first.value!r}), final decade {final.decade:g} (tested "
                         f"{final.value!r}): the confirm made it stricter")
    for name, final_floor, first_floor in (("MIN_TAIL_MM", tail, candidate.tail),
                                           ("MIN_ROOT_RADIUS_MM", root, candidate.root)):
        if final_floor.v != first_floor.v:
            notes.append(f"{name}: candidate {first_floor.v!r}, final {final_floor.v!r}")
    return tuple(notes)


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


def build_confirm(walls_dir: str, down_dir: str | None, explore_dir: str) -> _Set:
    decision = decide_walls(_read(walls_dir), _read(down_dir) if down_dir else ())
    out = _confirm_set(decision)
    sources = [f"walls={walls_dir}", *([f"walls-down={down_dir}"] if down_dir else []),
               f"explore={explore_dir}"]
    out.sharded(charge_table(_read(explore_dir)), sources)
    return out


# --- the Runs II smoke (07-06): a path check of `bench.oper_bound`, not a figure ----------------

SMOKE_RULE = "smoke, not a figure: 07-06 path check"
SMOKE_ARTIFACT = "stl-preview"
SMOKE_DRIFT_BUILDS = 3  # a small K for the path check; R23's K is 20, in the set 07-16 writes
SMOKE_PARTNERS: tuple[tuple[str, Params], ...] = (
    ("default-nut", {}), ("default-nut-left", {"left_hand": True}))


def pool_slot(kind: str, params: Params, workers: int) -> int:
    """The worker `BuildPool.executor_for` routes a part to: the hash of its validated field values
    modulo N, the same in every process (R14), so a set can name the slot before any pool runs."""
    return hash(KINDS[kind].model_validate(dict(params))) % workers


def bound_smoke() -> _Set:
    """The runner smoke of the Runs II instruments: a contention reading at N = 2 (the default
    bolt as P and the first default nut on the other slot) and at N = 1, one drift of K = 3
    and an arena reading with the trim on and off, all of the default bolt at `stl-preview`. It
    proves the path on the runner and sets nothing; its readings are not recorded as data."""
    out = _Set("bound-smoke", reps=1, shards=1, rule=SMOKE_RULE, notes=[
        "A path check of bench.oper_bound on the runner (07-06 Task 3); no figure from it is a "
        "bound or is recorded under bench/results."])
    bolt: dict[str, object] = {"label": "default-bolt", "kind": "bolt", "params": {}}
    p_slot = pool_slot("bolt", {}, 2)
    partner = next(((label, params) for label, params in SMOKE_PARTNERS
                    if pool_slot("nut", params, 2) != p_slot), None)
    if partner is None:
        raise ProtocolStop("R14", "neither default nut sits on another slot than the default "
                                  "bolt at N = 2, so no partner leaves P its own worker")
    label, params = partner
    out.copy({"label": "contention-n2", "kind": "contention", "artifact": SMOKE_ARTIFACT,
              "workers": 2, "points": [
                  {**bolt, "slot": p_slot},
                  {"label": label, "kind": "nut", "params": dict(params),
                   "slot": pool_slot("nut", params, 2)}]})
    out.copy({"label": "contention-n1", "kind": "contention", "artifact": SMOKE_ARTIFACT,
              "workers": 1, "points": [{**bolt, "slot": pool_slot("bolt", {}, 1)}]})
    part = {"kind": "bolt", "params": {}}
    out.copy({"label": f"drift-k{SMOKE_DRIFT_BUILDS}", "kind": "drift",
              "artifact": SMOKE_ARTIFACT, "part": part, "k": SMOKE_DRIFT_BUILDS,
              "deadline_s": DEADLINE_S})
    for trim in (True, False):
        out.copy({"label": f"arenas-trim-{'on' if trim else 'off'}", "kind": "arenas",
                  "artifact": SMOKE_ARTIFACT, "part": part, "trim": trim})
    return out


# --- the load smoke (07-08): a path check of `bench.oper_load`, not a figure ---------------------

LOAD_SMOKE_RULE = "smoke, not a figure: 07-08 path check"


def load_smoke() -> _Set:
    """The runner smoke of the load instruments: one load reading at N = 1, a queue of 2 and 2
    clients, `solid_cache` 4 and the JSON bodies, over the default bolt and nut at all three
    artifacts; and the default bolt's fine STL with the R19 gzip levels. It proves the path on
    the runner and sets nothing; its readings are not recorded as data."""
    out = _Set("load-smoke", reps=1, shards=1, rule=LOAD_SMOKE_RULE, notes=[
        "A path check of bench.oper_load, bench.oper_serve and the gzip levels on the runner "
        "(07-08 Task 3); no figure from it is a bound or is recorded under bench/results."])
    mix: list[dict[str, object]] = [
        {"label": f"default-{kind}", "kind": kind, "params": {}, "artifact": artifact}
        for kind in ("bolt", "nut") for artifact in ARTIFACTS]
    out.copy({"label": "load-n1", "kind": "load", "workers": 1, "queue": 2, "clients": 2,
              "solid_cache": 4, "bodies": True, "mix": mix})
    out.copy({"label": "default-bolt", "kind": "bolt", "params": {}, "artifact": "stl-fine",
              "gzip_levels": [1, 6, 9]})
    return out


# --- Runs II (07-15): D(A), the bound set, the load mix and the gzip set -------------------------
#
# R27 steps 1 to 4, R14, R15 and R19 over the admitted space: the explore points the parameter model
# takes and the shipped cost rule (`calc.cost.predict` against B-01's `BUDGET`) admits under a given
# envelope. Each file records the envelope it was drawn under and its `sources`, and `--check`
# writes it again under that recorded envelope: a widening never redraws a set (R12, G6).

RUNS2_REPS = 5  # R3: a set that sets a bound reads every point 5 times
SEED = 20261026  # R27 step 4: the date of the owner's rulings, as an integer
EDGE_POINTS = 3  # R27 step 3
TOP_SECONDS = 5  # R14: the 5 slowest admitted points
LOAD_ORDER: tuple[cost.Artifact, ...] = ("stl-fine", "step", "stl-preview")  # R15
LOAD_EDGE, LOAD_DRAW = 3, 17  # R15: 3 edge and 17 draw parts per artifact, 20 samples per p95
LOAD_SOLID_CACHE = 4  # R15: `SCREW_SOLID_CACHE` unless R22 is measuring a K
GZIP_ARTIFACTS: tuple[cost.Artifact, ...] = ("stl-preview", "stl-fine")  # R19: the STL bound set
GZIP_LEVELS = [1, 6, 9]  # R19
TIER_ORDER = "bench/results/phase-07/tier-order.json"
RUNS2_SETS = ("bound", "load", "gzip", "arenas", "outband")

type Envelope = Mapping[tuple[str, str, str], float]
type Budget = Mapping[cost.Artifact, cost.Budget]


def shipped_envelope() -> dict[tuple[str, str, str], float]:
    """`cost.ENVELOPE`, keyed by plain text as a recorded envelope is."""
    return {(kind, artifact, target): e for (kind, artifact, target), e in cost.ENVELOPE.items()}


def envelope_document(envelope: Envelope) -> dict[str, dict[str, dict[str, float]]]:
    """An envelope as a Runs II file records it: kind -> artifact -> target -> e."""
    out: dict[str, dict[str, dict[str, float]]] = {}
    for (kind, artifact, target), e in envelope.items():
        out.setdefault(kind, {}).setdefault(artifact, {})[target] = e
    return out


def envelope_of(raw: object) -> dict[tuple[str, str, str], float]:
    """The envelope a Runs II file recorded, keyed as `cost.ENVELOPE` is."""
    if not isinstance(raw, dict):
        raise TypeError("it records no envelope")
    found: dict[tuple[str, str, str], float] = {}
    for kind, artifacts in raw.items():
        if not isinstance(artifacts, dict):
            raise TypeError(f"its envelope of {kind} is not by artifact")
        for artifact, targets in artifacts.items():
            if not isinstance(targets, dict):
                raise TypeError(f"its envelope of {kind} {artifact} is not by target")
            for target, e in targets.items():
                if isinstance(e, bool) or not isinstance(e, int | float):
                    raise TypeError(f"its envelope of {kind} {artifact} {target} is not a number")
                found[str(kind), str(artifact), str(target)] = float(e)
    return found


@dataclass(frozen=True)
class Candidate:
    """An admitted explore point at one artifact: the point as the explore file lists it, and the
    part the parameter model makes of it."""

    point: Mapping[str, object]
    part: FastenerParams

    @property
    def label(self) -> str:
        return str(self.point["label"])

    @property
    def params(self) -> dict[str, object]:
        params = self.point["params"]
        assert isinstance(params, dict)
        return dict(params)


def _validated(kind: str, params: Mapping[str, object]) -> FastenerParams | None:
    """The production model's part, or None where a wall (L20) or a validator refuses it."""
    try:
        return KINDS[kind].model_validate(dict(params))
    except ValidationError:
        return None


def admits(part: FastenerParams, artifact: cost.Artifact, envelope: Envelope,
           budget: Budget) -> bool:
    """R12 with the shipped prediction (G28's bands included) under `envelope`: `cost.fits` with
    the envelope and the budget given rather than shipped, and without G30's turns refusal. Every
    set was drawn before G30, and G29's points lie below the turns floor by design, so with the
    refusal here `outband.json` would no longer regenerate from its sources (G6)."""
    return all(cost.admitted(pred, envelope[part.kind, artifact, target], component)
               for pred, target, component in zip(cost.predict(part, artifact), cost.TARGETS,
                                                  budget[artifact], strict=True))


def enveloped(part: FastenerParams, artifact: cost.Artifact,
              envelope: Envelope) -> tuple[float, float, float]:
    """`prediction x (1 + e)` per target (R12), in `cost.TARGETS` order."""
    pred = cost.predict(part, artifact)
    return (pred.bytes * (1.0 + envelope[part.kind, artifact, "bytes"]),
            pred.seconds * (1.0 + envelope[part.kind, artifact, "seconds"]),
            pred.peak * (1.0 + envelope[part.kind, artifact, "peak"]))


def edge_ratio(part: FastenerParams, artifact: cost.Artifact, envelope: Envelope,
               budget: Budget) -> float:
    """R27 step 2: the largest enveloped prediction over its budget component, over the targets
    whose component is finite for `artifact`; where none is, the enveloped build seconds, the
    slowest part the model admits."""
    values = enveloped(part, artifact, envelope)
    ratios = [value / component for value, component in zip(values, budget[artifact],
                                                              strict=True)
              if component is not None]
    return max(ratios) if ratios else values[1]


def _part_key(kind: str, params: Mapping[str, object]) -> str:
    """Two points are one part when their kind and params are equal as JSON objects (R27)."""
    return json.dumps([kind, params], sort_keys=True)


def candidates(points: Iterable[Mapping[str, object]], artifact: cost.Artifact,
               envelope: Envelope, budget: Budget) -> list[Candidate]:
    """R27 step 1: the admitted explore points at `artifact`, in file order, the first of two
    points that are one part kept."""
    out: list[Candidate] = []
    seen: set[str] = set()
    for point in points:
        if point.get("artifact") != artifact:
            continue
        kind, params = str(point["kind"]), point["params"]
        assert isinstance(params, dict)
        part = _validated(kind, params)
        key = _part_key(kind, params)
        if part is None or key in seen or not admits(part, artifact, envelope, budget):
            continue
        seen.add(key)
        out.append(Candidate(point, part))
    return out


def tier_order(points: Sequence[Mapping[str, object]], envelope: Envelope,
               budget: Budget = cost.BUDGET) -> dict[str, dict[str, object]]:
    """R27 steps 1 to 4 per artifact: the candidates in file order, the edge ranking (largest edge
    ratio first, a tie to the label that sorts first) and the draw, the other candidates in file
    order shuffled by a new `random.Random(SEED)`."""
    out: dict[str, dict[str, object]] = {}
    for artifact in cost.ARTIFACTS:
        found = candidates(points, artifact, envelope, budget)
        ratios = {c.label: edge_ratio(c.part, artifact, envelope, budget) for c in found}
        ranking = sorted(found, key=lambda c: (-ratios[c.label], c.label))
        edge = {c.label for c in ranking[:EDGE_POINTS]}
        draw = [c.label for c in found if c.label not in edge]
        random.Random(SEED).shuffle(draw)
        out[artifact] = {
            "candidates": [c.label for c in found],
            "edge_ranking": [{"label": c.label, "edge_ratio": ratios[c.label]} for c in ranking],
            "draw": draw}
    return out


def _explore_index(readings: Iterable[Reading]) -> dict[tuple[str, str], Reading]:
    found: dict[tuple[str, str], Reading] = {}
    for reading in readings:
        key = (str(reading["label"]), str(reading["artifact"]))
        if key in found:
            raise ProtocolStop("R3", f"{key[0]} at {key[1]} was read twice in explore")
        found[key] = reading
    return found


def _ok(index: Mapping[tuple[str, str], Reading], label: str, artifact: str) -> Reading | None:
    reading = index.get((label, artifact))
    return reading if reading is not None and reading.get("status") == "ok" else None


def _largest(found: Iterable[Candidate], key: Callable[[Candidate], float]) -> Candidate | None:
    """The candidate with the largest `key`, a tie to the label that sorts first."""
    return min(found, key=lambda c: (-key(c), c.label), default=None)


def bound_candidates(points: Sequence[Mapping[str, object]],
                     index: Mapping[tuple[str, str], Reading], artifact: cost.Artifact,
                     envelope: Envelope, budget: Budget = cost.BUDGET) -> list[Candidate]:
    """R14's candidates at `artifact` (G31): the admitted explore points whose explore reading is
    ok at every artifact. Two admitted nuts the kernel refuses entered the stl-preview set as P and
    as partners when only the two measured picks needed an ok reading, and every reading that built
    them was refused (bound 40907549180, gzip 40909739628), so those (P, N) had no max (R3)."""
    return [c for c in candidates(points, artifact, envelope, budget)
            if all(_ok(index, c.label, other) is not None for other in cost.ARTIFACTS)]


def bound_sets(points: Sequence[Mapping[str, object]], readings: Iterable[Reading],
               envelope: Envelope, budget: Budget = cost.BUDGET) -> dict[str, list[Candidate]]:
    """R14's bound set per artifact, from its candidates (`bound_candidates`): the 5 with the
    largest enveloped build-seconds prediction, the largest measured cold wall, the largest
    enveloped peak prediction and the largest measured `memory_peak_bytes`, a point in two groups
    once, so 5 to 8 points, in that order."""
    index = _explore_index(readings)
    out: dict[str, list[Candidate]] = {}
    for artifact in cost.ARTIFACTS:
        found = bound_candidates(points, index, artifact, envelope, budget)
        if not found:
            raise ProtocolStop("R14", f"no admitted point at {artifact} has an ok explore reading "
                                      "at every artifact, so the bound set has no point")

        def reading(c: Candidate, artifact: str = artifact) -> Reading:
            found_reading = _ok(index, c.label, artifact)
            assert found_reading is not None
            return found_reading

        def seconds(c: Candidate, artifact: cost.Artifact = artifact) -> float:
            return enveloped(c.part, artifact, envelope)[1]

        def peak(c: Candidate, artifact: cost.Artifact = artifact) -> float:
            return enveloped(c.part, artifact, envelope)[2]

        top = sorted(found, key=lambda c: (-seconds(c), c.label))[:TOP_SECONDS]
        picks = [*top,
                 _largest(found, lambda c: _number(reading(c), "build_s")
                          + _number(reading(c), "export_s")),
                 _largest(found, peak),
                 _largest(found, lambda c: _number(reading(c), "memory_peak_bytes"))]
        chosen: list[Candidate] = []
        for pick in picks:
            if pick is not None and pick.label not in {c.label for c in chosen}:
                chosen.append(pick)
        out[artifact] = chosen
    return out


def _member(c: Candidate, slot: int) -> dict[str, object]:
    return {"label": c.label, "kind": c.part.kind, "params": c.params, "slot": slot}


def bound_points(points: Sequence[Mapping[str, object]], readings: Iterable[Reading],
                 envelope: Envelope, budget: Budget = cost.BUDGET) -> list[dict[str, object]]:
    """R14's contention readings: every point P of every bound set at N 1, 2 and 3, P on its own
    slot (`hash(p) % N`, `pool_slot`) and, on every slot P does not hold, the candidate
    other than P on that slot with the largest enveloped build-seconds prediction, a tie to the
    label, both from `bound_candidates` (G31). A slot no candidate holds is a stop: no rule puts
    two points on one worker."""
    readings = list(readings)
    bound, index = bound_sets(points, readings, envelope, budget), _explore_index(readings)
    out: list[dict[str, object]] = []
    for artifact in cost.ARTIFACTS:
        found = bound_candidates(points, index, artifact, envelope, budget)
        # Slowest first, a tie to the label: the first on a slot is that slot's partner.
        slowest = sorted(found, key=lambda c: (-enveloped(c.part, artifact, envelope)[1],
                                               c.label))
        for p in bound[artifact]:
            for workers in CONTENTION_WORKERS:
                own = hash(p.part) % workers
                members = [_member(p, own)]
                for slot in range(workers):
                    if slot == own:
                        continue
                    partner = next((c for c in slowest if c.label != p.label
                                    and hash(c.part) % workers == slot), None)
                    if partner is None:
                        raise ProtocolStop("R14", f"{p.label} at {artifact}, N = {workers}: no "
                                                  f"candidate is on slot {slot}, so the "
                                                  "reading cannot run N-way")
                    members.append(_member(partner, slot))
                out.append({"label": f"{p.label}-n{workers}", "kind": "contention",
                            "artifact": artifact, "workers": workers, "points": members})
    return out


def _tier_lists(document: Mapping[str, object], artifact: str) -> tuple[list[str], list[str]]:
    """The edge ranking and the draw of `artifact` from a parsed `tier-order.json`."""
    artifacts = document.get("artifacts")
    entry = artifacts.get(artifact) if isinstance(artifacts, dict) else None
    if not isinstance(entry, dict):
        raise TypeError(f"tier-order.json has no {artifact}")
    ranking, draw = entry.get("edge_ranking"), entry.get("draw")
    if not (isinstance(ranking, list) and isinstance(draw, list)):
        raise TypeError(f"tier-order.json's {artifact} has no edge_ranking and draw lists")
    return ([str(item["label"]) for item in ranking if isinstance(item, dict)],
            [str(label) for label in draw])


def load_mix(tier: Mapping[str, object], points: Sequence[Mapping[str, object]],
             readings: Iterable[Reading]) -> list[dict[str, object]]:
    """R15's mix: the artifacts in `LOAD_ORDER`, each its first 3 unused parts of its edge ranking
    and then its first 17 unused parts of its draw whose explore reading at that artifact is ok, a
    part used once any artifact has taken it; the 60 requests in that order, shuffled once by a new
    `random.Random(SEED)`. A list that cannot supply its parts is a stop: no part is repeated."""
    index = _explore_index(readings)
    by_label = {(str(p["label"]), str(p["artifact"])): p for p in points if "artifact" in p}
    used: set[str] = set()
    mix: list[dict[str, object]] = []
    for artifact in LOAD_ORDER:
        ranking, draw = _tier_lists(tier, artifact)
        for labels, want, name in ((ranking, LOAD_EDGE, "edge ranking"),
                                   (draw, LOAD_DRAW, "draw")):
            taken = 0
            for label in labels:
                if taken == want:
                    break
                if (label, artifact) not in by_label:
                    raise ValueError(f"tier-order.json names {label} at {artifact}, which the "
                                     "explore file does not hold")
                point = by_label[label, artifact]
                kind, params = str(point["kind"]), point["params"]
                assert isinstance(params, dict)
                key = _part_key(kind, params)
                if key in used:
                    continue
                if (label, artifact) not in index:
                    raise ProtocolStop("R15", f"{label} at {artifact} has no explore reading")
                if _ok(index, label, artifact) is None:
                    continue
                used.add(key)
                mix.append({"label": label, "kind": kind, "params": dict(params),
                            "artifact": artifact})
                taken += 1
            if taken < want:
                raise ProtocolStop("R15", f"the {name} of {artifact} supplies {taken} unused parts "
                                          f"with an ok explore reading, not {want}")
    random.Random(SEED).shuffle(mix)
    return mix


def load_points(tier: Mapping[str, object], points: Sequence[Mapping[str, object]],
                readings: Iterable[Reading]) -> list[dict[str, object]]:
    """R15's load readings: N 1, 2 and 3, a queue and clients of 2N, `solid_cache` 4, the JSON
    bodies at N = 1 only, every N the one mix."""
    mix = load_mix(tier, points, readings)
    return [{"label": f"load-n{workers}", "kind": "load", "workers": workers,
             "queue": 2 * workers, "clients": 2 * workers, "solid_cache": LOAD_SOLID_CACHE,
             "bodies": workers == 1, "mix": mix} for workers in CONTENTION_WORKERS]


def gzip_points(bound: Mapping[str, Sequence[Candidate]]) -> list[dict[str, object]]:
    """R19's gzip set: every point of the `stl-preview` and `stl-fine` bound sets, as its explore
    point, read at gzip levels 1, 6 and 9."""
    return [{**c.point, "gzip_levels": list(GZIP_LEVELS)}
            for artifact in GZIP_ARTIFACTS for c in bound[artifact]]


def arena_points(bound: Mapping[str, Sequence[Candidate]],
                 readings: Iterable[Reading]) -> list[dict[str, object]]:
    """R23's arena readings (G17): per artifact, Z(A), the point of A's bound set with the largest
    `memory_peak_bytes` among its ok explore readings (a tie to the label that sorts first, R14's
    measured memory extremum), with the trim on and with it off."""
    index = _explore_index(readings)
    out: list[dict[str, object]] = []
    for artifact in cost.ARTIFACTS:
        measured = [c for c in bound[artifact] if _ok(index, c.label, artifact) is not None]

        def peak(c: Candidate, artifact: str = artifact) -> float:
            reading = _ok(index, c.label, artifact)
            assert reading is not None
            return _number(reading, "memory_peak_bytes")

        z = _largest(measured, peak)
        if z is None:
            raise ProtocolStop("R23", f"no point of the {artifact} bound set has an ok explore "
                                      "reading, so Z(A) has no part")
        for trim in (True, False):
            out.append({"label": f"arenas-{z.label}-trim-{'on' if trim else 'off'}",
                        "kind": "arenas", "artifact": artifact,
                        "part": {"kind": z.part.kind, "params": z.params}, "trim": trim})
    return out


# --- the out-of-band points (R11, G28 and G29) ---------------------------------------------------

FAR_FACTOR = Decimal(10)  # G28's follow-up: one point far above the band, at 10 x its high edge


@dataclass(frozen=True)
class Outband:
    """One out-of-band part: its label, its fields and the part the parameter model makes."""

    label: str
    params: dict[str, object]
    part: FastenerParams


def _form_step(kind: str, field: str) -> Decimal:
    """The form step the schema publishes for `field` (0.1 mm for s, k and m, 0.5 mm for
    thread_length), read from the model, not typed."""
    extra = KINDS[kind].model_fields[field].json_schema_extra
    assert isinstance(extra, dict)
    step = extra["step"]
    assert isinstance(step, float)
    return Decimal(repr(step))


def _on_step(n: int, step: Decimal) -> float:
    return float(n * step)


def _largest_below(bound: float, d: float, step: Decimal) -> float | None:
    """The largest positive value on `step` whose ratio to `d`, as `cost` divides it, is strictly
    below `bound`, or None when no positive value is."""
    n = int((Decimal(repr(bound)) * Decimal(repr(d)) / step).to_integral_value(ROUND_CEILING))
    while n > 0 and _on_step(n, step) / d >= bound:
        n -= 1
    while _on_step(n + 1, step) / d < bound:
        n += 1
    return _on_step(n, step) if n > 0 else None


def _smallest_above(bound: float, d: float, step: Decimal) -> float:
    """The smallest value on `step` whose ratio to `d` is strictly above `bound`."""
    n = int((Decimal(repr(bound)) * Decimal(repr(d)) / step).to_integral_value(ROUND_FLOOR))
    while _on_step(n, step) / d <= bound:
        n += 1
    while n > 1 and _on_step(n - 1, step) / d > bound:
        n -= 1
    return _on_step(n, step)


def _catalogue_rows(kind: str) -> list[tuple[str, dict[str, object]]]:
    """(row id, expanded fields) of the bolt (294) or nut (14) catalogue, in file order."""
    if kind == "bolt":
        return [(row.id, dict(expand(row.id) or {})) for row in catalogue()]
    return [(row.id, dict(expand_nut(row.id) or {})) for row in nut_catalogue()]


def _admitted_rows(kind: str, label: Callable[[str], str],
                   value: Callable[[FastenerParams], tuple[str, float] | None],
                   artifact: cost.Artifact, envelope: Envelope, budget: Budget) -> list[Outband]:
    """The catalogue rows of `kind` with one field set by `value` (None skips the row) that the
    walls and the rule admit at `artifact`, in file order."""
    found: list[Outband] = []
    for row_id, fields in _catalogue_rows(kind):
        base = _validated(kind, fields)
        assert base is not None, row_id
        moved = value(base)
        if moved is None:
            continue
        params = {**fields, moved[0]: moved[1]}
        part = _validated(kind, params)
        if part is not None and admits(part, artifact, envelope, budget):
            found.append(Outband(label(row_id), params, part))
    return found


def _nearest_and_first(found: Sequence[Outband], artifact: cost.Artifact, envelope: Envelope,
                       budget: Budget) -> list[Outband]:
    """The row nearest the budget (the largest edge ratio, as R27 ranks, a tie to the label that
    sorts first) and the first in file order; one point when they coincide."""
    nearest = min(found, key=lambda o: (-edge_ratio(o.part, artifact, envelope, budget), o.label))
    return [nearest] if nearest.label == found[0].label else [nearest, found[0]]


def _outband_point(o: Outband, artifact: str) -> dict[str, object]:
    return {"label": o.label, "kind": o.part.kind, "params": o.params, "artifact": artifact}


def _outband_label(kind: str, field: str, side: str, row: str) -> str:
    return f"outband-{kind}-{field}-{side}-{row}"


def _side_value(side: str, field: str, band: tuple[float, float], step: Decimal,
                p: FastenerParams) -> tuple[str, float] | None:
    """`field` of `p` moved out of its band: to the first value on `step` strictly below the low
    edge x d, strictly above the high edge x d, or at or above 10 x the high edge x d (far)."""
    low, high = band
    if side == "below":
        value = _largest_below(low, p.d, step)
        return None if value is None else (field, value)
    if side == "above":
        return field, _smallest_above(high, p.d, step)
    far = FAR_FACTOR * Decimal(repr(high)) * Decimal(repr(p.d)) / step
    return field, _on_step(int(far.to_integral_value(ROUND_CEILING)), step)


def head_ratio_points(envelope: Envelope, budget: Budget = cost.BUDGET
                      ) -> tuple[list[dict[str, object]], list[str]]:
    """G28's out-of-band points and the far points that do not exist. Per head ratio of
    `cost.BANDS`, artifact and side, the catalogue rows whose ratio field, set to the first value
    on its form step strictly below the band's low edge x d (above: strictly above its high edge
    x d), the walls and the rule admit: the one nearest the budget and the first in file order.
    One far point above, the first row admitted with the field at 10 x the high edge x d on its
    step, where one is. A side no row supplies is a stop (R11)."""
    points: list[dict[str, object]] = []
    absent: list[str] = []
    for (kind, field), (low, high) in cost.BANDS.items():
        step = _form_step(kind, field)
        for artifact in cost.ARTIFACTS:
            for side in ("below", "above", "far"):
                found = _admitted_rows(
                    kind, functools.partial(_outband_label, kind, field, side),
                    functools.partial(_side_value, side, field, (low, high), step), artifact,
                    envelope, budget)
                if not found and side == "far":
                    absent.append(f"{kind} {field}/d far above its band at {artifact}")
                    continue
                if not found:
                    raise ProtocolStop("R11", f"no {kind} catalogue row with {field}/d {side} its "
                                              f"band is admitted at {artifact} (G28)")
                chosen = found[:1] if side == "far" else _nearest_and_first(
                    found, artifact, envelope, budget)
                points += [_outband_point(o, artifact) for o in chosen]
    return points, absent


def _below_turns(p: FastenerParams, step: Decimal) -> tuple[str, float] | None:
    """G29: `thread_length` at the largest positive value on its form step whose built thread
    has fewer turns than `cost.MIN_FITTED_TURNS`, as `cost` computes the turns."""
    assert isinstance(p, BoltParams)

    def turns(n: int) -> float:
        return built_thread_length(_on_step(n, step), p.length) / p.pitch

    n = int((Decimal(repr(cost.MIN_FITTED_TURNS)) * Decimal(repr(p.pitch)) / step)
            .to_integral_value(ROUND_CEILING))
    while n > 0 and turns(n) >= cost.MIN_FITTED_TURNS:
        n -= 1
    while turns(n + 1) < cost.MIN_FITTED_TURNS:
        n += 1
    return ("thread_length", _on_step(n, step)) if n > 0 else None


def turns_points(envelope: Envelope, budget: Budget = cost.BUDGET) -> list[dict[str, object]]:
    """G29's points: per artifact the bolt catalogue rows with `thread_length` below the fewest
    fitted turns (`_below_turns`) that the walls and the rule admit, the one nearest the budget
    and the first in file order. An artifact with none is a stop (R11)."""
    step = _form_step("bolt", "thread_length")
    points: list[dict[str, object]] = []
    for artifact in cost.ARTIFACTS:
        found = _admitted_rows("bolt", "turns-below-{}".format,
                               functools.partial(_below_turns, step=step), artifact, envelope,
                               budget)
        if not found:
            raise ProtocolStop("R11", f"no bolt catalogue row below {cost.MIN_FITTED_TURNS!r} "
                                      f"built turns is admitted at {artifact} (G29)")
        points += [_outband_point(o, artifact)
                   for o in _nearest_and_first(found, artifact, envelope, budget)]
    return points


def _runs2_set(name: str, rule: str, notes: list[str], points: Iterable[Mapping[str, object]],
               envelope: Envelope, sources: list[str]) -> _Set:
    """A Runs II set at 5 repetitions, each reading charged R2's 600 s deadline (R6, G4, G24)."""
    out = _Set(name, reps=RUNS2_REPS, shards=1, rule=rule, notes=notes)
    for point in points:
        out.copy(point)
    out.shard_sizes = shard_sizes([float(DEADLINE_S)] * len(out.points), HALF_JOB_S)
    out.shards, out.sources, out.envelope = len(out.shard_sizes), sources, envelope_document(
        envelope)
    return out


def _explore_points() -> list[dict[str, object]]:
    return explore().points


EXPLORE_POINTS = "bench/points/explore.json"


def tier_order_text(envelope: Envelope) -> str:
    """`tier-order.json`: D(A) steps 1 to 4 per artifact under `envelope`. Steps 1 to 4 read the
    explore file and the prediction only, no reading and no timeout (R27), so the file's one
    source is the explore point file."""
    document = {
        "rule": "07-SWEEP-PROTOCOL.md R27 steps 1 to 4 (G6)", "seed": SEED,
        "budget": "B-01 (C1), calc.cost.BUDGET", "sources": [f"explore-points={EXPLORE_POINTS}"],
        "envelope": envelope_document(envelope),
        "artifacts": tier_order(_explore_points(), envelope)}
    return json.dumps(document, indent=1) + "\n"


def build_bound(explore_dir: str, envelope: Envelope) -> _Set:
    return _runs2_set("bound", "07-SWEEP-PROTOCOL.md R14 (G4, G6, G24, G31)", [
        "the candidates of an artifact: its admitted explore points whose explore reading is ok "
        "at every artifact (G31)",
        "per artifact the bound set: the 5 candidates with the largest enveloped build-seconds "
        "prediction, the largest measured cold wall, the largest measured memory_peak_bytes and "
        "the largest enveloped peak prediction, a tie to the label that sorts first, a point in "
        "two groups once",
        "each bound point P at N 1, 2 and 3: P on slot hash(p) % N and, on every other slot, the "
        "candidate other than P on that slot with the largest enveloped build-seconds "
        "prediction, a tie to the label",
        "5 repetitions; each reading charged R2's 600 s (R6, G4)"],
        bound_points(_explore_points(), _read(explore_dir), envelope), envelope,
        [f"explore={explore_dir}"])


def build_load(tier_path: str, explore_dir: str) -> _Set:
    tier = json.loads((REPO_ROOT / tier_path).read_text())
    return _runs2_set("load", "07-SWEEP-PROTOCOL.md R15 (G4, G6, G7)", [
        "N 1, 2 and 3, queue and clients 2N, solid_cache 4, the JSON bodies at N = 1 only",
        "one mix of 60 cold requests: stl-fine, step, then stl-preview, each its first 3 unused "
        "parts of its edge ranking and its first 17 unused parts of its draw (tier-order.json) "
        "with an ok explore reading, no part twice, shuffled once by random.Random(20261026)",
        "5 repetitions; each reading charged R2's 600 s (R6, G4)"],
        load_points(tier, _explore_points(), _read(explore_dir)), envelope_of(tier["envelope"]),
        [f"tier-order={tier_path}", f"explore={explore_dir}"])


def build_gzip(explore_dir: str, envelope: Envelope) -> _Set:
    bound = bound_sets(_explore_points(), _read(explore_dir), envelope)
    return _runs2_set("gzip", "07-SWEEP-PROTOCOL.md R19 (G11, G15, G24, G31)", [
        "every point of the stl-preview and stl-fine bound sets (R14, G31), read as a part with "
        "gzip levels 1, 6 and 9",
        "5 repetitions; each reading charged R2's 600 s (R6, G24)"],
        gzip_points(bound), envelope, [f"explore={explore_dir}"])


def build_arenas(explore_dir: str, envelope: Envelope) -> _Set:
    bound = bound_sets(_explore_points(), _read(explore_dir), envelope)
    return _runs2_set("arenas", "07-SWEEP-PROTOCOL.md R23 (G17, G22, G24)", [
        "per artifact Z(A), the bound-set point (R14) with the largest memory_peak_bytes among "
        "its ok explore readings, a tie to the label that sorts first, read with the trim on and "
        "with it off",
        "the measure is the cgroup's memory.current, read right after the export returns, before "
        "the level-1 gzip; the peak is read last (R2)",
        "5 repetitions; each reading charged R2's 600 s (R6, G24)"],
        arena_points(bound, _read(explore_dir)), envelope, [f"explore={explore_dir}"])


RERUN_SETS = ("bound-rerun", "gzip-rerun")
_RERUN_RULES = {"bound-rerun": "07-SWEEP-PROTOCOL.md R14 (G4, G24, G31)",
                "gzip-rerun": "07-SWEEP-PROTOCOL.md R19 (G24, G31)"}
# The fields a record copies from its point: a gzip point's `preset` is not among them.
_IDENTITY = ("label", "kind", "artifact", "params", "workers", "points", "gzip_levels")


def unread(points: Iterable[Mapping[str, object]],
           recorded: Iterable[Reading]) -> list[dict[str, object]]:
    """The points no recorded reading is of: a reading is of a point when every identity field
    the point carries is equal in the reading. A contention point keeps its label when a partner
    changes, so its members decide, not its label (G31)."""
    readings = list(recorded)

    def read(point: Mapping[str, object]) -> bool:
        keys = [key for key in _IDENTITY if key in point]
        return any(all(reading.get(key) == point[key] for key in keys) for reading in readings)

    return [dict(point) for point in points if not read(point)]


def build_rerun(name: str, explore_dir: str, run_dir: str, envelope: Envelope) -> _Set:
    """`bound-rerun.json` or `gzip-rerun.json` (G31): the points of the bound or gzip set, drawn
    under `envelope`, that no reading of the earlier run `run_dir` is of. A rerun with no point is
    not written: the earlier run read the whole set."""
    whole = (build_bound if name == "bound-rerun" else build_gzip)(explore_dir, envelope)
    points = unread(whole.points, _read(run_dir))
    if not points:
        raise ValueError(f"run {run_dir} read every point of the {whole.name} set")
    return _runs2_set(name, _RERUN_RULES[name], [
        f"the points of the {whole.name} set (its notes and envelope) that no reading of {run_dir} "
        "is of, every identity field the point carries equal in the reading; the earlier "
        "readings of the points they replace decide nothing (R14, G31)",
        "5 repetitions; each reading charged R2's 600 s (R6, G4, G24)"],
        points, envelope, [f"explore={explore_dir}", f"run={run_dir}"])


def build_outband(explore_dir: str, envelope: Envelope) -> _Set:
    """`outband.json`: G28's and G29's points at 5 repetitions, each charged as R6 charges an
    explore-like part, the largest explore `wall_s` of its (kind, artifact) group (G4)."""
    head, absent = head_ratio_points(envelope)
    out = _Set("outband", reps=RUNS2_REPS, shards=1, rule="07-SWEEP-PROTOCOL.md R11 (G28, G29)",
               notes=[
                   "G28: per head ratio of cost.BANDS (bolt k/d and s/d, nut s/d and m/d), "
                   "artifact and side, catalogue rows with the ratio field at the first value on "
                   "its 0.1 mm form step strictly below the band's low edge x d (outband-*-below-*)"
                   " or strictly above its high edge x d (outband-*-above-*) that the walls and "
                   "the shipped rule admit: the one with the largest enveloped edge ratio (R27's "
                   "rank, a tie to the label) and the first in file order, one point when they "
                   "coincide",
                   "G28: far above (outband-*-far-*), the first row admitted with the field at the "
                   "first value on its step at or above 10 x the high edge x d; none for "
                   + ("; ".join(absent) if absent else "no ratio"),
                   "G29 (turns-below-*): per artifact bolt catalogue rows with thread_length at "
                   "the largest value on its 0.5 mm form step whose built thread has fewer turns "
                   "than cost.MIN_FITTED_TURNS, admitted by the walls and the rule: the nearest "
                   "the budget and the first in file order",
                   "a reading above its enveloped prediction stops the phase for the owner and "
                   "widens no e (R11); 5 repetitions; each point charged the largest explore "
                   "wall_s of its (kind, artifact) group (R6, G4)"])
    for point in [*head, *turns_points(envelope)]:
        out.copy(point)
    out.sharded(charge_table(_read(explore_dir)), [f"explore={explore_dir}"])
    out.envelope = envelope_document(envelope)
    return out


# --- the load table (07-15 Task 2) ----------------------------------------------------------------

LOAD_COLUMNS = ("point", "N", "rep", "status", "p95 all s", *(f"p95 {a} s" for a in LOAD_ORDER),
                "idle peak bytes", "end peak bytes", "time to healthy s", "health p95 s")


def _p95_cell(spread: object) -> str:
    """A p95 as the record holds it, or the sample count when there were fewer than 20 (the
    record's p95 is then null, R15)."""
    if not isinstance(spread, dict):
        return "no samples"
    value = spread.get("p95_s")
    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"{value:.3f}"
    return f"fewer than 20 samples ({spread.get('samples')})"


def load_table(readings: Iterable[Reading]) -> str:
    """Per load point (N) and repetition: the status, the p95 over all 60 requests and per
    artifact over its 20, the idle and end peaks, the time to healthy and the health p95. A
    reading that is not ok prints its status and no figure (L02); a point whose repetitions are
    not 1 to 5 each once is `incomplete` and prints no figure either (R3)."""
    groups: dict[str, list[Reading]] = {}
    for reading in readings:
        if reading.get("kind") == "load":
            groups.setdefault(str(reading["label"]), []).append(reading)
    lines = ["| " + " | ".join(LOAD_COLUMNS) + " |", "|" + " --- |" * len(LOAD_COLUMNS)]
    for label, group in groups.items():
        reps = [r.get("rep") for r in group]
        complete = sorted(map(str, reps)) == [str(n) for n in range(1, RUNS2_REPS + 1)]
        for reading in sorted(group, key=lambda r: str(r.get("rep"))):
            head = [label, str(reading.get("workers")), str(reading.get("rep"))]
            status = str(reading["status"])
            if not complete or status != "ok":
                shown = status if complete else f"incomplete (reps {sorted(map(str, reps))})"
                lines.append("| " + " | ".join([*head, shown, *[""] * (len(LOAD_COLUMNS) - 4)])
                             + " |")
                continue
            latency = reading.get("latency")
            assert isinstance(latency, dict)
            cells = [*head, status, _p95_cell(latency.get("all")),
                     *(_p95_cell(latency.get(a)) for a in LOAD_ORDER),
                     str(reading.get("idle_peak_bytes")), str(reading.get("memory_peak_bytes")),
                     f"{_number(reading, 'time_to_healthy_s'):.3f}",
                     _p95_cell(reading.get("health_latency"))]
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# --- the envelope check (07-15 Task 3; R12, G5, G21, G28) -----------------------------------------

# R12, G5, G21: the cold isolated readings, which alone widen e. G28 and G29: an `outband` reading
# never does, it stops the phase instead; a load request wall and a contended wall never do.
NEVER_WIDENS = frozenset({"load"})
# G30: of R11's out-of-band points only a nut reading widens e. The bolt's never does: the one bolt
# over its envelope, G29's 2.5-turn M2, is refused since, and widening the bolt stl-fine bytes e
# from it would refuse 6 catalogue rows B-01 keeps (C1 sets each budget at the largest row).
OUTBAND_WIDENS = frozenset({"nut"})


def widens(set_name: str, reading: Reading) -> bool:
    """Whether a reading of the set `set_name` may widen e (R12, G5, G21, G30): never a load
    reading, an out-of-band one only of a nut, every other the cold isolated rule decides."""
    if set_name in NEVER_WIDENS:
        return False
    if set_name == "outband":
        return reading.get("kind") in OUTBAND_WIDENS
    return True


@dataclass(frozen=True)
class Widening:
    """One (kind, artifact, target): its e, the largest actual / (prediction x (1 + e)) over the
    readings that may widen it, the reading that set it, and the widened e when that exceeds 1."""

    kind: str
    artifact: str
    target: str
    e: float
    ratio: float
    worst: str
    widened: float | None


def _cold_isolated(reading: Reading) -> tuple[Mapping[str, object], float, float, float] | None:
    """The part and the (bytes, seconds, peak) actuals of a reading R12 lets widen e, or None:
    a part reading (a gzip reading included), an arena reading, a contention reading at N = 1
    (P alone, its own build and export) and build 1 of a drift reading. A contention reading at
    N = 2 or 3 and drift builds 2 to K never widen e (G5)."""
    if reading.get("status") != "ok" or reading.get("lift") is not None:
        return None
    kind = reading.get("kind")
    if kind in ("bolt", "nut"):
        part: object = {"kind": kind, "params": reading.get("params")}
        peak = _number(reading, "memory_peak_bytes")
    elif kind == "contention" and reading.get("workers") == 1:
        members = reading.get("points")
        assert isinstance(members, list)
        part, peak = members[0], _number(reading, "memory_peak_bytes")
    elif kind == "arenas":
        part, peak = reading.get("part"), _number(reading, "memory_peak_bytes")
    elif kind == "drift":
        peaks = reading.get("peaks")
        assert isinstance(peaks, list)
        part, peak = reading.get("part"), float(peaks[0])
    else:
        return None
    assert isinstance(part, dict)
    seconds = _number(reading, "build_s") + _number(reading, "export_s")
    return part, _number(reading, "bytes"), seconds, peak


def envelope_check(fit_document: Mapping[str, object],
                   readings: Iterable[tuple[str, Reading]]) -> list[Widening]:
    """R12 against later readings: per (kind, artifact, target) of fit.json, the largest actual /
    (prediction x (1 + e)) over the given readings R12 lets widen e, `cost.predict` (G28's bands
    included) as the prediction, and the widened e where that exceeds 1: the factor 1 + e raised
    to cover every such actual, by whole ulps as the fit's envelope is (07-09), so admission in
    floats covers it too. A widening never lowers an e; a model with no new reading keeps its e.
    `readings` are (run id, reading)."""
    models = fit_document["models"]
    assert isinstance(models, list)
    samples: dict[tuple[str, str, str], list[tuple[float, float, str]]] = {}
    for run, reading in readings:
        found = _cold_isolated(reading)
        if found is None:
            continue
        part_raw, *actuals = found
        params = part_raw.get("params")
        assert isinstance(params, dict)
        part = KINDS[str(part_raw["kind"])].model_validate(params)
        artifact = next(a for a in cost.ARTIFACTS if a == reading.get("artifact"))
        where = f"{run}:{reading.get('label')} rep {reading.get('rep')}"
        for target, pred, actual in zip(cost.TARGETS, cost.predict(part, artifact), actuals,
                                        strict=True):
            samples.setdefault((part.kind, artifact, target), []).append((pred, actual, where))
    out: list[Widening] = []
    for model in models:
        assert isinstance(model, dict)
        key = (str(model["kind"]), str(model["artifact"]), str(model["target"]))
        e = float(model["envelope"])
        found_samples = samples.get(key, [])
        if not found_samples:
            out.append(Widening(*key, e, 0.0, "", None))
            continue
        pred, actual, worst = max(found_samples, key=lambda x: x[1] / (x[0] * (1.0 + e)))
        ratio = actual / (pred * (1.0 + e))
        widened = None
        if ratio > 1.0:
            factor = max(1.0 + e, max(a / q for q, a, _ in found_samples))
            while any(q * (1.0 + (factor - 1.0)) < a for q, a, _ in found_samples):
                factor = math.nextafter(factor, math.inf)
            widened = factor - 1.0
        out.append(Widening(*key, e, ratio, worst, widened))
    return out


def _set_of(path: Path) -> str:
    """The set a measure job's record file holds: `oper-<set>-<shard>-<rep>.jsonl`."""
    stem = path.name.removeprefix("oper-").removesuffix(".jsonl")
    return stem.rsplit("-", 2)[0]


def read_runs(directories: Iterable[Path]) -> tuple[list[Reading], list[tuple[str, str, Reading]]]:
    """The runner headers, and (set, run id, reading) of every downloaded record, under
    `directories`; a file whose header does not name exactly one run is refused."""
    heads: list[Reading] = []
    out: list[tuple[str, str, Reading]] = []
    for directory in directories:
        files = sorted(directory.glob("*/*.jsonl"))
        if not files:
            raise ValueError(f"no *.jsonl records under {directory}")
        for path in files:
            headers, found = _read_records([str(path)])
            runs = {str(h.get("GITHUB_RUN_ID")) for h in headers}
            if len(runs) != 1:
                raise ValueError(f"{path}: headers name {sorted(runs)}, not one run")
            run = runs.pop()
            heads += headers
            out += [(_set_of(path), run, reading) for reading in found]
    return heads, out


def runs_readings(directories: Iterable[Path]) -> list[tuple[str, str, Reading]]:
    """(set, run id, reading) of every downloaded record under `directories`."""
    return read_runs(directories)[1]


def _admits_all(envelope: Envelope) -> list[str]:
    """What a widened envelope would refuse that B-01 was ruled to keep: a catalogue row (C1 keeps
    all 294 and 14 at every artifact) or the all-default bolt or nut (OPER-03's empty edge)."""
    parts = [*((row_id, KINDS["bolt"].model_validate(fields))
               for row_id, fields in _catalogue_rows("bolt")),
             *((row_id, KINDS["nut"].model_validate(fields))
               for row_id, fields in _catalogue_rows("nut")),
             ("default-bolt", KINDS["bolt"]()), ("default-nut", KINDS["nut"]())]
    return [f"{label} at {artifact}" for label, part in parts for artifact in cost.ARTIFACTS
            if not admits(part, artifact, envelope, cost.BUDGET)]


def _envelope_check_command(args: argparse.Namespace) -> None:
    """Print the check over the readings R12 lets widen e and, where an e widens, write fit.json
    with only the `envelope` of each widened model and a `widened_by` list changed (R12: the form
    is not re-fitted). A widening that would refuse a part B-01 keeps is a stop, written nowhere."""
    fit_path = Path(args.fit)
    document = json.loads(fit_path.read_text())
    tagged = runs_readings([Path(d) for d in args.source])
    kept = [(run, reading) for name, run, reading in tagged if widens(name, reading)]
    rows = envelope_check(document, kept)
    print("kind | artifact | target | e | largest actual / enveloped prediction | reading | "
          "widened e")
    for row in rows:
        print(f"{row.kind} | {row.artifact} | {row.target} | {row.e!r} | {row.ratio!r} | "
              f"{row.worst or 'none'} | {'' if row.widened is None else repr(row.widened)}")
    widened = [row for row in rows if row.widened is not None]
    if not widened:
        print("no reading exceeds its envelope")
        return
    envelope = shipped_envelope() | {(r.kind, r.artifact, r.target): r.widened
                                     for r in widened if r.widened is not None}
    refused = _admits_all(envelope)
    if refused:
        raise ProtocolStop("R12", f"the widened envelope refuses {len(refused)} parts B-01 keeps, "
                                  f"the first {refused[0]}: a widening may not change B-01's set")
    runs = sorted({row.worst.split(":", 1)[0] for row in widened})
    for model in document["models"]:
        key = (model["kind"], model["artifact"], model["target"])
        for row in widened:
            if (row.kind, row.artifact, row.target) == key:
                model["envelope"] = row.widened
    document["widened_by"] = sorted({*document.get("widened_by", []), *runs})
    fit_path.write_text(json.dumps(document, sort_keys=True, indent=1, allow_nan=False) + "\n")
    print(f"widened {len(widened)} envelopes by runs {', '.join(runs)}; wrote {fit_path}")


# --- the runtime values (07-16; R14 to R26) -------------------------------------------------------
#
# Every value the server and the image ship is derived here from committed runner records, in the
# order the rules' inputs exist (07-16 audit #4): R19's gzip level, R21's export cache, R26's tmpfs
# per N, R16's W, B, mem_limit(N), qualification and pick, R14's timeouts at the picked N, then R17,
# R18, R20, R24 and R25. The bound sets, the load mix and the gzip set are the committed point
# files, never drawn again (G6). Each value carries the run ids and the readings it rests on,
# and every "the phase stops and asks the owner" is a `ProtocolStop`: nothing is written past one.

RUNTIME = "bench/results/phase-07/runtime.json"
MIB = 2**20
LIMIT_STEP_BYTES = 256 * MIB  # R16, R26: the rounding step, fixed before the data
HOST_BYTES = 16 * 10**9  # D-02: mem_limit stays under this and under the smallest MemTotal (R16)
TIMEOUT_FACTOR = 2  # D-09: a timeout is ceil(2 x its bound point's max cold wall) (R14)
GZIP_KEEP = Fraction(9, 10)  # R19: a higher level keeps at most 90 % of the adopted level's bytes
GZIP_SLOWDOWN = Fraction(3, 2)  # R19: and takes at most 1.5x its seconds
HEALTH_PROBE_S = 1.0  # R24: the HEALTHCHECK's `urlopen(..., timeout=1)` (Dockerfile)
HEALTH_SAMPLES = 20  # R15: the floor of samples behind a reported p95
START_PERIOD_STEP_S = 10  # R25: --start-period is rounded up to 10 s
DOCKER_INTERVAL_S, DOCKER_RETRIES = 30, 3  # R25: Docker's documented defaults, cited as such
BOUND_SETS, GZIP_SETS, LOAD_SETS = ("bound", "bound-rerun"), ("gzip", "gzip-rerun"), ("load",)
# A load reading copies its point's settings, but its `bodies` is the measured list, not the flag.
_LOAD_IDENTITY = ("label", "kind", "workers", "queue", "clients", "solid_cache")
_REPS = [str(n) for n in range(1, RUNS2_REPS + 1)]

type Tagged = tuple[str, str, Reading]


@dataclass(frozen=True)
class Read:
    """A committed point and every reading of it, all from one run."""

    point: Mapping[str, object]
    run: str
    readings: tuple[Reading, ...]

    @property
    def what(self) -> str:
        return f"{self.point['label']} at {self.point.get('artifact', 'load')}"

    @property
    def workers(self) -> int:
        workers = self.point["workers"]
        assert isinstance(workers, int)
        return workers

    @property
    def ok(self) -> bool:
        """Repetitions 1 to 5 each once, every one `ok` (R3)."""
        return (sorted(str(r.get("rep")) for r in self.readings) == _REPS
                and all(r.get("status") == "ok" for r in self.readings))


def _where(run: str, reading: Reading) -> str:
    return f"{run}:{reading.get('label')} rep {reading.get('rep')}"


def _round_up(value: float, step: int) -> int:
    """`value` rounded up to a whole number of `step`, exactly: 1 GiB + 1 B is 1.25 GiB."""
    return math.ceil(Fraction(value) / step) * step


def matched(points: Iterable[Mapping[str, object]], tagged: Iterable[Tagged],
            sets: Sequence[str], keys: Sequence[str], rule: str) -> list[Read]:
    """Each point with its readings in `sets`: a reading is of a point when every identity field
    in `keys` that the point carries is equal in it. A contention point keeps its label when a
    partner changes, so its members decide, never its label (G31). A point read in no run or in
    two is a stop: its repetitions must come from exactly one run."""
    pool = [(run, reading) for name, run, reading in tagged if name in sets]
    out: list[Read] = []
    for point in points:
        fields = [key for key in keys if key in point]
        found = [(run, r) for run, r in pool if all(r.get(key) == point[key] for key in fields)]
        runs = sorted({run for run, _ in found})
        read = Read(point, runs[0] if runs else "", tuple(r for _, r in found))
        if len(runs) != 1:
            raise ProtocolStop(rule, f"{read.what} is read in {len(runs)} runs "
                                     f"({', '.join(runs) or 'none'}), not in exactly one (R3)")
        out.append(read)
    return out


def _five_ok(read: Read, rule: str) -> list[Reading]:
    """The 5 repetitions of `read`, or a stop: a point with a repetition that is not `ok`, or
    without repetitions 1 to 5 each once, has no max (R3)."""
    if not read.ok:
        reps = sorted(str(r.get("rep")) for r in read.readings)
        statuses = sorted({str(r.get("status")) for r in read.readings})
        raise ProtocolStop(rule, f"{read.what} has no max: run {read.run}, repetitions {reps}, "
                                 f"statuses {statuses} (R3)")
    return sorted(read.readings, key=lambda r: str(r.get("rep")))


def _cold_wall(reading: Reading) -> float:
    return _number(reading, "build_s") + _number(reading, "export_s")


def _gzip_bytes_seconds(reading: Reading, level: int) -> tuple[int, float]:
    entries = reading.get("gzip")
    found = [e for e in entries if isinstance(e, dict) and e.get("level") == level] if isinstance(
        entries, list) else []
    if len(found) != 1:
        raise ProtocolStop("R19", f"the reading of {reading.get('label')} rep {reading.get('rep')} "
                                  f"has no one gzip entry at level {level}")
    return int(_number(found[0], "bytes")), _number(found[0], "seconds")


def gzip_level(reads: Sequence[Read]) -> dict[str, object]:
    """R19 (G11, G15, G22): per gzip point and level, the max bytes and the max seconds over its 5
    repetitions. Level 1 is the start, level 6 is tried, then level 9 against the level adopted
    by then; a level is adopted only if, at every point on its own, its bytes are at most 90 % of
    the adopted level's and its seconds at most 1.5x. A point with no max is a stop."""
    maxima: dict[str, dict[int, tuple[int, float]]] = {}
    for read in reads:
        rows = _five_ok(read, "R19")
        levels: dict[int, tuple[int, float]] = {}
        for level in GZIP_LEVELS:
            pairs = [_gzip_bytes_seconds(r, level) for r in rows]
            levels[level] = (max(b for b, _ in pairs), max(s for _, s in pairs))
        maxima[read.what] = levels
    adopted, trials = GZIP_LEVELS[0], []
    for level in GZIP_LEVELS[1:]:
        ratios = {what: (m[level][0] / m[adopted][0], m[level][1] / m[adopted][1])
                  for what, m in maxima.items()}
        failing = [what for what, m in maxima.items()
                   if not (m[level][0] <= GZIP_KEEP * m[adopted][0]
                           and Fraction(m[level][1]) <= GZIP_SLOWDOWN * Fraction(m[adopted][1]))]
        trials.append({"level": level, "against": adopted, "adopted": not failing,
                       "failing": failing,
                       "bytes_and_seconds_ratios": {w: list(r) for w, r in ratios.items()}})
        if not failing:
            adopted = level
    return {"level": adopted, "runs": sorted({read.run for read in reads}), "trials": trials,
            "maxima": {what: {str(level): {"bytes": b, "seconds": s}
                              for level, (b, s) in m.items()} for what, m in maxima.items()}}


def export_cache(explore: Iterable[Tagged], gzip_reads: Sequence[Read]) -> dict[str, object]:
    """R21 (G16): the whole MiB that holds both encodings of all three artifacts of the candidate
    with the largest raw plus level-1 gzip bytes over its three explore readings. The candidates
    are the explore parts admitted (`cost.fits`) and read `ok` at all 3 artifacts. The level-1
    bytes bound every level only while no R19 reading shows level 6 or 9 above level 1: a stop."""
    for read in gzip_reads:
        for reading in read.readings:
            if reading.get("status") != "ok":
                continue
            first, _ = _gzip_bytes_seconds(reading, GZIP_LEVELS[0])
            for level in GZIP_LEVELS[1:]:
                if _gzip_bytes_seconds(reading, level)[0] > first:
                    raise ProtocolStop("R21", f"{_where(read.run, reading)} reads more bytes at "
                                              f"gzip level {level} than at level 1 (G16)")
    tagged = list(explore)
    runs = sorted({run for _, run, _ in tagged})
    by_label: dict[str, dict[str, Reading]] = {}
    for (label, artifact), reading in _explore_index(r for _, _, r in tagged).items():
        by_label.setdefault(label, {})[artifact] = reading
    best: tuple[int, str] | None = None
    candidates_seen = 0
    for label, found in sorted(by_label.items()):
        if set(found) != set(cost.ARTIFACTS) or any(r.get("status") != "ok"
                                                    for r in found.values()):
            continue
        params = found["step"].get("params")
        assert isinstance(params, dict)
        part = _validated(str(found["step"]["kind"]), params)
        if part is None or not all(cost.fits(part, a) for a in cost.ARTIFACTS):
            continue
        candidates_seen += 1
        total = sum(int(_number(r, "bytes")) + int(_number(r, "gzip1_bytes"))
                    for r in found.values())
        if best is None or total > best[0]:
            best = (total, label)
    if best is None:
        raise ProtocolStop("R21", "no explore part is admitted and read ok at all 3 artifacts")
    mib = math.ceil(Fraction(best[0], MIB))
    return {"mib": mib, "bytes": mib * MIB, "part": best[1], "raw_and_gzip1_bytes": best[0],
            "candidates": candidates_seen, "runs": runs}


def tmpfs_base(explore: Iterable[Tagged]) -> tuple[float, str]:
    """R26's tmpfs per worker before rounding: B-01's `stl-fine` bytes budget, or where the budget
    leaves it unbounded the largest enveloped `stl-fine` bytes prediction over the admitted explore
    points."""
    component = cost.BUDGET["stl-fine"][0]
    if component is not None:
        return component, "the stl-fine bytes budget (B-01)"
    found: list[float] = []
    for _, _, reading in explore:
        params = reading.get("params")
        if reading.get("artifact") != "stl-fine" or not isinstance(params, dict):
            continue
        part = _validated(str(reading["kind"]), params)
        if part is not None and cost.fits(part, "stl-fine"):
            found.append(enveloped(part, "stl-fine", shipped_envelope())[0])
    if not found:
        raise ProtocolStop("R26", "the stl-fine bytes are unbounded and no explore point is "
                                  "admitted")
    return max(found), "the largest enveloped stl-fine bytes prediction over the admitted explore"


def tmpfs_inside(tmpfs: int, limit: int, workers: int) -> None:
    """R26: the tmpfs lives inside the container's memory, so it must fit inside mem_limit."""
    if tmpfs > limit:
        raise ProtocolStop("R26", f"the tmpfs at N = {workers}, {tmpfs} bytes, is larger than "
                                  f"mem_limit, {limit} bytes")


def _runner(headers: Sequence[Reading]) -> tuple[int, int]:
    """The one nproc every runner header recorded, and the smallest MemTotal (R16)."""
    nprocs = {h.get("nproc") for h in headers}
    totals = [h.get("mem_total_bytes") for h in headers]
    if len(nprocs) != 1:
        raise ProtocolStop("R16", f"the runner headers record nproc {sorted(map(str, nprocs))}, "
                                  "not one value, so no N is at most nproc - 1 for all of them")
    nproc = nprocs.pop()
    if not isinstance(nproc, int) or not all(isinstance(t, int) for t in totals) or not totals:
        raise ProtocolStop("R16", "a runner header records no whole nproc or MemTotal")
    return nproc, min(t for t in totals if isinstance(t, int))


def _w(bound: Sequence[Read]) -> tuple[int, str]:
    """R16's W: the max container peak over the N = 1 contention readings of every point of every
    bound set, the memory extrema included. A point without 5 ok repetitions leaves W no number."""
    best: tuple[int, str] | None = None
    for read in bound:
        if read.workers != 1:
            continue
        for reading in _five_ok(read, "R16"):
            peak = int(_number(reading, "memory_peak_bytes"))
            if best is None or peak > best[0]:
                best = (peak, _where(read.run, reading))
    if best is None:
        raise ProtocolStop("R16", "no bound point was read at N = 1, so W has no number")
    return best


@dataclass(frozen=True)
class Workers:
    """R16 at one N: its load run, tmpfs and, with 5 ok load repetitions, its load peak, p95 and
    mem_limit; whether it qualifies, and why not."""

    load_run: str
    tmpfs_bytes: int
    qualifies: bool
    why_not: tuple[str, ...]
    load_peak_bytes: int | None = None
    load_peak_reading: str | None = None
    p95_s: float | None = None
    p95_reading: str | None = None
    mem_limit_bytes: int | None = None


def per_workers(read: Read, w: int, b: int, cache: int, tmpfs: int, nproc: int,
                mem_total: int) -> Workers:
    """R16 at one N (G7): mem_limit(N), the larger of W x N + B + the export cache + the tmpfs and
    the max load peak at N, rounded up to 256 MiB. N qualifies when that is under 16 x 10^9 bytes
    and under the smallest MemTotal, N is at most nproc - 1 and all 5 load repetitions are ok."""
    n = read.workers
    why = [f"N = {n} is above nproc - 1 = {nproc - 1}"] if n > nproc - 1 else []
    if not read.ok:
        reps = sorted((str(r.get("rep")), str(r.get("status"))) for r in read.readings)
        return Workers(read.run, tmpfs, False, (*why, f"its load repetitions are not 5 ok: {reps}"))
    rows = _five_ok(read, "R16")
    peak = max(rows, key=lambda r: _number(r, "memory_peak_bytes"))
    p95s: list[tuple[float, str]] = []
    for reading in rows:
        latency = reading.get("latency")
        spread = latency.get("all") if isinstance(latency, dict) else None
        if not isinstance(spread, dict):
            raise ProtocolStop("R16", f"{_where(read.run, reading)} has no p95 over all requests")
        p95s.append((_number(spread, "p95_s"), _where(read.run, reading)))
    p95 = max(p95s)
    peak_bytes = int(_number(peak, "memory_peak_bytes"))
    limit = _round_up(max(w * n + b + cache + tmpfs, peak_bytes), LIMIT_STEP_BYTES)
    if not limit < HOST_BYTES:
        why.append(f"mem_limit {limit} is not under 16 x 10^9 bytes")
    if not limit < mem_total:
        why.append(f"mem_limit {limit} is not under the smallest MemTotal {mem_total}")
    return Workers(read.run, tmpfs, not why, tuple(why), peak_bytes, _where(read.run, peak),
                   p95[0], p95[1], limit)


def timeouts(bound: Sequence[Read], workers: int) -> dict[str, dict[str, object]]:
    """R14 (D-09) at the picked N: per artifact the bound point, the P whose max cold wall over its
    5 repetitions is the largest (a tie to the label), and the timeout `ceil(2 x` that max `)`."""
    out: dict[str, dict[str, object]] = {}
    for artifact in cost.ARTIFACTS:
        best: tuple[float, str, str] | None = None
        for read in bound:
            if read.workers != workers or read.point.get("artifact") != artifact:
                continue
            reading = max(_five_ok(read, "R14"), key=_cold_wall)
            wall, label = _cold_wall(reading), str(read.point["label"])
            if best is None or wall > best[0] or (wall == best[0] and label < best[1]):
                best = (wall, label, _where(read.run, reading))
        if best is None:
            raise ProtocolStop("R14", f"no bound point of {artifact} was read at N = {workers}")
        out[artifact] = {"seconds": math.ceil(TIMEOUT_FACTOR * best[0]), "max_cold_wall_s": best[0],
                         "bound_point": best[1], "reading": best[2]}
    return out


def _pool_deadline(call: Mapping[str, object], limits: Mapping[str, int]) -> float:
    """D-14 (`screw.pool`): a call's own timeout plus those already pending on its slot."""
    pending = call.get("pending")
    assert isinstance(pending, list)
    return limits[str(call["artifact"])] + sum(limits[str(a)] for a in pending)


def queue_depth(reads: Sequence[Read], limits: Mapping[str, int], limit: int,
                workers: int) -> dict[str, object]:
    """R17 (G8) on the picked N's load records under R14's timeouts: 2N when no pool call's queue
    wait plus build exceeds the D-14 deadline its slot gives it and every end peak is at most
    mem_limit, otherwise N."""
    worst: tuple[float, str] | None = None
    peak = 0
    for read in reads:
        for reading in _five_ok(read, "R17"):
            peak = max(peak, int(_number(reading, "memory_peak_bytes")))
            calls = reading.get("pool_calls")
            if not isinstance(calls, list) or not calls:
                raise ProtocolStop("R17", f"{_where(read.run, reading)} has no pool log")
            for index, call in enumerate(calls):
                assert isinstance(call, dict)
                ratio = (_number(call, "end_s") - _number(call, "submit_s")) / _pool_deadline(
                    call, limits)
                if worst is None or ratio > worst[0]:
                    worst = (ratio, f"{_where(read.run, reading)} pool call {index}")
    assert worst is not None
    timed_out, over = worst[0] > 1.0, peak > limit
    return {"depth": workers if timed_out or over else 2 * workers,
            "largest_wall_over_deadline": worst[0], "reading": worst[1],
            "end_peak_bytes": peak, "mem_limit_bytes": limit}


def _wall_of(request: Mapping[str, object]) -> float:
    return _number(request, "end_s") - _number(request, "start_s")


def retry_after(reads: Sequence[Read]) -> dict[str, dict[str, object]]:
    """R18 (D-11): per artifact, the median built-request wall of the picked N's load runs, pooled
    over its 5 repetitions. The ceil and the live queue depth are applied at run time."""
    walls: dict[str, list[float]] = {}
    for read in reads:
        for reading in _five_ok(read, "R18"):
            requests = reading.get("requests")
            assert isinstance(requests, list)
            for request in requests:
                assert isinstance(request, dict)
                if request.get("status_code") == 200:
                    walls.setdefault(str(request["artifact"]), []).append(_wall_of(request))
    return {artifact: {"median_s": statistics.median(walls[artifact]),
                       "samples": len(walls[artifact])} for artifact in cost.ARTIFACTS}


def minimum_size(reads: Sequence[Read], level: int) -> dict[str, object]:
    """R20: the smallest measured JSON body length from which every measured body shrinks at the
    adopted level: the smallest length above the largest body that does not shrink."""
    bodies: list[tuple[int, int, str]] = []
    for read in reads:
        for reading in read.readings:
            found = reading.get("bodies")
            if reading.get("status") != "ok" or not isinstance(found, list):
                continue
            for body in found:
                assert isinstance(body, dict)
                gz = body.get("gzip")
                assert isinstance(gz, dict)
                bodies.append((int(_number(body, "bytes")), int(gz[str(level)]),
                               f"{_where(read.run, reading)} {body.get('path')}"))
    if not bodies:
        raise ProtocolStop("R20", "no load reading measured a JSON body")
    grows = [b for b in bodies if b[1] >= b[0]]
    floor = max(grows, default=None)
    above = sorted(b[0] for b in bodies if floor is None or b[0] > floor[0])
    if not above:
        raise ProtocolStop("R20", f"the largest measured body does not shrink at level {level}")
    return {"bytes": above[0], "level": level, "bodies": len(bodies),
            "largest_not_shrinking": None if floor is None else {
                "bytes": floor[0], "gzip_bytes": floor[1], "body": floor[2]},
            "runs": sorted({read.run for read in reads})}


def screw_workers(reads: Sequence[Read]) -> dict[str, object]:
    """R24: `SCREW_WORKERS` stays 1 when the max over the picked N's 5 repetitions of each one's
    `/api/health` p95 is at most the probe's 1 s; otherwise, or below 20 samples, a stop."""
    worst: tuple[float, str] | None = None
    for read in reads:
        for reading in _five_ok(read, "R24"):
            spread = reading.get("health_latency")
            assert isinstance(spread, dict)
            if _number(spread, "samples") < HEALTH_SAMPLES:
                raise ProtocolStop("R24", f"{_where(read.run, reading)} has "
                                          f"{spread.get('samples')} health samples, under 20")
            p95 = _number(spread, "p95_s")
            if worst is None or p95 > worst[0]:
                worst = (p95, _where(read.run, reading))
    assert worst is not None
    if worst[0] > HEALTH_PROBE_S:
        raise ProtocolStop("R24", f"the health p95 under load is {worst[0]} s at {worst[1]}, "
                                  "above the probe's 1 s")
    return {"workers": 1, "health_p95_s": worst[0], "reading": worst[1]}


def healthcheck(reads: Sequence[Read]) -> dict[str, object]:
    """R25 (G18): `--timeout` is ceil(2 x the max wall of the HEALTHCHECK command) over the picked
    N's 5 load readings; `--start-period` 2 x the max time to the first healthy response, rounded
    up to 10 s; `--interval` and `--retries` Docker's documented defaults."""
    walls: list[tuple[float, str]] = []
    healthy: list[tuple[float, str]] = []
    failed = 0
    for read in reads:
        for reading in _five_ok(read, "R25"):
            healthy.append((_number(reading, "time_to_healthy_s"), _where(read.run, reading)))
            checks = reading.get("healthcheck")
            assert isinstance(checks, list)
            for check in checks:
                assert isinstance(check, dict)
                walls.append((_number(check, "wall_s"), _where(read.run, reading)))
                failed += check.get("exit_code") != 0
    if not walls:
        raise ProtocolStop("R25", "no HEALTHCHECK command was timed under load")
    wall, slowest = max(walls), max(healthy)
    return {"timeout_s": math.ceil(TIMEOUT_FACTOR * wall[0]), "max_wall_s": wall[0],
            "wall_reading": wall[1], "walls": len(walls), "nonzero_exits": failed,
            "start_period_s": START_PERIOD_STEP_S * math.ceil(
                Fraction(TIMEOUT_FACTOR * slowest[0]) / START_PERIOD_STEP_S),
            "max_time_to_healthy_s": slowest[0], "healthy_reading": slowest[1],
            "interval_s": DOCKER_INTERVAL_S, "retries": DOCKER_RETRIES,
            "interval_and_retries": "Docker's documented defaults (R25)"}


def derivation(headers: Sequence[Reading], tagged: Sequence[Tagged],
               sets: Mapping[str, Sequence[Mapping[str, object]]], sources: Sequence[str], *,
               stage_two: bool = False) -> Iterator[tuple[str, object]]:
    """runtime.json's values in order, each as it is derived. First R14 to R21 and R24 to R26
    over the records, in the order their inputs exist (07-16), from the committed `bound`, `load`
    and `gzip` points in `sets`; then, with `stage_two`, R22 and R23 from the `solid-cache-<k>`,
    `arenas` and `drift` points, which need the pick and the timeouts. A stop ends it there."""
    bound = matched(sets["bound"], tagged, BOUND_SETS, _IDENTITY, "R14")
    gzip_reads = matched(sets["gzip"], tagged, GZIP_SETS, _IDENTITY, "R19")
    loads = matched(sets["load"], tagged, LOAD_SETS, _LOAD_IDENTITY, "R15")
    explore = [t for t in tagged if t[0] == "explore"]
    gzip = gzip_level(gzip_reads)
    cache = export_cache(explore, gzip_reads)
    base, base_rule = tmpfs_base(explore)
    nproc, mem_total = _runner(headers)
    w, w_reading = _w(bound)
    w_row: dict[str, object] = {"bytes": w, "reading": w_reading}
    drifts: dict[str, dict[str, object]] = {}
    flat: dict[str, dict[str, object]] = {}
    if stage_two:  # R23's plateau, then W takes the drift readings' largest peak (R16, G32)
        drift_reads = matched(sets["drift"], tagged, DRIFT_SETS, _DRIFT_IDENTITY, "R23")
        plateau_reads = matched(sets[f"drift-{PLATEAU_BUILDS}"], tagged, PLATEAU_SETS,
                                _DRIFT_IDENTITY, "R23")
        drifts, flat = drift(drift_reads), plateau(plateau_reads, drift_reads)
        peak, peak_reading = drift_peak([*drift_reads, *plateau_reads])
        w_row = {"bytes": max(w, peak), "contention": {"bytes": w, "reading": w_reading},
                 "drift": {"bytes": peak, "reading": peak_reading}}
        w = max(w, peak)
    idle = [(int(_number(r, "idle_peak_bytes")), _where(read.run, r))
            for read in loads for r in read.readings if r.get("status") == "ok"]
    if not idle:
        raise ProtocolStop("R16", "no load reading is ok, so B has no number")
    b = max(idle)
    cache_bytes = cache["bytes"]
    assert isinstance(cache_bytes, int)
    rows = {read.workers: per_workers(read, w, b[0], cache_bytes,
                                      _round_up(base * read.workers, LIMIT_STEP_BYTES), nproc,
                                      mem_total) for read in loads}
    ranked = sorted((row.p95_s, n) for n, row in rows.items()
                    if row.qualifies and row.p95_s is not None)
    if not ranked:
        raise ProtocolStop("R16", "no N qualifies (G7): " + "; ".join(
            f"N = {n}: {', '.join(row.why_not)}" for n, row in sorted(rows.items())))
    picked = ranked[0][1]  # the lowest max-over-reps p95, a tie to the smaller N
    limit = rows[picked].mem_limit_bytes
    assert limit is not None
    tmpfs_inside(rows[picked].tmpfs_bytes, limit, picked)
    limits = timeouts(bound, picked)
    for read in bound:  # every bound point has 5 ok repetitions from one run (R3, G31)
        _five_ok(read, "R14")
    picked_reads = [read for read in loads if read.workers == picked]
    seconds = {artifact: int(str(row["seconds"])) for artifact, row in limits.items()}
    level = gzip["level"]
    assert isinstance(level, int)
    yield from {
        "rule": ("07-SWEEP-PROTOCOL.md R14 to R26 (G6 to G9, G11, G15 to G18, G20, G22, G31, G32)"
                 if stage_two else "07-SWEEP-PROTOCOL.md R14 to R21, R24 to R26 (G6, G7, G8, "
                 "G11, G15, G16, G18, G22, G31)"),
        "sources": list(sources),
        "sets": {name: f"bench/points/{name}.json" for name in sorted(sets)},
        "runner": {"nproc": nproc, "smallest_mem_total_bytes": mem_total, "headers": len(headers)},
        "gzip": gzip,
        "export_cache": cache,
        "tmpfs_per_worker": {"bytes": base, "rule": base_rule},
        "w": w_row,
        "b": {"bytes": b[0], "reading": b[1]},
        "per_workers": {str(n): dataclasses.asdict(row) for n, row in sorted(rows.items())},
        "picked_workers": picked,
        "mem_limit_bytes": limit,
        "tmpfs_bytes": rows[picked].tmpfs_bytes,
        "timeouts": limits,
        "queue_depth": queue_depth(picked_reads, seconds, limit, picked),
        "retry_after": retry_after(picked_reads),
        "minimum_size": minimum_size(loads, level),
        "screw_workers": screw_workers(picked_reads),
        "healthcheck": healthcheck(picked_reads)}.items()
    if not stage_two:
        return
    picked_load = picked_reads[0]
    cache_row = solid_cache(
        {k: matched(sets[f"solid-cache-{k}"], tagged, (f"solid-cache-{k}",), _LOAD_IDENTITY,
                    "R22")[0] for k in SOLID_CACHE_KS if f"solid-cache-{k}" in sets},
        lambda w_k: per_workers(picked_load, w_k, b[0], cache_bytes, rows[picked].tmpfs_bytes,
                                nproc, mem_total))
    yield "solid_cache_k", cache_row["k"]
    yield "solid_cache", cache_row
    w_k_rows = cache_row["w_k"]
    assert isinstance(w_k_rows, dict)
    w_k_limit = w_k_rows[str(cache_row["k"])]["mem_limit_bytes"]
    assert isinstance(w_k_limit, int)
    yield "shipped_mem_limit", {  # G20: the larger of the two, both at the picked N (R16, R22)
        "bytes": max(limit, w_k_limit), "from_w_bytes": limit, "from_w_k_bytes": w_k_limit}
    release = arenas(matched(sets["arenas"], tagged, ("arenas",), _ARENAS_IDENTITY, "R23"))
    yield "arenas_kept", release["kept"]
    yield "arenas", release
    yield "drift", drifts
    yield "plateau", flat
    yield "recycling", {"max_tasks_per_child": None,
                        "rule": "R23: the plateau holds at every artifact, and the drift is "
                                "counted in W (R16)"}
    yield "tessellation_kept", {"kept": True, "rule": "R23: the tessellation presets are kept"}


def runtime(headers: Sequence[Reading], tagged: Sequence[Tagged],
            sets: Mapping[str, Sequence[Mapping[str, object]]],
            sources: Sequence[str]) -> dict[str, object]:
    """runtime.json's values: the whole `derivation`, or a stop."""
    return dict(derivation(headers, tagged, sets, sources))


def _points_of(name: str) -> list[Mapping[str, object]]:
    points = json.loads((POINTS_DIR / f"{name}.json").read_text())["points"]
    assert isinstance(points, list)
    return points


def _runtime_sets() -> dict[str, list[Mapping[str, object]]]:
    """Every committed point file the derivation reads: the bound, gzip and load sets (G6), then
    R22's W(K) sets that exist, R23's arena set and both drift sets (G32)."""
    names = ["bound", "gzip", "load", "arenas", "drift", f"drift-{PLATEAU_BUILDS}",
             *(f"solid-cache-{k}" for k in SOLID_CACHE_KS
               if (POINTS_DIR / f"solid-cache-{k}.json").is_file())]
    return {name: _points_of(name) for name in names}


def derive_runtime(directories: Iterable[Path]) -> dict[str, object]:
    """runtime.json's values, stage two included, from the records under `directories` and the
    committed point files (G6, G32)."""
    folders = sorted(Path(d) for d in directories)
    headers, tagged = read_runs(folders)
    return dict(derivation(headers, tagged, _runtime_sets(), [_relative(str(d)) for d in folders],
                           stage_two=True))


def runtime_text(directories: Iterable[Path]) -> str:
    return json.dumps(derive_runtime(directories), indent=1, allow_nan=False) + "\n"


# --- R22's W(K) set and R23's drift set (07-16 Task 2), after the pick and the timeouts --------

DRIFT_BUILDS = 20  # R23's K: the parts a load run takes for each artifact (R15)
PLATEAU_BUILDS = 60  # R23's plateau reading, its builds 21 to 40 against 41 to 60
DRIFT_SETS = ("drift",)
PLATEAU_SETS = ("drift-60",)
SOLID_CACHE_KS = (4, 3, 2, 1)  # R22: K = 4 first, each lower K only if the one above failed
BOUND_POINTS = "bench/points/bound.json"
LOAD_POINTS = "bench/points/load.json"


def _bound_set(bound: Iterable[Mapping[str, object]], artifact: str) -> list[Mapping[str, object]]:
    """The points P of `artifact`'s committed bound set, each once, from its contention points."""
    found: dict[str, Mapping[str, object]] = {}
    for point in bound:
        members = point.get("points")
        if point.get("artifact") == artifact and isinstance(members, list) and members:
            p = members[0]
            assert isinstance(p, dict)
            found.setdefault(str(p["label"]), p)
    return list(found.values())


def drift_points(bound: Sequence[Mapping[str, object]], explore: Iterable[Reading],
                 timeouts: Mapping[str, int],
                 builds: int = DRIFT_BUILDS) -> list[dict[str, object]]:
    """R23's drift readings: per artifact A, Z(A), the point of A's committed bound set with the
    largest `memory_peak_bytes` among its ok explore readings (a tie to the label that sorts
    first), built K times with a deadline of K x A's timeout (R14): K = 20, or 60 for the plateau
    reading, the same parts in the same order. A deadline that is not
    under half the measure job's timeout stops the phase (R6, G4): the job also counts setup, the
    image build and the upload."""
    index = _explore_index(explore)
    out: list[dict[str, object]] = []
    for artifact in cost.ARTIFACTS:
        measured: list[tuple[int, str, Mapping[str, object]]] = []
        for p in _bound_set(bound, artifact):
            reading = _ok(index, str(p["label"]), artifact)
            if reading is not None:
                measured.append((int(_number(reading, "memory_peak_bytes")), str(p["label"]), p))
        if not measured:
            raise ProtocolStop("R23", f"no point of the {artifact} bound set has an ok explore "
                                      "reading, so Z(A) has no part")
        _, label, z = min(measured, key=lambda m: (-m[0], m[1]))
        deadline = builds * timeouts[artifact]
        if not deadline < HALF_JOB_S:
            raise ProtocolStop("R6", f"the drift reading of {label} at {artifact} has a deadline "
                                     f"of {deadline} s, not under half the job timeout "
                                     f"({HALF_JOB_S:g} s)")
        out.append({"label": f"drift-{label}", "kind": "drift", "artifact": artifact,
                    "part": {"kind": z["kind"], "params": z["params"]}, "k": builds,
                    "deadline_s": deadline})
    return out


def solid_cache_points(load: Sequence[Mapping[str, object]], k: int) -> list[dict[str, object]]:
    """R22's W(K) reading (G9): the committed R15 mix at N = 1, a queue and clients of 2, with
    `SCREW_SOLID_CACHE` = K; the JSON bodies are R20's and are not read again."""
    one = [p for p in load if p.get("workers") == 1]
    if len(one) != 1:
        raise ValueError("the load set has no one point at N = 1")
    return [{"label": f"solid-cache-{k}", "kind": "load", "workers": 1, "queue": 2, "clients": 2,
             "solid_cache": k, "bodies": False, "mix": one[0]["mix"]}]


def _runtime_timeouts(path: str) -> dict[str, int]:
    rows = json.loads((REPO_ROOT / path).read_text())["timeouts"]
    return {artifact: int(rows[artifact]["seconds"]) for artifact in cost.ARTIFACTS}


def _explore_dir_of(bound_path: str) -> str:
    sources = json.loads((REPO_ROOT / bound_path).read_text())["sources"]
    return dict(str(entry).split("=", 1) for entry in sources)["explore"]


def build_drift(bound_path: str, runtime_path: str, builds: int = DRIFT_BUILDS) -> _Set:
    bound = json.loads((REPO_ROOT / bound_path).read_text())["points"]
    explore_dir = _explore_dir_of(bound_path)
    plateau = builds != DRIFT_BUILDS
    out = _Set(f"drift-{builds}" if plateau else "drift", reps=RUNS2_REPS, shards=1,
               rule=f"07-SWEEP-PROTOCOL.md R23 (G4, G14{', G32' if plateau else ''})", notes=[
                   "per artifact Z(A): the point of the committed bound set (bound.json) with the "
                   "largest memory_peak_bytes among its ok explore readings, a tie to the label "
                   "that sorts first",
                   f"K = {builds} cold builds in one process, the solid cache emptied before "
                   "each; the peak read after each build, its export and a level-1 gzip (G14)",
                   f"each reading's deadline_s is {builds} x its artifact's timeout "
                   "(runtime.json, R14), and it is charged that deadline (R6, G4); 5 repetitions",
                   *(["the plateau reading (G32): the same parts in the same order as drift.json; "
                      "builds 41 to 60 against builds 21 to 40"] if plateau else [])])
    for point in drift_points(bound, _read(explore_dir), _runtime_timeouts(runtime_path),
                              builds):
        out.copy(point)
    charged = [float(str(point["deadline_s"])) for point in out.points]
    out.shard_sizes = shard_sizes(charged, HALF_JOB_S)
    out.shards = len(out.shard_sizes)
    out.sources = [f"bound={bound_path}", f"explore={explore_dir}", f"runtime={runtime_path}"]
    return out


def build_solid_cache(load_path: str, k: int) -> _Set:
    load = json.loads((REPO_ROOT / load_path).read_text())["points"]
    out = _Set(f"solid-cache-{k}", reps=RUNS2_REPS, shards=1,
               rule="07-SWEEP-PROTOCOL.md R22 (G4, G9)", notes=[
                   f"W({k}): the committed R15 mix (load.json) at N = 1, queue and clients 2, "
                   f"SCREW_SOLID_CACHE = {k}, measured after R16's pick (G9)",
                   "W(K) is the max container peak over the 5 repetitions; each reading charged "
                   "R2's 600 s (R6, G4)"])
    for point in solid_cache_points(load, k):
        out.copy(point)
    out.shard_sizes = shard_sizes([float(DEADLINE_S)] * len(out.points), HALF_JOB_S)
    out.shards, out.sources = len(out.shard_sizes), [f"load={load_path}"]
    return out


_DRIFT_IDENTITY = ("label", "kind", "artifact", "part", "k", "deadline_s")
_ARENAS_IDENTITY = ("label", "kind", "artifact", "part", "trim")
DRIFT_ALLOWANCE = Fraction(1, 10)  # R23: of the smallest build-1 peak, fixed before any reading


def solid_cache(w_reads: Mapping[int, Read],
                qualify: Callable[[int], Workers]) -> dict[str, object]:
    """R22 (G9, G20): K = 4 if mem_limit built from W(4) at the picked N still qualifies (R16),
    else the largest K in 3, 2, 1 that does; W(K) the max container peak over its 5 repetitions
    at N = 1. A lower K is read only once the one above failed, so a K that is needed and not
    measured is a stop, as is a W(K) repetition that is not ok and no K that qualifies."""
    rows: list[tuple[int, int, str, Workers]] = []
    for k in SOLID_CACHE_KS:
        if k not in w_reads:
            raise ProtocolStop("R22", f"W({k + 1}) does not qualify and W({k}) is not measured")
        read = w_reads[k]
        peak = max(_five_ok(read, "R22"), key=lambda r: _number(r, "memory_peak_bytes"))
        w_k = int(_number(peak, "memory_peak_bytes"))
        rows.append((k, w_k, _where(read.run, peak), qualify(w_k)))
        if rows[-1][3].qualifies:
            return {"k": k, "runs": [w_reads[j].run for j, *_ in rows], "w_k": {
                str(j): {"w_bytes": w, "reading": where, "mem_limit_bytes": row.mem_limit_bytes,
                         "qualifies": row.qualifies, "why_not": list(row.why_not)}
                for j, w, where, row in rows}}
    raise ProtocolStop("R22", "no K in 4, 3, 2, 1 qualifies: " + "; ".join(
        f"W({k}): {', '.join(row.why_not)}" for k, _, _, row in rows))


def drift(reads: Sequence[Read]) -> dict[str, dict[str, object]]:
    """R23's drift per artifact: the max over its 5 repetitions of the peak after build K minus the
    peak after build 1, with each repetition's, and the allowance, 0.10 x the smallest build-1
    peak. A repetition that is not ok or misses build 1 or build K leaves no drift: a stop."""
    out: dict[str, dict[str, object]] = {}
    for read in reads:
        k = read.point["k"]
        assert isinstance(k, int)
        rows: list[tuple[int, int, str, list[object]]] = []
        for reading in _five_ok(read, "R23"):
            peaks = reading.get("peaks")
            if not isinstance(peaks, list) or len(peaks) < k:
                raise ProtocolStop("R23", f"{_where(read.run, reading)} has no peak after build "
                                          f"1 and build {k}")
            rows.append((int(peaks[0]), int(peaks[k - 1]), _where(read.run, reading), peaks))
        worst = max(rows, key=lambda row: row[1] - row[0])
        allowance = DRIFT_ALLOWANCE * min(row[0] for row in rows)
        out[str(read.point["artifact"])] = {
            "drift_bytes": worst[1] - worst[0], "reading": worst[2],
            "allowance_bytes": float(allowance), "above_allowance": worst[1] - worst[0] > allowance,
            "repetitions": [{"reading": where, "drift_bytes": last - first, "peaks": peaks}
                            for first, last, where, peaks in rows]}
    return out


def plateau(reads: Sequence[Read], drift_reads: Sequence[Read]) -> dict[str, dict[str, object]]:
    """R23's plateau (G32), fixed before its reading: per artifact and repetition of the 60-build
    reading, the max peak over builds 41 to 60 minus the max peak over builds 21 to 40, which at
    the worst repetition of every artifact must be at most 0.10 x the smallest build-1 peak among
    the repetitions of both drift readings of that artifact. A miss stops the phase, and the next
    step is recycling; a repetition that is not ok or misses a build's peak leaves no plateau."""
    firsts: dict[str, list[int]] = {}
    for read in drift_reads:
        for reading in _five_ok(read, "R23"):
            peaks = reading.get("peaks")
            assert isinstance(peaks, list)
            firsts.setdefault(str(read.point["artifact"]), []).append(int(peaks[0]))
    out: dict[str, dict[str, object]] = {}
    for read in reads:
        artifact = str(read.point["artifact"])
        rows: list[tuple[int, str]] = []
        for reading in _five_ok(read, "R23"):
            peaks = reading.get("peaks")
            if not isinstance(peaks, list) or len(peaks) < PLATEAU_BUILDS:
                raise ProtocolStop("R23", f"{_where(read.run, reading)} has no peak after each of "
                                          f"its {PLATEAU_BUILDS} builds")
            values = [int(peak) for peak in peaks[:PLATEAU_BUILDS]]
            firsts.setdefault(artifact, []).append(values[0])
            rows.append((max(values[40:60]) - max(values[20:40]), _where(read.run, reading)))
        worst = max(rows)
        allowance = DRIFT_ALLOWANCE * min(firsts[artifact])
        out[artifact] = {"difference_bytes": worst[0], "reading": worst[1],
                         "allowance_bytes": float(allowance), "holds": worst[0] <= allowance,
                         "repetitions": [{"reading": where, "difference_bytes": difference}
                                         for difference, where in rows]}
    missed = [f"{artifact}: builds 41 to 60 peak {row['difference_bytes']} bytes above builds 21 "
              f"to 40 at {row['reading']}, over its allowance of {row['allowance_bytes']!r} bytes"
              for artifact, row in out.items() if not row["holds"]]
    if missed:
        raise ProtocolStop("R23", "the plateau does not hold: " + "; ".join(missed)
                                  + "; the next step is recycling")
    return out


def drift_peak(reads: Sequence[Read]) -> tuple[int, str]:
    """The largest peak after any build of the drift readings, which W takes once the plateau
    holds (R16, G32), and the reading and build that set it."""
    best: tuple[int, str] | None = None
    for read in reads:
        for reading in _five_ok(read, "R23"):
            peaks = reading.get("peaks")
            assert isinstance(peaks, list)
            for number, peak in enumerate(peaks, start=1):
                if best is None or int(peak) > best[0]:
                    best = (int(peak), f"{_where(read.run, reading)} build {number}")
    assert best is not None
    return best


def arenas(reads: Sequence[Read]) -> dict[str, object]:
    """R23 (G17, G22): the trim is kept only if, at every artifact, the max over 5 repetitions of
    the cgroup's `memory.current` read after the export is lower with it than without."""
    maxima: dict[str, dict[bool, tuple[int, str]]] = {}
    for read in reads:
        reading = max(_five_ok(read, "R23"), key=lambda r: _number(r, "memory_current_bytes"))
        maxima.setdefault(str(read.point["artifact"]), {})[read.point["trim"] is True] = (
            int(_number(reading, "memory_current_bytes")), _where(read.run, reading))
    lower = {artifact: sides[True][0] < sides[False][0] for artifact, sides in maxima.items()}
    return {"kept": all(lower.values()), "lower_with_trim": lower,
            "runs": sorted({read.run for read in reads}),
            "maxima": {artifact: {f"trim_{'on' if trim else 'off'}": {
                "memory_current_bytes": value, "reading": where}
                for trim, (value, where) in sorted(sides.items(), reverse=True)}
                for artifact, sides in maxima.items()}}


def _runtime_set_paths() -> list[Path]:
    return [POINTS_DIR / "drift.json", POINTS_DIR / f"drift-{PLATEAU_BUILDS}.json",
            *(POINTS_DIR / f"solid-cache-{k}.json" for k in SOLID_CACHE_KS)]


def _regenerate_runtime_set(path: Path, text: str) -> str:
    """The text a drift or W(K) file would have if written again from its own sources."""
    sources = dict(str(e).split("=", 1) for e in json.loads(text).get("sources", []))
    if path.stem.startswith("drift"):
        builds = DRIFT_BUILDS if path.stem == "drift" else PLATEAU_BUILDS
        return build_drift(sources["bound"], sources["runtime"], builds).text()
    return build_solid_cache(sources["load"], int(path.stem.rsplit("-", 1)[1])).text()


def _check_runtime_sets() -> str | None:
    """The first drift or W(K) file that is not what its generator writes from its sources."""
    for path in _runtime_set_paths():
        if not path.is_file():
            continue
        text = path.read_text()
        try:
            again = _regenerate_runtime_set(path, text)
        except (KeyError, TypeError, ValueError) as exc:  # a stop is a ValueError, too
            return f"{path} cannot be written again from its sources: {exc}"
        if text != again:
            return f"{path} is not what the generator writes from its sources"
    return None


def _recorded_envelope(text: str) -> dict[tuple[str, str, str], float]:
    """The envelope a Runs II file was drawn under. A recorded e above the shipped one is no
    envelope this code ever shipped (a widening only raises e), so the file cannot stand."""
    recorded, shipped = envelope_of(json.loads(text).get("envelope")), shipped_envelope()
    if set(recorded) != set(shipped):
        raise ValueError("its envelope does not name every model the cost rule ships")
    above = [key for key, e in recorded.items() if e > shipped[key]]
    if above:
        raise ValueError(f"its recorded e of {' '.join(above[0])} exceeds the shipped one")
    return recorded


def _regenerate_runs2(name: str, text: str) -> str:
    """The text a Runs II file would have if drawn again from its sources under its own recorded
    envelope (G6)."""
    envelope = _recorded_envelope(text)
    if name == "tier-order":
        return tier_order_text(envelope)
    raw = json.loads(text)
    sources = dict(str(entry).split("=", 1) for entry in raw.get("sources", []))
    needs = {"bound": ("explore",), "load": ("tier-order", "explore"), "gzip": ("explore",),
             "arenas": ("explore",), "outband": ("explore",), "bound-rerun": ("explore", "run"),
             "gzip-rerun": ("explore", "run"), PITCH_WALK: ("explore",)}[name]
    missing = [source for source in needs if source not in sources]
    if missing:
        raise ValueError(f"it names no {' and '.join(missing)} source")
    if name == "bound":
        return build_bound(sources["explore"], envelope).text()
    if name == "load":
        return build_load(sources["tier-order"], sources["explore"]).text()
    if name == "arenas":
        return build_arenas(sources["explore"], envelope).text()
    if name == "outband":
        return build_outband(sources["explore"], envelope).text()
    if name in RERUN_SETS:
        return build_rerun(name, sources["explore"], sources["run"], envelope).text()
    if name == PITCH_WALK:
        return build_pitch_walk(sources["explore"], envelope).text()
    return build_gzip(sources["explore"], envelope).text()


def _check_runs2() -> str | None:
    """The first Runs II file that is not what its generator writes under its recorded envelope,
    with the reason, or None. Absent files are not checked: each is written by its own step."""
    paths = [("tier-order", REPO_ROOT / TIER_ORDER),
             *((name, POINTS_DIR / f"{name}.json") for name in (*RUNS2_SETS, *RERUN_SETS,
                                                                PITCH_WALK))]
    for name, path in paths:
        if not path.is_file():
            continue
        text = path.read_text()
        try:
            same = same_but_predicted(text, _regenerate_runs2(name, text))
        except (TypeError, ValueError) as exc:  # a stop is a ValueError, too
            return f"{path} cannot be written again from its sources: {exc}"
        if not same:
            return f"{path} is not what the generator writes from its sources"
    return None


def _regenerate(path: Path) -> str:
    """The text a derived point file would have if written again from its own `sources`."""
    raw = json.loads(path.read_text())
    sources = dict(str(entry).split("=", 1) for entry in raw.get("sources", []))
    needs = {"walls-down": ("walls", "explore"), "walls-voids": ("explore",),
             "walls-confirm": ("walls", "explore")}[path.stem]
    missing = [name for name in needs if name not in sources]
    if missing:
        raise ValueError(f"it names no {' and '.join(missing)} source")
    if path.stem == "walls-down":
        out = build_walk_down(sources["walls"], sources["explore"])
    elif path.stem == "walls-voids":
        out = build_void_walk(sources["explore"])
    else:
        out = build_confirm(sources["walls"], sources.get("walls-down"), sources["explore"])
    if out is None:
        raise ValueError("its sources need no such set")
    return out.text()


# --- R27 step 5: the required tier (07-18) -------------------------------------------------------
#
# The tier is cut from the committed D(A) (`tier-order.json`, steps 1 to 4, never drawn again: G6)
# with the timeouts R14 fixed, so it could not exist before 07-16. Each point carries what R29
# judges it by: its artifact's timeout and, per target, the shipped prediction x (1 + e). A widening
# therefore moves a point's limits and nothing else, and the regeneration test in
# tests/test_oper_followup.py fails `make verify` when this file and the shipped constants disagree.

TIER_S = 600  # R27 step 5: D-12's 10 minutes; an artifact's summed charges stay under it
# R27 (G34): the tier is read in parallel shards, each about D-12's 10 minutes of readings; read
# in one job, the 435 points took 35.5 min on the runner (07-18).
SHARD_S = 600
BOUNDARY = "tests/data/oper_boundary.json"


def boundary_points(tier: Mapping[str, object], points: Sequence[Mapping[str, object]],
                    readings: Iterable[Reading], envelope: Envelope,
                    timeouts: Mapping[cost.Artifact, float]) -> list[dict[str, object]]:
    """R27 step 5 per artifact, in `cost.ARTIFACTS` order, over the committed D(A): the 3 edge
    points always, then draw points in order, each only while the summed charges of the points
    taken, itself included, stay under `TIER_S`, stopping at the first that does not fit. A point's
    charge is the cold wall of its explore reading when that is ok, and otherwise its artifact's
    full timeout (R14), never `wall_s`. `points` gives each label its params; the order and the
    membership come from `tier` alone. A point's `estimate_s`, which sizes the shards (G34), is
    its explore container wall, or the larger of that and its timeout where that reading is not
    ok: a container wall counts the start and the stop a cold wall leaves out."""
    index = _explore_index(readings)
    by_label = {(str(p["label"]), str(p["artifact"])): p for p in points if "artifact" in p}
    out: list[dict[str, object]] = []
    for artifact in cost.ARTIFACTS:
        ranking, draw = _tier_lists(tier, artifact)
        timeout = float(timeouts[artifact])
        total = 0.0
        for position, label in enumerate([*ranking[:EDGE_POINTS], *draw]):
            if (label, artifact) not in by_label:
                raise ValueError(f"tier-order.json names {label} at {artifact}, which the explore "
                                 "file does not hold")
            if (label, artifact) not in index:
                raise ProtocolStop("R27", f"{label} at {artifact} has no explore reading")
            reading = index[label, artifact]
            charge = _cold_wall(reading) if reading.get("status") == "ok" else timeout
            if position >= EDGE_POINTS and not total + charge < TIER_S:
                break
            total += charge
            point = by_label[label, artifact]
            kind, params = str(point["kind"]), point["params"]
            assert isinstance(params, dict)
            part = _validated(kind, params)
            if part is None:
                raise ValueError(f"tier-order.json names {label}, which the parameter model "
                                 "refuses")
            limit = enveloped(part, artifact, envelope)
            wall = _number(reading, "wall_s")
            out.append({"label": label, "kind": kind, "params": dict(params),
                        "artifact": artifact, "charge_s": charge,
                        "estimate_s": wall if reading.get("status") == "ok" else max(wall,
                                                                                    timeout),
                        "timeout_s": timeout,
                        "limit": dict(zip(cost.TARGETS, limit, strict=True))})
    return out


def boundary_text(explore_dir: str) -> str:
    """`tests/data/oper_boundary.json`: R27 step 5 over the committed `tier-order.json` and the
    explore readings under `explore_dir`, with the shipped envelope and timeouts."""
    tier = json.loads((REPO_ROOT / TIER_ORDER).read_text())
    envelope = shipped_envelope()
    points = boundary_points(tier, _explore_points(), _read(explore_dir), envelope,
                             cost.BUILD_TIMEOUT_S)
    document = {
        "rule": "07-SWEEP-PROTOCOL.md R27 step 5, judged by R29 (D-07, D-12, G6, G34)",
        "tier_s": TIER_S, "sources": [f"tier-order={TIER_ORDER}", f"explore={explore_dir}"],
        "timeouts": dict(cost.BUILD_TIMEOUT_S), "envelope": envelope_document(envelope),
        "shard_s": SHARD_S,
        "shard_sizes": shard_sizes([_number(p, "estimate_s") for p in points], SHARD_S),
        "points": points}
    return json.dumps(document, indent=1) + "\n"


# --- R31: the fine-pitch walk (G35) --------------------------------------------------------------
#
# The in-wall debug session (.planning/debug/in-wall-kernel-builderror.md) found the kernel's
# end-cut booleans refuse parts at a fine pitch for their d, and the owner ruled a wall on the
# exact d / pitch per kind, final only once this walk, read on the runner, confirms it. The grid
# is the session's: its d values, its 3-turn bolt forms and its four nut forms, around each wall.

PITCH_WALK = "walls-pitch"
PITCH_RULE = "07-SWEEP-PROTOCOL.md R31 (G35)"
PITCH_BOLT_D = ("0.3", "0.5", "0.8", "1", "1.2", "1.5", "1.8", "2", "2.2", "2.5", "2.8", "3",
                "3.5", "4", "4.5", "5", "6", "8", "10", "12", "16", "20", "24", "30", "42", "60",
                "100", "150", "200", "300", "450", "600", "999.999")
PITCH_BOLT_Q = (5, 8, 10, 12, 14, *range(15, 32))
PITCH_NUT_D = ("0.5", "0.6", "0.7", "0.8", "0.9", "1", "1.1", "1.2", "1.4", "1.5", "1.6", "1.8",
               "2", "2.2", "2.4", "2.5", "2.6", "2.8", "3", "3.2", "3.5", "4", "4.5", "5", "5.5",
               "6", "7", "8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "30", "42",
               "60", "100", "200", "300", "600")
PITCH_NUT_Q = tuple(range(5, 13))
PITCH_BOLT_FORMS = ("n3", "n3s")  # t = L = 3 P; t = 3 P with a shank, L = t + d
PITCH_NUT_FORMS = ("base", "s4", "c0", "m1")  # m 0.8 d, s 1.6 d, c 0.15; s 4 d; c 0; m = d
PITCH_BOLT_S_MAX = 1000.0  # R31: s = 1.6 d at most 1000 mm, the walls' s (L20) when R31 was ruled
PITCH_TURNS = 3
# R31: a refusal comes in the build, before any export, so the status does not depend on the
# artifact; `step` is the one whose explore groups R6 charges least for both kinds (bolt 29.9 s,
# nut 38.0 s, against 600.7 s and 74.7 s at stl-preview; run 40646117094).
PITCH_ARTIFACT = ("step",)
# R31: W is the largest ISO 3 R10 number at or below F / 1.25, one R10 step under F.
R10_SERIES = tuple(Fraction(v) for v in ("1", "1.25", "1.6", "2", "2.5", "3.15", "4", "5", "6.3",
                                          "8"))
PITCH_MARGIN = Fraction(5, 4)
RULED_PITCH_WALLS = {"bolt": Fraction(20), "nut": Fraction(8)}  # G35 rulings 1 and 2


def _ceil_figures(x: Fraction) -> float:
    """`x` rounded up to 6 significant figures, exactly: a pitch of `d / q` rounded so that the
    exact `d / pitch` is at most q (R31)."""
    scale = Fraction(1)
    while scale > x:
        scale /= 10
    while scale * 10 <= x:
        scale *= 10
    step = scale / 10 ** (SIGNIFICANT_FIGURES - 1)
    return _dec(math.ceil(x / step) * step)


def _pitch_params(kind: str, form: str, d: str, q: int,
                  left: bool) -> dict[str, float | bool]:
    """The fields of one R31 cell."""
    pitch = _ceil_figures(Fraction(d) / q)
    size = float(d)
    if kind == "bolt":
        thread = _dec(PITCH_TURNS * Fraction(repr(pitch)))
        length = thread if form == "n3" else _dec(Fraction(repr(thread)) + Fraction(d))
        return {"d": size, "pitch": pitch, "length": length, "thread_length": thread,
                "s": min(_scaled(size, "1.6"), PITCH_BOLT_S_MAX), "k": _scaled(size, "0.6"),
                "left_hand": left}
    return {"d": size, "pitch": pitch,
            "m": size if form == "m1" else _scaled(size, "0.8"),
            "s": _scaled(size, "4" if form == "s4" else "1.6"),
            "clearance": 0.0 if form == "c0" else DEFAULT_NUT_CLEARANCE, "left_hand": left}


def _model_refusal(kind: str, params: Params) -> str | None:
    """The pydantic error type with which the production parameter model refuses `params`, or
    `None`."""
    try:
        KINDS[kind].model_validate(dict(params))
    except ValidationError as exc:
        return str(exc.errors()[0]["type"])
    return None


def _pitch_cells() -> Iterator[tuple[str, str, str, int, bool]]:
    """(kind, form, d, q, left) of every R31 cell, in file order."""
    for kind, forms, sizes, ratios in (("bolt", PITCH_BOLT_FORMS, PITCH_BOLT_D, PITCH_BOLT_Q),
                                       ("nut", PITCH_NUT_FORMS, PITCH_NUT_D, PITCH_NUT_Q)):
        for form in forms:
            for d in sizes:
                for q in ratios:
                    for left in (False, True):
                        yield kind, form, d, q, left


def pitch_walk_set(envelope: Envelope, budget: Budget = cost.BUDGET) -> _Set:
    """R31's walk, unsharded: every cell at `step`, a cell the parameter model refuses or the cost
    model admits at no artifact (under `envelope`) in `dropped` with its type."""
    out = _Set(PITCH_WALK, reps=1, shards=1, rule=PITCH_RULE, notes=[
        "R31: bolts with 3 turns of thread (t = L = 3 pitch, and t = 3 pitch with L = t + d), s "
        "1.6 d at most 1000 mm, k 0.6 d; nuts m 0.8 d, s 1.6 d, clearance 0.15, and the same with "
        "s 4 d, with clearance 0, and with m = d; both hands; pitch = d / q rounded up to 6 "
        "significant figures, so the exact d / pitch is at most q",
        "1 repetition at step; F per kind is the smallest exact d / pitch of a refused or crashed "
        "reading, W the largest ISO 3 R10 number at or below F / 1.25 (G35)"])
    for kind, form, d, q, left in _pitch_cells():
        params = _pitch_params(kind, form, d, q, left)
        label = f"pitch-{kind}-{form}-d{d}-q{q}-{_hand(left)}"
        error = _model_refusal(kind, params)
        if error is None:
            part = KINDS[kind].model_validate(params)
            if not any(admits(part, artifact, envelope, budget) for artifact in cost.ARTIFACTS):
                error = "over_budget"
        if error is not None:
            out.dropped.append({"label": label, "kind": kind, "params": params,
                                "artifacts": list(PITCH_ARTIFACT), "error": error})
            continue
        for artifact in PITCH_ARTIFACT:
            out.copy({"label": label, "kind": kind, "params": params, "artifact": artifact})
    out.envelope = envelope_document(envelope)
    return out


def build_pitch_walk(explore_dir: str, envelope: Envelope) -> _Set:
    """R31's walk under `envelope`, sharded by R6 from an explore run."""
    out = pitch_walk_set(envelope)
    out.sharded(charge_table(_read(explore_dir)), [f"explore={explore_dir}"])
    return out


@dataclass(frozen=True)
class PitchWall:
    """R31 for one kind: F, the reading that sets it, and W."""

    kind: str
    f: Fraction
    label: str
    w: Fraction


def r10_at_or_below(x: Fraction) -> Fraction:
    """The largest number of the ISO 3 R10 series at or below `x` (above 0)."""
    if x <= 0:
        raise ValueError(f"{x} is not above 0")
    scale = Fraction(1)
    while scale > x:
        scale /= 10
    while scale * 10 <= x:
        scale *= 10
    return max(value * scale for value in R10_SERIES if value * scale <= x)


def _d_per_pitch(params: object) -> Fraction:
    if not isinstance(params, Mapping):
        raise ProtocolStop("R31", "a walk reading carries no params")
    return _exact(float(params["d"])) / _exact(float(params["pitch"]))


def pitch_walls(points: Sequence[Mapping[str, object]],
                readings: Iterable[Reading]) -> dict[str, PitchWall]:
    """R31 per kind from the walk's readings: every point read exactly once, nothing read that the
    walk does not hold, every reading `ok`, `refused` or `crashed`. F is the smallest exact
    d / pitch of a `refused` or `crashed` reading and W the largest R10 number at or below
    F / 1.25. Anything else has no number: `ProtocolStop`."""
    wanted = {(str(p["label"]), str(p["artifact"])) for p in points}
    seen: dict[tuple[str, str], Reading] = {}
    for reading in readings:
        key = (str(reading.get("label")), str(reading.get("artifact")))
        if key not in wanted:
            raise ProtocolStop("R31", f"{key[0]} at {key[1]} is not a point of the walk")
        if key in seen:
            raise ProtocolStop("R31", f"{key[0]} at {key[1]} was read twice")
        seen[key] = reading
    missing = sorted(wanted - set(seen))
    if missing:
        raise ProtocolStop("R31", f"{len(missing)} points of the walk have no reading, the first "
                                  f"{missing[0][0]} at {missing[0][1]}")
    failing: dict[str, tuple[Fraction, str]] = {}
    for (label, _), reading in sorted(seen.items()):
        status = str(reading.get("status"))
        if status == "ok":
            continue
        if status not in FAILED:
            raise ProtocolStop("R31", f"{label} is {status}, which is cost or a gap and not a "
                                      "wall, so W has no number")
        kind, ratio = str(reading.get("kind")), _d_per_pitch(reading.get("params"))
        if kind not in failing or ratio < failing[kind][0]:
            failing[kind] = (ratio, label)
    walls: dict[str, PitchWall] = {}
    for kind in CELL_KINDS:
        if kind not in failing:
            raise ProtocolStop("R31", f"no {kind} of the walk was refused or crashed, so F and W "
                                      "have no number")
        f, label = failing[kind]
        walls[kind] = PitchWall(kind, f, label, r10_at_or_below(f / PITCH_MARGIN))
    return walls


def pitch_walls_text(walls: Mapping[str, PitchWall]) -> str:
    """One line per kind: F as the exact fraction and its float, the reading that sets it, W."""
    return "".join(f"{wall.kind}: F = {wall.f} ({float(wall.f)!r}) at {wall.label}; "
                   f"F / 1.25 = {float(wall.f / PITCH_MARGIN)!r}; W = {wall.w}\n"
                   for wall in walls.values())


# --- how far a regeneration on this host drifts from the committed files (07-18) ----------------
#
# `cost.predict` is `math.exp` of a sum of `math.log` terms, and the platform's libm decides their
# last bit: the 07-18 CI run regenerated tests/data/oper_boundary.json on the Linux runner with a
# limit of 6801399.66316881 where macOS writes 6801399.663168809, one ulp apart. A float under
# one of `PREDICTED` keys is a prediction (an edge ratio, a limit); every other value is copied
# or read from a record and must regenerate exactly.

PREDICTED = frozenset({"edge_ratio", "limit"})
# R27 (G33): how far a predicted float may move when a file is written again on another platform.
# The Linux runner moved 2 of the 2559 predicted floats of tier-order.json and the tier file by
# one ulp from the macOS files, the larger by a relative 1.459 x 2^-52; this is that rounded up to
# a whole multiple of 2^-52. Every other value regenerates exactly.
PREDICTED_REL_TOL = 2 * 2.0**-52


@dataclass(frozen=True)
class Drift:
    """One value a regeneration wrote differently: where, both values, and whether it is a
    prediction-derived float."""

    path: str
    committed: object
    fresh: object
    predicted: bool

    @property
    def relative(self) -> float:
        """|committed - fresh| / |committed| for a predicted float, else infinity."""
        a, b = self.committed, self.fresh
        if not (self.predicted and isinstance(a, float) and isinstance(b, float) and a != 0):
            return math.inf
        return abs(a - b) / abs(a)


def drifts(committed: object, fresh: object, path: str = "$",
           predicted: bool = False) -> list[Drift]:
    """Every value of two parsed JSON documents that differs, with its path. Keys, their order
    and list lengths must agree; a difference there is one drift at that path."""
    if isinstance(committed, dict) and isinstance(fresh, dict):
        if list(committed) != list(fresh):
            return [Drift(path, list(committed), list(fresh), False)]
        return [d for key in committed for d in drifts(
            committed[key], fresh[key], f"{path}.{key}", predicted or key in PREDICTED)]
    if isinstance(committed, list) and isinstance(fresh, list):
        if len(committed) != len(fresh):
            return [Drift(path, len(committed), len(fresh), False)]
        return [d for i, (a, b) in enumerate(zip(committed, fresh, strict=True))
                for d in drifts(a, b, f"{path}[{i}]", predicted)]
    if type(committed) is type(fresh) and committed == fresh:
        return []
    return [Drift(path, committed, fresh,
                  predicted and isinstance(committed, float) and isinstance(fresh, float))]


def same_but_predicted(text: str, again: str) -> bool:
    """Whether a file written again is the committed one: the same text, or the same document with
    only predicted floats moved, each by a relative difference of at most `PREDICTED_REL_TOL`."""
    if text == again:
        return True
    found = drifts(json.loads(text), json.loads(again))
    return bool(found) and all(d.predicted and d.relative <= PREDICTED_REL_TOL for d in found)


def _predicted_count(document: object, predicted: bool = False) -> int:
    if isinstance(document, dict):
        return sum(_predicted_count(value, predicted or key in PREDICTED)
                   for key, value in document.items())
    if isinstance(document, list):
        return sum(_predicted_count(value, predicted) for value in document)
    return int(predicted and isinstance(document, float))


def _regenerations() -> Iterator[tuple[Path, str, Callable[[], str]]]:
    """Every committed file `--check` and the boundary test write again, with its text and how
    to write it again on this host."""
    texts = generate()
    for name in texts:
        yield (POINTS_DIR / f"{name}.json", (POINTS_DIR / f"{name}.json").read_text(),
               functools.partial(texts.__getitem__, name))
    for path in (POINTS_DIR / f"{name}.json" for name in GENERATED):
        if path.is_file():
            yield path, path.read_text(), functools.partial(_regenerate, path)
    for name, path in (("tier-order", REPO_ROOT / TIER_ORDER),
                       *((name, POINTS_DIR / f"{name}.json") for name in (*RUNS2_SETS,
                                                                          *RERUN_SETS,
                                                                          PITCH_WALK))):
        if path.is_file():
            text = path.read_text()
            yield path, text, functools.partial(_regenerate_runs2, name, text)
    for path in _runtime_set_paths():
        if path.is_file():
            text = path.read_text()
            yield path, text, functools.partial(_regenerate_runtime_set, path, text)
    path = REPO_ROOT / BOUNDARY
    if path.is_file():
        text = path.read_text()
        explore_dir = dict(str(e).split("=", 1) for e in json.loads(text)["sources"])["explore"]
        yield path, text, functools.partial(boundary_text, explore_dir)


def prediction_drift_text() -> str:
    """Per regenerable file: exact, or how many of its predicted floats differ, the largest
    relative difference (also in units of 2^-52) and how many other values differ."""
    lines = ["file | predicted floats | differing | largest relative difference | x 2^-52 | "
             "other values differing"]
    for path, text, again in _regenerations():
        fresh = again()
        committed = json.loads(text)
        found = [] if fresh == text else drifts(committed, json.loads(fresh))
        predicted = [d for d in found if d.predicted]
        largest = max((d.relative for d in predicted), default=0.0)
        lines.append(f"{path.relative_to(REPO_ROOT).as_posix()} | {_predicted_count(committed)} "
                     f"| {len(predicted)} | {largest!r} | {largest / 2**-52!r} "
                     f"| {len(found) - len(predicted)}")
    return "\n".join(lines) + "\n"


# --- the command ---------------------------------------------------------------------------------


def generate() -> dict[str, str]:
    """The text of every point file written from code alone, by set name, in the order the files
    are checked: the four pre-registered sets and the Runs II smokes."""
    return {s.name: s.text() for s in (explore(), spread(), walls(), controls(), bound_smoke(),
                                       load_smoke())}


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


def _print_derived(result: Derived) -> None:
    """Each wall with its rule, what it rests on and the confirm one step past it (07 D-08,
    D-18)."""
    candidate = result.candidate
    print(f"MAX_TURNS = {result.max_turns}  (R7: T, the smallest first ok step over 60 cells; "
          f"{len(candidate.turn_labels)} walls and walk-down readings, then the confirm at "
          f"{result.max_turns} turns: {len(result.turn_labels)} cells x 5 repetitions, all ok)")
    print(f"  past it: {result.past['MAX_TURNS']}")
    print(f"MAX_FIELD_MM = {result.max_field_mm!r}  (R8: the ceiling value the most fields share, "
          "a tie to the lower)")
    for (kind, field), ceiling in result.ceilings.items():
        name = f"MAX_{kind.upper()}_{field.upper()}_MM"
        constant = name if name in result.constants else "MAX_FIELD_MM"
        print(f"{kind} {field}: {ceiling.value!r} mm (decade {ceiling.decade:g}, constant "
              f"{constant}); rests on {', '.join(ceiling.labels)}")
        print(f"  past it: {result.past[f'{kind} {field}']}")
    for name, value in result.constants.items():
        print(f"{name} = {value!r}")
    for (kind, field), first_refused in result.cost_limited.items():
        print(f"{kind} {field}: no constant of its own (G27: its limit is cost, first refused "
              f"decade {first_refused:g} mm); under MAX_FIELD_MM {result.max_field_mm!r}")
        print(f"  at the decade below: {result.past[f'{kind} {field}']}")
    for name, floor in (("MIN_TAIL_MM", result.tail), ("MIN_ROOT_RADIUS_MM", result.root)):
        shown = "above 0" if floor.v is None else repr(floor.v)
        rule = "R9" if name == "MIN_TAIL_MM" else "R10"
        failing = (f"{len(floor.failing)} failing, the largest value at {floor.failing[0]}"
                   if floor.failing else "none failing")
        print(f"{name} = {shown}  ({rule}: {floor.read} readings read after the confirm, "
              f"{failing})")
        if name in result.past:
            print(f"  past it: {result.past[name]}")
    for note in result.notes:
        print(f"differs from the candidate: {note}")
    if not result.notes:
        print("differs from the candidate: nowhere")


def _runs2(args: argparse.Namespace, explore_dir: str) -> None:
    """Write the Runs II files `--sets` names under the shipped envelope, `tier-order` first: the
    load mix reads the committed D(A), so D(A) is fixed before any load set exists (R27, G6)."""
    envelope, tier_path = shipped_envelope(), _relative(args.tier_order)
    out_dir = Path(args.out_dir)
    for name in args.sets:
        if name == "tier-order":
            (REPO_ROOT / tier_path).parent.mkdir(parents=True, exist_ok=True)
            (REPO_ROOT / tier_path).write_text(tier_order_text(envelope))
            print(f"tier-order: {tier_path}")
            continue
        if name == "bound":
            made = build_bound(explore_dir, envelope)
        elif name == "load":
            made = build_load(tier_path, explore_dir)
        elif name == "arenas":
            made = build_arenas(explore_dir, envelope)
        elif name == "outband":
            made = build_outband(explore_dir, envelope)
        else:
            made = build_gzip(explore_dir, envelope)
        (out_dir / f"{name}.json").write_text(made.text())
        print(f"{name}: {len(made.points)} points in shards of {made.shard_sizes}")


def _run(args: argparse.Namespace) -> int:
    walls_dir = _relative(args.walls) if hasattr(args, "walls") else ""
    explore_dir = _relative(args.explore) if hasattr(args, "explore") else ""
    down_dir = _relative(args.down) if getattr(args, "down", None) else None
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
        _print_decision(decide_walls(_read(walls_dir), _read(down_dir) if down_dir else ()))
    elif args.command == "derive-walls":
        result = derive_walls(_read(walls_dir), _read(down_dir) if down_dir else (),
                              _read(_relative(args.confirm)))
        _print_derived(result)
        if result.tail.v is None:
            # MIN_TAIL_MM is also the builder's crash guard (helical.py folds a sliver below it),
            # and no rule says what it becomes when the walk finds no failing tail.
            raise ProtocolStop("R9", "the tail floor is 'above 0', and MIN_TAIL_MM is also the "
                                     "builder's guard against a kernel crash on a float leftover: "
                                     "no rule says what it becomes, so the owner rules")
    elif args.command == "runs2":
        _runs2(args, explore_dir)
    elif args.command == "rerun":
        name = f"{args.set}-rerun"
        whole = (POINTS_DIR / f"{args.set}.json").read_text()
        made = build_rerun(name, explore_dir, _relative(args.run), _recorded_envelope(whole))
        Path(args.out).write_text(made.text())
        print(f"{name}: {len(made.points)} points in shards of {made.shard_sizes}")
    elif args.command == "envelope-check":
        _envelope_check_command(args)
    elif args.command == "prediction-drift":
        sys.stdout.write(prediction_drift_text())
    elif args.command == "boundary":
        Path(args.out).write_text(boundary_text(explore_dir))
        print(f"wrote {args.out}")
    elif args.command == "pitch-walk":
        made = build_pitch_walk(explore_dir, shipped_envelope())
        Path(args.out).write_text(made.text())
        print(f"{made.name}: {len(made.points)} points in shards of {made.shard_sizes}, "
              f"{len(made.dropped)} dropped")
    elif args.command == "pitch-walls":
        walls = pitch_walls(_points_of(PITCH_WALK), read_readings(Path(args.source)))
        sys.stdout.write(pitch_walls_text(walls))
        other = [w for w in walls.values() if w.w != RULED_PITCH_WALLS[w.kind]]
        if other:
            raise ProtocolStop("R31", "; ".join(
                f"the {w.kind} W is {w.w}, not the ruled {RULED_PITCH_WALLS[w.kind]}"
                for w in other))
    elif args.command == "load-table":
        sys.stdout.write(load_table(read_readings(Path(args.source))))
    elif args.command in ("drift", "solid-cache"):
        made = (build_drift(BOUND_POINTS, RUNTIME, args.k) if args.command == "drift"
                else build_solid_cache(LOAD_POINTS, args.k))
        Path(args.out).write_text(made.text())
        print(f"{made.name}: {len(made.points)} points in shards of {made.shard_sizes}")
    elif args.command == "check-r22-r23":
        folders = sorted(Path(d) for d in args.source)
        headers, tagged = read_runs(folders)
        sets = _runtime_sets()
        stage_one = set(runtime(headers, tagged, sets, []))
        for key, value in derivation(headers, tagged, sets, [], stage_two=True):
            if key not in stage_one:
                print(json.dumps({key: value}, indent=1))
    elif args.command == "derive-runtime":
        text = runtime_text(Path(d) for d in args.source)
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    else:
        confirm = build_confirm(walls_dir, down_dir, explore_dir)
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
                           ("confirm", "write the walls confirm set"),
                           ("derive-walls", "R3 and R7 to R10: the walls with their confirm")):
        command = sub.add_parser(name, help=helptext)
        command.add_argument("--walls", required=True)
        if name != "walk-down":
            command.add_argument("--down")
        if name == "derive-walls":
            command.add_argument("--confirm", required=True)
        elif name != "decide-walls":
            command.add_argument("--explore", required=True)
            command.add_argument("--out", required=True)
    runs2 = sub.add_parser("runs2", help="write the Runs II files from an explore run (07-15)")
    runs2.add_argument("--explore", required=True)
    runs2.add_argument("--out-dir", required=True)
    runs2.add_argument("--tier-order", default=str(REPO_ROOT / TIER_ORDER))
    runs2.add_argument("--sets", nargs="+", choices=("tier-order", *RUNS2_SETS),
                       default=["tier-order", *RUNS2_SETS])
    rerun = sub.add_parser("rerun", help="the points of a Runs II set an earlier run did not "
                                         "read (07-15, G31)")
    rerun.add_argument("--set", required=True, choices=("bound", "gzip"))
    rerun.add_argument("--explore", required=True)
    rerun.add_argument("--run", required=True)
    rerun.add_argument("--out", required=True)
    pitch_walk = sub.add_parser("pitch-walk", help="write R31's fine-pitch walk (G35)")
    pitch_walk.add_argument("--explore", required=True)
    pitch_walk.add_argument("--out", required=True)
    sub.add_parser("pitch-walls", help="R31's F and W per kind from the walk's records, exit 3 "
                                       "if a W is not the ruled one (G35)").add_argument(
        "--from", dest="source", required=True)
    sub.add_parser("load-table", help="the per-N table of a load run's readings").add_argument(
        "--from", dest="source", required=True)
    check = sub.add_parser("envelope-check",
                           help="R12 over the Runs II readings that may widen e (07-15)")
    check.add_argument("--fit", required=True)
    check.add_argument("--from", dest="source", nargs="+", required=True)
    sub.add_parser("prediction-drift", help="how far this host's regeneration of every "
                                            "committed file drifts from it (07-18)")
    boundary = sub.add_parser("boundary", help="write R27 step 5's required tier over the "
                                               "committed tier-order.json (07-18)")
    boundary.add_argument("--explore", required=True)
    boundary.add_argument("--out", required=True)
    drift_set =sub.add_parser("drift", help="write R23's drift set from runtime.json's timeouts "
                                             "(07-16)")
    drift_set.add_argument("--k", type=int, default=DRIFT_BUILDS,
                           choices=(DRIFT_BUILDS, PLATEAU_BUILDS))
    drift_set.add_argument("--out", required=True)
    solid = sub.add_parser("solid-cache", help="write R22's W(K) set (07-16)")
    solid.add_argument("--k", type=int, required=True, choices=SOLID_CACHE_KS)
    solid.add_argument("--out", required=True)
    sub.add_parser("check-r22-r23", help="R22's K, R23's arena release and drift, printed as "
                                         "they are derived (07-16)").add_argument(
        "--from", dest="source", nargs="+", required=True)
    derive = sub.add_parser("derive-runtime", help="R14 to R26: the runtime values from the "
                                                   "records (07-16)")
    derive.add_argument("--from", dest="source", nargs="+", required=True)
    derive.add_argument("--out", required=True)
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
        failure = _check_runs2() or _check_runtime_sets()
        if failure is not None:
            print(f"oper_sets: {failure}", file=sys.stderr)
            return 1
        return 0
    for name, text in texts.items():
        (POINTS_DIR / f"{name}.json").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
