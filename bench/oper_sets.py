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
import functools
import json
import random
import statistics
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
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
    the envelope and the budget given rather than shipped."""
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


def bound_sets(points: Sequence[Mapping[str, object]], readings: Iterable[Reading],
               envelope: Envelope, budget: Budget = cost.BUDGET) -> dict[str, list[Candidate]]:
    """R14's bound set per artifact: the 5 admitted points with the largest enveloped build-seconds
    prediction, the largest measured cold wall among ok explore readings, the largest enveloped
    peak prediction and the largest measured `memory_peak_bytes` among ok readings, a point in
    two groups once, so 5 to 8 points, in that order."""
    index = _explore_index(readings)
    out: dict[str, list[Candidate]] = {}
    for artifact in cost.ARTIFACTS:
        found = candidates(points, artifact, envelope, budget)
        measured = [c for c in found if _ok(index, c.label, artifact) is not None]
        if not measured:
            raise ProtocolStop("R14", f"no admitted point at {artifact} has an ok explore reading, "
                                      "so the measured extrema have no point")

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
                 _largest(measured, lambda c: _number(reading(c), "build_s")
                          + _number(reading(c), "export_s")),
                 _largest(found, peak),
                 _largest(measured, lambda c: _number(reading(c), "memory_peak_bytes"))]
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
    slot (`hash(p) % N`, `pool_slot`) and, on every slot P does not hold, the admitted point
    other than P on that slot with the largest enveloped build-seconds prediction, a tie to the
    label. A slot no admitted point holds is a stop: no rule puts two points on one worker."""
    bound = bound_sets(points, readings, envelope, budget)
    out: list[dict[str, object]] = []
    for artifact in cost.ARTIFACTS:
        found = candidates(points, artifact, envelope, budget)
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
                                                  f"admitted point is on slot {slot}, so the "
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
    return _runs2_set("bound", "07-SWEEP-PROTOCOL.md R14 (G4, G6, G24)", [
        "per artifact the bound set: the 5 admitted explore points with the largest enveloped "
        "build-seconds prediction, the largest measured cold wall and the largest measured "
        "memory_peak_bytes among ok explore readings, and the largest enveloped peak prediction, "
        "a tie to the label that sorts first, a point in two groups once",
        "each bound point P at N 1, 2 and 3: P on slot hash(p) % N and, on every other slot, the "
        "admitted point other than P on that slot with the largest enveloped build-seconds "
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
    return _runs2_set("gzip", "07-SWEEP-PROTOCOL.md R19 (G11, G15, G24)", [
        "every point of the stl-preview and stl-fine bound sets (R14), read as a part with "
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
             "arenas": ("explore",), "outband": ("explore",)}[name]
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
    return build_gzip(sources["explore"], envelope).text()


def _check_runs2() -> str | None:
    """The first Runs II file that is not what its generator writes under its recorded envelope,
    with the reason, or None. Absent files are not checked: each is written by its own step."""
    paths = [("tier-order", REPO_ROOT / TIER_ORDER),
             *((name, POINTS_DIR / f"{name}.json") for name in RUNS2_SETS)]
    for name, path in paths:
        if not path.is_file():
            continue
        text = path.read_text()
        try:
            same = text == _regenerate_runs2(name, text)
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
    elif args.command == "load-table":
        sys.stdout.write(load_table(read_readings(Path(args.source))))
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
    sub.add_parser("load-table", help="the per-N table of a load run's readings").add_argument(
        "--from", dest="source", required=True)
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
        failure = _check_runs2()
        if failure is not None:
            print(f"oper_sets: {failure}", file=sys.stderr)
            return 1
        return 0
    for name, text in texts.items():
        (POINTS_DIR / f"{name}.json").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
