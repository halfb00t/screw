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
import itertools
import json
import math
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np
from pydantic import ValidationError

from bench import oper_lift
from bench.oper import _read_records, summarize
from bench.oper_sets import ProtocolStop
from screw.calc.cost import ARTIFACTS
from screw.calc.thread import MAX_TURNS, MIN_ROOT_RADIUS_MM, MIN_TAIL_MM, built_thread_length
from screw.params import (
    KINDS,
    MAX_BOLT_D_MM,
    MAX_BOLT_K_MM,
    MAX_BOLT_LENGTH_MM,
    MAX_BOLT_THREAD_LENGTH_MM,
    MAX_FIELD_MM,
    MAX_NUT_CLEARANCE_MM,
    MAX_NUT_M_MM,
)
from screw.tables.presets import catalogue, nut_catalogue

type Params = Mapping[str, object]
type Triple = tuple[float | None, float | None, float | None]
type Bands = Mapping[tuple[str, str], tuple[float, float]]

# R13's order of a budget triple, and the reading field each target is read from. `seconds` is
# the cold wall of R11, `build_s + export_s`, summed per reading before the per-point max.
TARGETS = ("bytes", "seconds", "peak")

# R11's features, in the order the coefficients follow; the intercept comes first.
FEATURES: dict[str, tuple[str, ...]] = {
    "bolt": ("ln_d", "ln_pitch", "ln_turns", "ln_length", "ln_s", "ln_k", "left_hand"),
    "nut": ("ln_d", "ln_pitch", "ln_s", "ln_m", "clearance", "left_hand"),
}

# G28's head ratios, each a field over d. The fitted points hold each in a narrow band (bolt k/d
# 0.6 to 0.7), so a coefficient can say a taller head is cheaper (`ln_k` is negative on every bolt
# model): outside its band a ratio is predicted no lower than anywhere in the band (R11).
RATIOS: dict[str, tuple[str, ...]] = {"bolt": ("k", "s"), "nut": ("s", "m")}

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


def head_bands(points: Iterable[FitPoint]) -> dict[tuple[str, str], tuple[float, float]]:
    """G28: each head ratio's [min, max] over the fitted points of its kind, an omitted field at
    its frozen default, as `features` reads it. `emit-constants` ships these as `cost.BANDS`."""
    full = [(p.kind, _full(p.kind, p.params)) for p in points]
    found: dict[tuple[str, str], tuple[float, float]] = {}
    for kind, fields in RATIOS.items():
        for field in fields:
            ratios = [_num(q[field]) / _num(q["d"]) for k, q in full if k == kind]
            found[kind, field] = (min(ratios), max(ratios))
    return found


def min_turns(points: Iterable[FitPoint]) -> float:
    """B-03's floor (second clarification, 2026-10-29): the fewest built-thread turns over the
    fitted bolt points, each read with its omitted fields at their frozen defaults, the turns
    `features` takes the log of. `emit-constants` ships it as `cost.MIN_FITTED_TURNS`."""
    turns = []
    for p in points:
        if p.kind == "bolt":
            q = _full("bolt", p.params)
            turns.append(built_thread_length(_num(q["thread_length"]), _num(q["length"]))
                         / _num(q["pitch"]))
    return min(turns)


def edges(kind: str, params: Params, bands: Bands) -> list[dict[str, float]]:
    """G28: every combination of band edges of the part's out-of-band head ratios, as the fields
    each sets (edge x d, every other field held); empty when every ratio is in its band. A ratio
    above its band takes both edges, one below it the low edge only (ruling 5): a smaller head is
    assumed, unmeasured, never to cost more than one at the low edge."""
    full = _full(kind, params)
    d = _num(full["d"])
    out: list[tuple[str, tuple[float, ...]]] = []
    for (k, field), (low, high) in bands.items():
        ratio = _num(full[field]) / d if k == kind else low
        if ratio > high:
            out.append((field, (low * d, high * d)))
        elif ratio < low:
            out.append((field, (low * d,)))
    if not out:
        return []
    names = [field for field, _ in out]
    return [dict(zip(names, combo, strict=True))
            for combo in itertools.product(*(values for _, values in out))]


