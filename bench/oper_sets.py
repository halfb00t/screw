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
import sys
from collections.abc import Mapping
from decimal import ROUND_CEILING, ROUND_HALF_UP, Context, Decimal
from fractions import Fraction

from pydantic import ValidationError

from bench.oper import DEADLINE_S, POINTS_DIR
from bench.thread_spike.maths import PITCH, SAMPLE_SIZES, standard_max
from screw.calc.thread import _exact, thread_depth
from screw.params import KINDS
from screw.tables.presets import catalogue, expand, expand_nut, nut_catalogue

type Params = Mapping[str, float | bool]

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


def _refusal(kind: str, params: Params) -> str | None:
    """The pydantic error type with which the parameter model refuses `params`, or `None`."""
    try:
        KINDS[kind].model_validate(params)
    except ValidationError as exc:
        return str(exc.errors()[0]["type"])
    return None


class _Set:
    """One point file being written: the points in the order they are added, and what the model
    refused."""

    def __init__(self, name: str, *, reps: int, shards: int, notes: list[str]) -> None:
        self.name, self.reps, self.shards, self.notes = name, reps, shards, notes
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
             preset: str | None = None) -> None:
        """`params` of `kind` at each of `artifacts`, or one `dropped` entry if the model
        refuses them (the model does not look at the artifact, so a part is judged once)."""
        error = _refusal(kind, params)
        if error is not None:
            self.dropped.append({"label": label, "kind": kind, "params": dict(params),
                                 "artifacts": list(artifacts), "error": error})
            return
        for artifact in artifacts:
            point: dict[str, object] = {"label": label, "kind": kind, "params": dict(params),
                                        "artifact": artifact}
            if preset is not None:
                point["preset"] = preset
            self._add(point)

    def probe(self, label: str, probe: str, args: Params) -> None:
        self._add({"label": label, "kind": "probe", "probe": probe, "args": dict(args)})

    def text(self) -> str:
        document = {"set": self.name, "rule": RULE, "reps": self.reps, "shards": self.shards,
                    "deadline_s": DEADLINE_S, "points": self.points, "dropped": self.dropped,
                    "notes": self.notes}
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
TAIL_SIZES = ((6.0, 1.0), (2.0, 0.4), (20.0, 2.5))
TAIL_DECADES = tuple(range(2, 10))
ROOT_RADII = (1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6, 1e-6)
LEAD_IN_NUTS = (("M2", 2.0, 0.4, 12.0), ("M8", 8.0, 1.25, 38.0), ("M14", 14.0, 2.0, 46.0))
LEAD_IN_CEILINGS = (1e3, 1e4, 1e5)
COUNTERSINK_NUTS = ((0.05, 1.5), (0.05, 1.8), (0.01, 1.5))


def _turn_walls(out: _Set) -> None:
    for size, (d_exact, pitch_exact) in PITCH.items():
        d, pitch = _dec(d_exact), _dec(pitch_exact)
        for left in (False, True):
            thread = _dec(250 * pitch_exact)
            out.part(f"turns-bolt-{size}-{_hand(left)}", "bolt",
                     {"d": d, "pitch": pitch, "length": thread, "thread_length": thread,
                      "s": _scaled(d, "1.6"), "k": _scaled(d, "0.6"), "left_hand": left}, PREVIEW)
            out.part(f"turns-nut-{size}-{_hand(left)}", "nut",
                     {"d": d, "pitch": pitch, "m": _dec(248 * pitch_exact),
                      "s": _scaled(d, "1.6"), "left_hand": left}, PREVIEW)


