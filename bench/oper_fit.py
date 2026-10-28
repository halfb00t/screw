"""The kernel-free cost model of phase 7, fitted to the runner records, and the candidate budget
table the owner rules on (07 D-05, D-06, D-07, D-17, Budget Q1).

Three rules of `07-SWEEP-PROTOCOL.md` are applied here and no other. R11 fixes the form: one
ordinary least-squares model per (kind, artifact, target) of the natural log of the target on the
features `features` lists, fitted on the per-point max of every `explore` and `spread` point whose
every repetition is `ok` and whose repetitions are exactly the ones its set asked for
(`bench.oper.summarize`, R3). R12 fixes the envelope: `e` is `max(0, largest actual / predicted -
1)` over the fitted points, and a part is admitted iff `prediction x (1 + e)` is at most the budget
for every bounded target. R13 fixes the three candidate budgets, C1, C2 and C3, and G10 says no
other triple is offered.

Nothing here picks a budget: `table` prints the candidates side by side with what each keeps and
refuses, and the owner rules (plan 07-10). No figure is invented: a target with too few fitted
points has no model and the fit stops naming it (L02).

Kernel-free (import-linter contract 9): the parameter model, the thread maths and the catalogue
are pure Python, and numpy is the only addition, already pinned in requirements.txt. `predict`
uses `math.exp` on a plain sum, the arithmetic `calc.cost` will ship (07-11), not numpy's.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from bench.oper import _read_records, summarize
from bench.oper_sets import ProtocolStop
from screw.calc.cost import ARTIFACTS
from screw.calc.thread import built_thread_length
from screw.params import KINDS

type Params = Mapping[str, object]

# R13's order of a budget triple, and the reading field each target is read from. `seconds` is
# the cold wall of R11, `build_s + export_s`, summed per reading before the per-point max.
TARGETS = ("bytes", "seconds", "peak")

# R11's features, in the order the coefficients follow; the intercept comes first.
FEATURES: dict[str, tuple[str, ...]] = {
    "bolt": ("ln_d", "ln_pitch", "ln_turns", "ln_length", "ln_s", "ln_k", "left_hand"),
    "nut": ("ln_d", "ln_pitch", "ln_s", "ln_m", "clearance", "left_hand"),
}

# The repetitions each fitted set asked for (R3, R4): explore reads once, spread five times.
SET_REPS: dict[str, tuple[int, ...]] = {"explore": (1,), "spread": (1, 2, 3, 4, 5)}

# R13's C2: the 16 x 10^9 bytes of D-02 in four equal shares, one per vCPU (three builds at
# N <= 3, D-03, and one for uvicorn, gzip, the caches and tmpfs).
PEAK_SHARE_BYTES = 4e9

# D-06: the fields a defaulted value can push a part over by, and the way the cap path moves
# each: a length or a height is trimmed, the pitch is raised (fewer turns).
TRIMMABLE: dict[str, tuple[tuple[str, int], ...]] = {
    "bolt": (("thread_length", -1), ("length", -1), ("pitch", 1)),
    "nut": (("m", -1), ("pitch", 1)),
}

_RUNNER_MACHINE = "x86_64"


@dataclass(frozen=True, slots=True)
class FitPoint:
    """One fitted point: a part at an artifact, with the per-point max of each target."""

    set: str
    label: str
    kind: str
    artifact: str
    params: Mapping[str, object]
    bytes: float
    seconds: float
    peak: float

    def target(self, name: str) -> float:
        return {"bytes": self.bytes, "seconds": self.seconds, "peak": self.peak}[name]


@dataclass(frozen=True, slots=True)
class Model:
    """One (kind, artifact, target) model: the intercept then one coefficient per feature."""

    kind: str
    artifact: str
    target: str
    coefficients: tuple[float, ...]
    n: int
    rank: int
    envelope: float
    envelope_set_by: str

    def as_json(self) -> dict[str, object]:
        return {"kind": self.kind, "artifact": self.artifact, "target": self.target,
                "features": ["intercept", *FEATURES[self.kind]],
                "coefficients": list(self.coefficients), "n": self.n, "rank": self.rank,
                "envelope": self.envelope, "envelope_set_by": self.envelope_set_by}

    @staticmethod
    def from_json(raw: Mapping[str, object]) -> Model:
        coefficients = raw["coefficients"]
        if not isinstance(coefficients, list):
            raise TypeError(f"a model's coefficients are not a list: {coefficients!r}")
        return Model(str(raw["kind"]), str(raw["artifact"]), str(raw["target"]),
                     tuple(float(c) for c in coefficients), _int(raw["n"]), _int(raw["rank"]),
                     float(_num(raw["envelope"])), str(raw["envelope_set_by"]))


def _int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"expected a whole number, got {value!r}")
    return value


def _num(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"expected a number, got {value!r}")
    return float(value)


def _full(kind: str, params: Params) -> dict[str, object]:
    """`params` with every field it omits at its frozen default: the spread's default parts carry
    no fields, and a link that omits one means the default (L02)."""
    fields = KINDS[kind].model_fields
    return {name: field.default for name, field in fields.items()} | dict(params)


def features(kind: str, params: Params) -> list[float]:
    """R11's features of a part, in `FEATURES[kind]` order (the intercept is the fit's)."""
    p = _full(kind, params)
    d, pitch = _num(p["d"]), _num(p["pitch"])
    hand = 1.0 if p["left_hand"] is True else 0.0
    if kind == "bolt":
        length = _num(p["length"])
        # The thread the builder makes, over the pitch: the turns the builder sweeps (D-17).
        turns = built_thread_length(_num(p["thread_length"]), length) / pitch
        return [math.log(d), math.log(pitch), math.log(turns), math.log(length),
                math.log(_num(p["s"])), math.log(_num(p["k"])), hand]
    if kind == "nut":
        return [math.log(d), math.log(pitch), math.log(_num(p["s"])), math.log(_num(p["m"])),
                _num(p["clearance"]), hand]
    raise ValueError(f"no cost model for kind {kind!r}")


def predict(model: Model, params: Params) -> float:
    """The model's prediction of its target for a part, before the envelope."""
    z = model.coefficients[0]
    for coefficient, x in zip(model.coefficients[1:], features(model.kind, params), strict=True):
        z += coefficient * x
    return math.exp(z)