def _raw(model: Model, params: Params) -> float:
    z = model.coefficients[0]
    for coefficient, x in zip(model.coefficients[1:], features(model.kind, params), strict=True):
        z += coefficient * x
    return math.exp(z)


def predict(model: Model, params: Params, bands: Bands | None = None) -> float:
    """The model's prediction of its target for a part, before the envelope.

    With `bands` (G28), a part with a head ratio outside its band is predicted as the largest of
    the raw prediction and the one at every combination of the `edges`: above the band, for this
    log-linear model, the largest anywhere in the band; below it, max(raw, low edge). Inside every
    band, and with no bands (the fit and its envelope, whose points are the bands), it is the raw
    prediction."""
    value = _raw(model, params)
    for moved in edges(model.kind, params, bands or {}):
        value = max(value, _raw(model, _full(model.kind, params) | moved))
    return value


def enveloped(model: Model, params: Params, bands: Bands | None = None) -> float:
    """`prediction x (1 + e)`, the figure R12 compares with the budget."""
    return predict(model, params, bands) * (1.0 + model.envelope)


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


# --- the candidate table (R13, D-06) ----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Part:
    """A part the table judges: a catalogue row or an explore free-space point, at an artifact."""

    label: str
    kind: str
    artifact: str
    params: Mapping[str, object]
    catalogue: bool


def _catalogue_parts(artifact: str) -> list[Part]:
    return ([Part(row.id, "bolt", artifact, dict(row.fields), True) for row in catalogue()]
            + [Part(row.id, "nut", artifact, dict(row.fields), True) for row in nut_catalogue()])


def admitted(models: Mapping[tuple[str, str, str], Model], part: Part, budget: Triple,
             bands: Bands | None = None) -> bool:
    """R12 over every target of a part's kind at its artifact (G28 with `bands`)."""
    return all(admit(predict(models[part.kind, part.artifact, t], part.params, bands),
                     models[part.kind, part.artifact, t].envelope, b)
               for t, b in zip(TARGETS, budget, strict=True))


def within_walls(kind: str, params: Params) -> bool:
    """Whether the parameter model (the walls of L20 and every validator) takes the part, as the
    budget table B-01 ruled on saw it: without R31's fine-pitch wall, which came after (G36)."""
    try:
        oper_lift.drawn(kind, params)
    except ValidationError:
        return False
    return True


def c3_basis(points: Sequence[FitPoint]) -> FitPoint:
    """R13's rho point: the `stl-fine` point with the largest raw bytes among the explore and
    spread points whose every repetition is ok (the fit input), a tie to the label first."""
    fine = [p for p in points if p.artifact == "stl-fine"]
    if not fine:
        raise ProtocolStop("R13", "no stl-fine point is ok in every repetition, so rho has no "
                                  "number")
    return min(fine, key=lambda p: (-p.bytes, p.label, p.set))


def candidates(document: Mapping[str, object], points: Sequence[FitPoint]
               ) -> dict[str, dict[str, Triple]]:
    """R13's three candidates per artifact as (bytes, seconds, peak), None for an unbounded
    component, and nothing else (G10)."""
    models = models_of(document)
    ruled = head_bands(points)
    c1: dict[str, Triple] = {}
    for artifact in ARTIFACTS:
        parts = _catalogue_parts(artifact)
        top = [max(enveloped(models[p.kind, artifact, t], p.params, ruled) for p in parts)
               for t in TARGETS]
        c1[artifact] = (top[0], top[1], top[2])
    basis = c3_basis(points)
    q = PEAK_SHARE_BYTES / (basis.peak / basis.bytes)
    return {
        "C1": c1,
        "C2": dict.fromkeys(ARTIFACTS, (None, None, PEAK_SHARE_BYTES)),
        "C3": {a: (q, None, None) if a == "stl-fine" else (None, None, None) for a in ARTIFACTS},
    }


def _stepped(value: float, step: float, n: int) -> float:
    # Decimal steps, so 20 - 3 x 0.5 is 18.5 and not 18.499999999999996: the value a form
    # stepping from the default would send.
    return float(Decimal(repr(value)) + n * Decimal(repr(step)))