def _ceiling_walls(out: _Set) -> None:
    for x in CEILINGS:
        tag = f"{x:g}"
        # The head rule is s > d, so with s = X the largest d is the largest value under X.
        d_max = _below(Decimal(repr(x)))
        out.part(f"ceiling-bolt-d-{tag}", "bolt",
                 {"d": d_max, "s": x, "k": _scaled(d_max, "0.6"), "thread_length": 1.0}, PREVIEW)
        out.part(f"ceiling-bolt-length-{tag}", "bolt", {"length": x}, PREVIEW)
        out.part(f"ceiling-bolt-s-{tag}", "bolt", {"s": x}, PREVIEW)
        out.part(f"ceiling-bolt-k-{tag}", "bolt", {"k": x}, PREVIEW)
        pitch = _dec(Fraction(repr(x)) / 250)
        d = _round_sig(Decimal(repr(2 * pitch)), ROUND_CEILING)
        out.part(f"ceiling-bolt-thread-{tag}", "bolt",
                 {"d": d, "pitch": pitch, "length": x, "thread_length": x,
                  "s": _scaled(d, "1.6"), "k": _scaled(d, "0.6")}, PREVIEW)
        out.part(f"ceiling-nut-s-{tag}", "nut", {"s": x}, PREVIEW)
        # Pitch rounded up so m + 2 P stays at or under 250 turns of the rounded pitch.
        nut_pitch = _round_sig(Decimal(repr(x)) / Decimal(248), ROUND_CEILING)
        nut_d = _scaled(nut_pitch, "2.5")
        out.part(f"ceiling-nut-m-{tag}", "nut",
                 {"d": nut_d, "pitch": nut_pitch, "m": x, "s": _scaled(nut_d, "1.6")}, PREVIEW)


def _tail_walls(out: _Set) -> None:
    for d, pitch in TAIL_SIZES:
        for left in (False, True):
            for decade in TAIL_DECADES:
                out.probe(f"tail-d{d:g}-p{pitch:g}-{_hand(left)}-1e-{decade}", "tail",
                          {"d": d, "pitch": pitch, "turns": 3, "tail": float(f"1e-{decade}"),
                           "left_hand": left})


def _pitch_for_root(d: float, root: float) -> float:
    """The pitch whose root radius `d/2 - thread_depth(pitch)` is `root`, to full float
    precision. Rounded to 6 figures it would be off by up to 5e-6 mm at pitch 3.7, which is
    more than the 1e-6 mm end of the walk."""
    return (d / 2 - root) / thread_depth(1.0)


def _root_walls(out: _Set) -> None:
    for size, (d_exact, _) in PITCH.items():
        d = _dec(d_exact)
        for left in (False, True):
            for root in ROOT_RADII:
                tag = f"{_hand(left)}-r{root:g}"
                pitch = _pitch_for_root(d, root)
                thread = 3 * pitch
                out.part(f"root-bolt-{size}-{tag}", "bolt",
                         {"d": d, "pitch": pitch, "length": thread, "thread_length": thread,
                          "s": _scaled(d, "1.6"), "k": _scaled(d, "0.6"), "left_hand": left},
                         PREVIEW)
                void_pitch = _pitch_for_root(d, root - DEFAULT_NUT_CLEARANCE)
                out.part(f"root-nut-{size}-{tag}", "nut",
                         {"d": d, "pitch": void_pitch, "m": 3 * void_pitch,
                          "s": _scaled(d, "1.6"), "left_hand": left}, PREVIEW)


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
        "nut clearance has no corner of its own: nut_too_thin already bounds it by s",
        "(c) tails: the `tail` probe at 3 sizes, both hands, 1e-2 down to 1e-9 mm with the "
        "builder's guard lowered in the probe only, 3 whole turns before the tail",
        "(d) root radius walk: for each size and hand, r from 1e-2 down to 1e-6 mm for the "
        "bolt (d/2 - 5H/8 = r) and the nut void (d/2 - 5H/8 + 0.15 = r); the pitch is solved to "
        "full float precision, 3 turns",
        "(e) the nuts the lead-in and countersink debt items name, at s 1e3, 1e4 and 1e5 and at "
        "the countersink item's d 2, s 4, m 3 pitches and clearances",
    ])
    _turn_walls(out)
    _ceiling_walls(out)
    _tail_walls(out)
    _root_walls(out)
    _nut_debt_walls(out)
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


# --- the command ---------------------------------------------------------------------------------


def generate() -> dict[str, str]:
    """The text of every point file, by set name, in the order the files are checked."""
    return {s.name: s.text() for s in (explore(), spread(), walls(), controls())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bench.oper_sets", description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 naming the first committed file that is not what this writes")
    args = parser.parse_args(argv)
    whole, rows = integer_turn_rows()
    print(f"integer L/P: {whole} of {rows}")
    texts = generate()
    if args.check:
        for name, text in texts.items():
            path = POINTS_DIR / f"{name}.json"
            if not path.is_file() or path.read_text() != text:
                print(f"oper_sets: {path} is not what the generator writes", file=sys.stderr)
                return 1
        return 0
    for name, text in texts.items():
        (POINTS_DIR / f"{name}.json").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