def enveloped(model: Model, params: Params) -> float:
    """`prediction x (1 + e)`, the figure R12 compares with the budget."""
    return predict(model, params) * (1.0 + model.envelope)


def admit(pred: float, e: float, budget: float | None) -> bool:
    """R12 for one target: admitted iff `pred x (1 + e)` is at most the budget; at it is admitted,
    one float above it is refused. No budget (an unbounded component) admits."""
    return budget is None or pred * (1.0 + e) <= budget


def envelope(model: Model, points: Iterable[FitPoint]) -> tuple[float, str]:
    """R12's `e` over the fitted points, and the label of the point that set it.

    `max(0, ratio - 1)` multiplied back can land one ulp under the actual it came from, so the
    factor `1 + e` is raised by single ulps until `prediction x (1 + e)` is at least every actual:
    the guarantee the envelope exists for holds in the float arithmetic admission uses. The ulps
    are the factor's, not `e`'s: `e`'s own next float above 0 is 5e-324, which leaves `1 + e`
    at 1."""
    sample = [(p, p.target(model.target), predict(model, p.params)) for p in points]
    worst = max(sample, key=lambda item: item[1] / item[2])
    factor = max(1.0, worst[1] / worst[2])
    while any(pred * (1.0 + (factor - 1.0)) < actual for _, actual, pred in sample):
        factor = math.nextafter(factor, math.inf)
    e = factor - 1.0
    return e, f"{worst[0].set}:{worst[0].label}" if e > 0 else ""


def fit(points: Sequence[FitPoint]) -> list[Model]:
    """One model per (kind, artifact, target), with its envelope (R11, R12).

    A (kind, artifact, target) with fewer fitted points than coefficients + 1 has no model: the
    fit stops naming it (L02, no number)."""
    models: list[Model] = []
    for kind in FEATURES:
        for artifact in ARTIFACTS:
            sample = [p for p in points if p.kind == kind and p.artifact == artifact]
            need = len(FEATURES[kind]) + 2
            for target in TARGETS:
                if len(sample) < need:
                    raise ProtocolStop("R11", f"{kind} {artifact} {target}: {len(sample)} fitted "
                                              f"points, {need} needed for a model")
                x = np.array([[1.0, *features(kind, p.params)] for p in sample])
                y = np.array([math.log(p.target(target)) for p in sample])
                coef, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
                draft = Model(kind, artifact, target, tuple(float(c) for c in coef), len(sample),
                              int(rank), 0.0, "")
                e, by = envelope(draft, sample)
                models.append(Model(kind, artifact, target, draft.coefficients, len(sample),
                                    int(rank), e, by))
    return models