def d06_trim(models: Mapping[tuple[str, str, str], Model], part: Part, budget: Triple,
             bands: Bands | None = None) -> str:
    """D-06's evidence for one refused part: for each trimmable field at its frozen default, the
    first value on its form step (a length or height trimmed, the pitch raised) that the walls and
    the budget admit, or that none does; `explicit only` when no such field is at its default."""
    fields = KINDS[part.kind].model_fields
    steps = KINDS[part.kind].model_json_schema()["properties"]
    full = _full(part.kind, part.params)
    found: list[str] = []
    for name, direction in TRIMMABLE[part.kind]:
        default = fields[name].default
        if full[name] != default:
            continue
        step = float(steps[name]["step"])
        n = 1
        result = f"{name}: no admitting value"
        while (value := _stepped(default, step, direction * n)) > 0:
            trial = Part(part.label, part.kind, part.artifact, full | {name: value},
                         part.catalogue)
            if not within_walls(part.kind, trial.params):
                break
            if admitted(models, trial, budget, bands):
                result = f"{name}: admits at {value!r}"
                break
            n += 1
        found.append(result)
    return "; ".join(found) if found else "explicit only"


def _explore_parts(explore: Sequence[Mapping[str, object]]) -> dict[str, list[Part]]:
    ids = {row.id for row in catalogue()} | {row.id for row in nut_catalogue()}
    parts: dict[str, list[Part]] = {a: [] for a in ARTIFACTS}
    seen: set[tuple[str, str]] = set()
    for reading in explore:
        label, artifact = str(reading["label"]), str(reading["artifact"])
        params = reading["params"]
        if label in ids or (label, artifact) in seen or not isinstance(params, dict):
            continue
        seen.add((label, artifact))
        parts[artifact].append(Part(label, str(reading["kind"]), artifact, params, False))
    return parts


def _fmt(value: float | None) -> str:
    return "unbounded" if value is None else repr(value)


def _g(value: float | None) -> str:
    return "-" if value is None else f"{value:.6g}"