def fit_points(explore: Sequence[Mapping[str, object]], spread: Sequence[Mapping[str, object]]
               ) -> tuple[list[FitPoint], list[dict[str, object]]]:
    """The fit input and the excluded points (R3, R11).

    Each set is summarized with its own expected repetitions, so a point with any repetition that
    is not `ok`, or with repetitions that are not exactly its set's (four of five, one read twice),
    has no max and is excluded, listed with its statuses and its repetitions. The cold wall is
    summed per reading before the per-point max."""
    points: list[FitPoint] = []
    excluded: list[dict[str, object]] = []
    for name, readings in (("explore", explore), ("spread", spread)):
        groups: dict[tuple[object, object], list[Mapping[str, object]]] = {}
        for reading in readings:
            groups.setdefault((reading["label"], reading["artifact"]), []).append(reading)
        for row in summarize(readings, SET_REPS[name]):
            group = groups[row["label"], row["artifact"]]
            kind = str(group[0]["kind"])
            maximum = row["max"]
            if row["status"] != "ok" or not isinstance(maximum, dict):
                excluded.append({"set": name, "label": row["label"], "kind": kind,
                                 "artifact": row["artifact"], "status": row["status"],
                                 "counts": row["counts"], "reps": row["reps"]})
                continue
            params = group[0]["params"]
            if not isinstance(params, dict):
                raise TypeError(f"{row['label']}: params are not an object")
            seconds = max(_num(r["build_s"]) + _num(r["export_s"]) for r in group)
            points.append(FitPoint(name, str(row["label"]), kind, str(row["artifact"]), params,
                                   float(maximum["bytes"]), seconds,
                                   float(maximum["memory_peak_bytes"])))
    return points, excluded


def load_set(name: str, directories: Sequence[Path]) -> tuple[list[str], list[dict[str, object]]]:
    """The run ids and readings of one set's downloaded records.

    Only a runner record is taken (R1): every file is a `measure` job's `oper-<set>-` JSONL whose
    header names an `x86_64` machine and a GitHub run id, so a macOS or emulated run, a smoke set
    or a hand-written file is refused, never fitted."""
    run_ids: set[str] = set()
    readings: list[dict[str, object]] = []
    for directory in directories:
        files = sorted(directory.glob("*/*.jsonl"))
        if not files:
            raise ValueError(f"no *.jsonl records under {directory}")
        for path in files:
            if not path.name.startswith(f"oper-{name}-"):
                raise ValueError(f"{path}: not a record of the {name} set")
            headers, found = _read_records([str(path)])
            if len(headers) != 1:
                raise ValueError(f"{path}: {len(headers)} headers, expected 1")
            head = headers[0]
            run = head.get("GITHUB_RUN_ID")
            if head.get("machine") != _RUNNER_MACHINE or not isinstance(run, str) or not run:
                raise ValueError(f"{path}: not a linux/amd64 runner record (machine "
                                 f"{head.get('machine')!r}, run {run!r})")
            for reading in found:
                if reading.get("kind") not in FEATURES or reading.get("lift") is not None:
                    raise ValueError(f"{path}: {reading.get('label')} is not a part reading")
            run_ids.add(run)
            readings += found
    return sorted(run_ids), readings


def fit_document(explore_dirs: Sequence[Path], spread_dirs: Sequence[Path]) -> dict[str, object]:
    """fit.json: the models, the excluded points, the fitted counts and the run ids (D-05, D-17)."""
    explore_runs, explore = load_set("explore", explore_dirs)
    spread_runs, spread = load_set("spread", spread_dirs)
    points, excluded = fit_points(explore, spread)
    return {"rules": "R11 and R12 of 07-SWEEP-PROTOCOL.md",
            "run_ids": {"explore": explore_runs, "spread": spread_runs},
            "fitted": {name: sum(1 for p in points if p.set == name) for name in SET_REPS},
            "models": [m.as_json() for m in fit(points)], "excluded": excluded}


def models_of(document: Mapping[str, object]) -> dict[tuple[str, str, str], Model]:
    raw = document["models"]
    if not isinstance(raw, list):
        raise TypeError("fit.json has no models list")
    models = [Model.from_json(m) for m in raw]
    return {(m.kind, m.artifact, m.target): m for m in models}


def _dump(document: Mapping[str, object]) -> str:
    # Sorted keys and `repr` floats (json's own), so the same records write the same bytes.
    return json.dumps(document, sort_keys=True, indent=1, allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bench.oper_fit", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_fit = sub.add_parser("fit", help="fit the models and write fit.json")
    p_fit.add_argument("--explore", nargs="+", type=Path, required=True)
    p_fit.add_argument("--spread", nargs="+", type=Path, required=True)
    p_fit.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        text = _dump(fit_document(args.explore, args.spread))
    except ProtocolStop as exc:
        print(f"oper_fit: the phase stops for the owner {exc}", file=sys.stderr)
        return 3
    except (OSError, TypeError, ValueError) as exc:
        print(f"oper_fit: {exc}", file=sys.stderr)
        return 2
    if args.out == "-":
        sys.stdout.write(text)
    else:
        Path(args.out).write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