def table(document: Mapping[str, object], points: Sequence[FitPoint],
          explore: Sequence[Mapping[str, object]], fit_path: str) -> str:
    """`07-BUDGET-TABLE.md`: the three candidates of R13, each with what it keeps and refuses, and
    the D-06 evidence. Plain text; the code writes no recommendation."""
    models = models_of(document)
    ruled = head_bands(points)
    cands = candidates(document, points)
    free = _explore_parts(explore)
    readings: dict[tuple[str, str], Mapping[str, object]] = {
        (str(r["label"]), str(r["artifact"])): r for r in explore}
    runs = document["run_ids"]
    if not isinstance(runs, dict):
        raise TypeError("fit.json has no run ids")
    basis = c3_basis(points)
    rho = basis.peak / basis.bytes
    lines = [
        "# Phase 7 candidate budget table (R13, D-06)", "",
        f"Generated by `python -m bench.oper_fit table` from `{fit_path}` and the committed "
        "records; not edited by hand. Regenerating it must give the same bytes.", "",
        f"Runs: explore {', '.join(runs['explore'])}, spread {', '.join(runs['spread'])} "
        "(linux/amd64 GitHub runners, `bench/RESULTS.md`).", "",
        f"Walls (L20): MAX_TURNS {MAX_TURNS}, MAX_FIELD_MM {MAX_FIELD_MM!r}, MAX_BOLT_D_MM "
        f"{MAX_BOLT_D_MM!r}, MAX_BOLT_LENGTH_MM {MAX_BOLT_LENGTH_MM!r}, MAX_BOLT_K_MM "
        f"{MAX_BOLT_K_MM!r}, MAX_BOLT_THREAD_LENGTH_MM {MAX_BOLT_THREAD_LENGTH_MM!r}, "
        f"MAX_NUT_M_MM {MAX_NUT_M_MM!r}, MAX_NUT_CLEARANCE_MM {MAX_NUT_CLEARANCE_MM!r}, "
        f"MIN_TAIL_MM {MIN_TAIL_MM!r}, MIN_ROOT_RADIUS_MM {MIN_ROOT_RADIUS_MM!r} (a rod floor, "
        "G26). A part the parameter model refuses is a 422 under every candidate and is counted "
        "as refused by the walls.", "",
        "Admission (R12): a part is admitted iff prediction x (1 + e) is at most the component for "
        "every bounded component; at the budget is admitted, one float above is refused. "
        "Components are (raw bytes, cold build seconds = build_s + export_s, cgroup peak bytes).",
        "", "## Envelopes", "",
        "| kind | artifact | target | fitted points | rank | e | set by |",
        "| --- | --- | --- | --- | --- | --- | --- |"]
    lines += [f"| {m.kind} | {m.artifact} | {m.target} | {m.n} | {m.rank} | {m.envelope!r} | "
              f"{m.envelope_set_by or '-'} |" for m in models.values()]
    lines += ["", f"C3's rho: `stl-fine` point `{basis.set}:{basis.label}` ({basis.kind}), "
              f"per-point max raw bytes {basis.bytes!r}, per-point max cgroup peak {basis.peak!r}, "
              f"rho {rho!r}, Q = {PEAK_SHARE_BYTES!r} / rho = {PEAK_SHARE_BYTES / rho!r} bytes."]
    titles = {"C1": "catalogue-complete", "C2": "memory-bound", "C3": "bytes-bound"}
    for name, per_artifact in cands.items():
        lines += ["", f"## {name}, {titles[name]}", "",
                  "| artifact | budget (bytes, seconds, peak) | bolt catalogue kept / refused of "
                  f"{len(catalogue())} | nut catalogue kept / refused of {len(nut_catalogue())} "
                  "| free space admitted / refused by budget / refused by walls | predicted worst "
                  "s, bytes, peak (enveloped) | measured worst s, bytes, peak (admitted, ok) | "
                  "admitted with a non-ok explore reading |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        refused_rows: dict[str, list[str]] = {}
        d06: list[tuple[Part, str]] = []
        explicit = 0
        for artifact in ARTIFACTS:
            budget = per_artifact[artifact]
            kept: dict[str, list[int]] = {"bolt": [0, 0], "nut": [0, 0]}
            free_counts = [0, 0, 0]
            worst_pred = [0.0, 0.0, 0.0]
            worst_meas: list[float | None] = [None, None, None]
            non_ok: dict[str, int] = {}
            population = _catalogue_parts(artifact) + free[artifact]
            for part in population:
                if not within_walls(part.kind, part.params):
                    if part.catalogue:
                        kept[part.kind][1] += 1
                        refused_rows.setdefault(artifact, []).append(f"{part.label} (walls)")
                    else:
                        free_counts[2] += 1
                    continue
                ok = admitted(models, part, budget, ruled)
                if part.catalogue:
                    kept[part.kind][0 if ok else 1] += 1
                    if not ok:
                        refused_rows.setdefault(artifact, []).append(part.label)
                else:
                    free_counts[0 if ok else 1] += 1
                if not ok:
                    trim = d06_trim(models, part, budget, ruled)
                    if trim == "explicit only":
                        explicit += 1
                    else:
                        d06.append((part, trim))
                    continue
                for i, t in enumerate(TARGETS):
                    worst_pred[i] = max(worst_pred[i],
                                        enveloped(models[part.kind, artifact, t], part.params,
                                                  ruled))
                reading = readings.get((part.label, artifact))
                if reading is None:
                    continue
                if reading["status"] != "ok":
                    status = str(reading["status"])
                    non_ok[status] = non_ok.get(status, 0) + 1
                    continue
                measured = (_num(reading["bytes"]),
                            _num(reading["build_s"]) + _num(reading["export_s"]),
                            _num(reading["memory_peak_bytes"]))
                worst_meas = [m if w is None else max(w, m)
                              for w, m in zip(worst_meas, measured, strict=True)]
            lines.append(
                f"| {artifact} | ({', '.join(_fmt(b) for b in budget)}) "
                f"| {kept['bolt'][0]} / {kept['bolt'][1]} | {kept['nut'][0]} / {kept['nut'][1]} "
                f"| {free_counts[0]} / {free_counts[1]} / {free_counts[2]} "
                f"| {_g(worst_pred[1])} s, {_g(worst_pred[0])} B, {_g(worst_pred[2])} B "
                f"| {_g(worst_meas[1])} s, {_g(worst_meas[0])} B, {_g(worst_meas[2])} B "
                f"| {sum(non_ok.values())}"
                + "".join(f", {s} {n}" for s, n in sorted(non_ok.items())) + " |")
        lines += ["", f"### {name}: D-06 evidence", "",
                  "Refused points (catalogue and free space, inside the walls) with a bolt "
                  "`thread_length` or `length`, a nut `m`, or a `pitch` at its frozen default, and "
                  "the first value on the field's form step that the walls and this candidate "
                  "admit.", ""]
        if d06:
            lines += ["| point | kind | artifact | trim |", "| --- | --- | --- | --- |"]
            lines += [f"| {p.label} | {p.kind} | {p.artifact} | {trim} |" for p, trim in d06]
        else:
            lines.append("No refused point has such a field at its default.")
        lines += ["", f"Refused points with no such field at its default (explicit only): "
                  f"{explicit}.", "", f"### {name}: refused catalogue rows", ""]
        if refused_rows:
            lines += [f"- {a}: {', '.join(ids)}" for a, ids in refused_rows.items()]
        else:
            lines.append("None.")
    return "\n".join(lines) + "\n"


# --- the constants `calc.cost` ships (07-11) ----------------------------------------------------

EMIT_BEGIN = ("# BEGIN emit-constants: `python -m bench.oper_fit emit-constants`; not edited "
              "by hand.")
EMIT_END = "# END emit-constants"

# B-01's budget rows in `07-OWNER-RULINGS.md`: `| <artifact> | (<bytes>, <seconds>, <peak>) |`.
_BUDGET_ROW = re.compile(r"^\| (stl-preview|stl-fine|step) \| \(([^)]*)\) \|$", re.MULTILINE)


def ruled_budget(rulings: str) -> tuple[str, dict[str, Triple]]:
    """B-01's date and its per-artifact (bytes, seconds, peak) triples, read from the rulings file
    as the owner's table prints them, so the shipped budget is the ruled one and no other (G10).
    `unbounded` reads as None."""
    date = re.search(r"^Date: (\d{4}-\d{2}-\d{2})", rulings, re.MULTILINE)
    section = re.search(r"^## B-01\b(.*?)(?=^## )", rulings, re.MULTILINE | re.DOTALL)
    if date is None or section is None:
        raise ValueError("the rulings file has no Date line or no B-01 section")
    budget: dict[str, Triple] = {}
    for artifact, cells in _BUDGET_ROW.findall(section.group(1)):
        values = [None if c.strip() == "unbounded" else float(c) for c in cells.split(",")]
        if len(values) != len(TARGETS) or artifact in budget:
            raise ValueError(f"B-01: a malformed or repeated row for {artifact}")
        budget[artifact] = (values[0], values[1], values[2])
    if sorted(budget) != sorted(ARTIFACTS):
        raise ValueError(f"B-01 rules {sorted(budget)}, not every artifact {sorted(ARTIFACTS)}")
    return date.group(1), budget


def _wrapped(head: str, items: Sequence[str], tail: str) -> list[str]:
    # Greedy, so the block stays under ruff's 100 columns (L05: ruff never reformats it).
    lines, line = [], head
    for n, item in enumerate(items):
        piece = item + ("," if n < len(items) - 1 else tail)
        if len(line) + len(piece) + 1 > 99:
            lines.append(line)
            line = "        " + piece
        else:
            line += ("" if line.endswith("(") else " ") + piece
    return [*lines, line]


def emit_constants(document: Mapping[str, object], rulings: str, bands: Bands,
                   turns: float) -> str:
    """The Python block `calc/cost.py` carries between `EMIT_BEGIN` and `EMIT_END`: the
    coefficients and envelopes of fit.json, G28's head-ratio bands and B-03's turns floor of the
    records fit.json was fitted on, and B-01's budget, floats written with `repr`, so the shipped
    numbers are generated from their evidence, never typed (D-05, D-07, G28, B-03)."""
    models = models_of(document)
    runs = document["run_ids"]
    if not isinstance(runs, dict):
        raise TypeError("fit.json has no run ids")
    widened = document.get("widened_by", [])
    if not isinstance(widened, list):
        raise TypeError("fit.json's widened_by is not a list")
    date, budget = ruled_budget(rulings)
    source = (f"# fit.json, runs explore {', '.join(runs['explore'])} and spread "
              f"{', '.join(runs['spread'])}.")
    lines = [EMIT_BEGIN,
             "# R11's least squares: the intercept, then one coefficient per `FEATURES[kind]`.",
             source,
             "COEFFICIENTS: Final[Mapping[ModelKey, tuple[float, ...]]] = MappingProxyType({"]
    for (kind, artifact, target), m in models.items():
        lines += _wrapped(f'    ("{kind}", "{artifact}", "{target}"): (',
                          [repr(c) for c in m.coefficients], "),")
    lines += ["})", "# R12's envelope e per model.", source]
    lines += [f"# Widened by run {r} (R12)." for r in widened]
    lines += ["ENVELOPE: Final[Mapping[ModelKey, float]] = MappingProxyType({"]
    lines += [f'    ("{k}", "{a}", "{t}"): {m.envelope!r},' for (k, a, t), m in models.items()]
    lines += ["})",
              "# G28's band of each head ratio, field / d: its [min, max] over the fitted",
              "# points of its kind, an omitted field at its default (R11).",
              f"# The records of runs explore {', '.join(runs['explore'])} and spread "
              f"{', '.join(runs['spread'])}.",
              "BANDS: Final[Mapping[tuple[str, str], tuple[float, float]]] = MappingProxyType({"]
    lines += [f'    ("{kind}", "{field}"): ({low!r}, {high!r}),'
              for (kind, field), (low, high) in bands.items()]
    lines += ["})",
              "# B-03's second clarification: the fewest built-thread turns, built thread over",
              "# the pitch, over the fitted bolt points, an omitted field at its default (R11).",
              f"# The records of runs explore {', '.join(runs['explore'])} and spread "
              f"{', '.join(runs['spread'])}.",
              f"MIN_FITTED_TURNS: Final[float] = {turns!r}",
              f"# B-01 of 07-OWNER-RULINGS.md ({date}): C1 of R13, catalogue-complete.",
              "# (raw bytes, cold build seconds, cgroup peak bytes); None is unbounded.",
              "BUDGET: Final[Mapping[Artifact, Budget]] = MappingProxyType({"]
    for artifact in ARTIFACTS:
        lines += _wrapped(f'    "{artifact}": (', [repr(v) for v in budget[artifact]], "),")
    return "\n".join([*lines, "})", EMIT_END]) + "\n"


def _dump(document: Mapping[str, object]) -> str:
    # Sorted keys and `repr` floats (json's own), so the same records write the same bytes.
    return json.dumps(document, sort_keys=True, indent=1, allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bench.oper_fit", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_fit = sub.add_parser("fit", help="fit the models and write fit.json")
    p_table = sub.add_parser("table", help="write the candidate budget table")
    for p in (p_fit, p_table):
        p.add_argument("--explore", nargs="+", type=Path, required=True)
        p.add_argument("--spread", nargs="+", type=Path, required=True)
        p.add_argument("--out", required=True)
    p_table.add_argument("--fit", required=True)
    p_emit = sub.add_parser("emit-constants", help="print the constants calc/cost.py ships")
    p_emit.add_argument("--fit", required=True)
    p_emit.add_argument("--rulings", required=True)
    p_emit.add_argument("--explore", nargs="+", type=Path, required=True)
    p_emit.add_argument("--spread", nargs="+", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "emit-constants":
            points, _ = fit_points(load_set("explore", args.explore)[1],
                                   load_set("spread", args.spread)[1])
            sys.stdout.write(emit_constants(json.loads(Path(args.fit).read_text()),
                                            Path(args.rulings).read_text(),
                                            head_bands(points), min_turns(points)))
            return 0
        if args.command == "fit":
            text = _dump(fit_document(args.explore, args.spread))
        else:
            document = json.loads(Path(args.fit).read_text())
            _, explore = load_set("explore", args.explore)
            _, spread = load_set("spread", args.spread)
            points, _ = fit_points(explore, spread)
            text = table(document, points, explore, args.fit)
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
