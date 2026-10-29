"""Per-artifact cost rules: which files a download can produce, how long a build may take, and
whether a part's artifact fits its measured budget.

Kernel-free and logger-free like the rest of `calc` (import-linter contracts 2 and 4), and free of
numpy: `predict` runs on every keystroke through `derive`, so it is a plain sum and `math.exp`,
the arithmetic `bench.oper_fit.predict` fitted with (R11). The pool, the app and the bench harness
all key on the same three artifact names.
"""

from __future__ import annotations

import itertools
import math
import sys
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal, NamedTuple, get_args

from pydantic import ValidationError

from screw.calc.thread import _plain, built_thread_length
from screw.params import BoltParams, FastenerParams, NutParams

Artifact = Literal["stl-preview", "stl-fine", "step"]
ARTIFACTS: Final[tuple[Artifact, ...]] = get_args(Artifact)

# INTERIM (Phase 1 D-01, carried from spur; Phase 7 plan 07-16 replaces all three with
# measured values and a cited run). 30 s per build is spur's: its worst observed single build
# was 7.39 s (a 200-tooth fine gear, ten concurrent requests, host under contention), so 30 s is
# about 4x spur's observation -- a margin chosen for slower hardware on spur's corpus. It is
# not a measurement of screw: M6 x 20 builds in 0.09 s (planner probe 2026-10-10), while an
# in-cap off-row part can need minutes (03-RESEARCH Pitfall 5: d=100, pitch=5, length=1250,
# fine STL 152.6 s and 7875 MiB peak RSS, single run, macOS arm64, not a bound). So these are
# the backstop below the turn cap (D-01, D-18; `MAX_TURNS`), not a figure for the threads.
#
# Code constants with no environment override (D-16): a deployer on slower hardware re-sweeps
# and a superseding log entry records the new figure, so the number in force always cites the
# run that set it. Read-only, so a stray assignment cannot move a bound the log cites.
BUILD_TIMEOUT_S: Final[Mapping[Artifact, float]] = MappingProxyType(
    {"stl-preview": 30.0, "stl-fine": 30.0, "step": 30.0})


def artifact_of(fmt: str, quality: str) -> Artifact:
    """The artifact a download of `fmt` at `quality` produces.

    STEP ignores the quality (`solid._write_export` tessellates only for STL), so both of its
    qualities are one artifact with one timeout.
    """
    if quality not in ("preview", "fine"):
        raise ValueError(f"no artifact for quality {quality!r}")
    if fmt == "step":
        return "step"
    if fmt == "stl":
        return "stl-preview" if quality == "preview" else "stl-fine"
    raise ValueError(f"no artifact for format {fmt!r}")


# --- the cost model (07 D-05, D-07, D-17; R11, R12; B-01) --------------------------------------

Target = Literal["bytes", "seconds", "peak"]
TARGETS: Final[tuple[Target, ...]] = get_args(Target)
type ModelKey = tuple[str, Artifact, Target]
type Budget = tuple[float | None, float | None, float | None]

# R11's features, in the order the coefficients follow after the intercept; the same names and
# order as `bench.oper_fit.FEATURES`, which tests/test_cost.py holds equal.
FEATURES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "bolt": ("ln_d", "ln_pitch", "ln_turns", "ln_length", "ln_s", "ln_k", "left_hand"),
    "nut": ("ln_d", "ln_pitch", "ln_s", "ln_m", "clearance", "left_hand"),
})

# The numeric fields the features read, in the order the refusal text and the 422's `ctx.fields`
# name them (B-02): the bolt's turns are its built thread over the pitch, so `thread_length` and
# `length` both move them. The hand is a feature but no field a user shrinks a part by.
FIELDS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "bolt": ("d", "pitch", "length", "s", "k", "thread_length"),
    "nut": ("d", "pitch", "s", "m", "clearance"),
})

# BEGIN emit-constants: `python -m bench.oper_fit emit-constants`; not edited by hand.
# R11's least squares: the intercept, then one coefficient per `FEATURES[kind]`.
# fit.json, runs explore 40646117094 and spread 40646125666.
COEFFICIENTS: Final[Mapping[ModelKey, tuple[float, ...]]] = MappingProxyType({
    ("bolt", "stl-preview", "bytes"): (8.520962322183781, 0.2633880404477821,
        0.0027484416285799814, 1.0189385237562507, -0.025601499394011976, 1.4650904172545873,
        -0.7809665064607385, -0.07959442210300958),
    ("bolt", "stl-preview", "seconds"): (-5.2555915925272565, -0.3830930746650897,
        -0.2759638422879909, 0.5299188269066086, 0.12348426010683368, 3.686170682854927,
        -2.7685645753092394, -0.057849635433456136),
    ("bolt", "stl-preview", "peak"): (16.43533914375026, -1.670428599104153, -0.029807463325174147,
        0.1834267176181396, -0.024052555098778405, 2.638257057596685, -0.5519406250653605,
        0.03380061811599671),
    ("bolt", "stl-fine", "bytes"): (10.258829174407301, 3.886504630593928, -0.06164464988483598,
        0.9700637584459836, 0.03047485143663836, 0.5503198660144293, -3.675006998315813,
        -0.2750395081212716),
    ("bolt", "stl-fine", "seconds"): (-4.770758262268293, 1.7967990002902046, -0.10578453047034266,
        0.7921641249141849, 0.01934359698858789, 2.2508250755707264, -3.3662155284549704,
        0.13472185645861945),
    ("bolt", "stl-fine", "peak"): (15.679190629020743, 1.4138940073877415, -0.04969747941041629,
        0.21915129297500027, 0.00046229401032016034, 2.1778426720613884, -3.0070381675011566,
        0.03443781809827005),
    ("bolt", "step", "bytes"): (11.120125319256811, 0.16079821844031625, -0.0014501314331426996,
        0.8944458686202342, -0.05629377785162237, 0.20777637239021748, -0.20691176819588397,
        0.04482727909723022),
    ("bolt", "step", "seconds"): (-2.767722347811926, 1.4283863741280929, -0.33801070595914673,
        0.3883583398976484, 0.1581213059467766, 1.0520543935755158, -2.338008271401886,
        -0.04431184617745629),
    ("bolt", "step", "peak"): (18.12787996299112, 0.5776071852522069, -0.016930333615659907,
        0.15895114163398202, -0.0007811181960355954, 0.3575613084027657, -0.8975131474757659,
        0.035261823080591524),
    ("nut", "stl-preview", "bytes"): (9.503685747087617, 0.7099886472165183, -1.029614736509572,
        0.12137488785657789, 1.0358929491509747, 0.09611459718844559, -0.1606467568469765),
    ("nut", "stl-preview", "seconds"): (-0.7486351870808057, 0.40936184937141784,
        -0.7594630973345009, -0.09478569519639327, 0.5624186749813316, -0.05467467125721249,
        -0.11733444235170201),
    ("nut", "stl-preview", "peak"): (18.585749128971052, 0.30526866793652474, -0.21178463442955536,
        -0.0494831589946223, 0.08373326074468937, 0.005316238227168808, -0.0569768497103201),
    ("nut", "stl-fine", "bytes"): (12.066538321728528, 0.5890306349005798, -0.9926241550513081,
        0.04064085709953195, 1.106276190354379, 0.11195342153670919, -0.14415026071075085),
    ("nut", "stl-fine", "seconds"): (-1.4660150657649265, 0.6712639392062811, -0.9284111228053379,
        -0.1276808559264419, 0.8541615950406674, 0.06459631600519246, -0.07053029236008582),
    ("nut", "stl-fine", "peak"): (18.078350444935996, 0.5848485472446224, -0.3267687150188528,
        0.006409924083256925, 0.22910166945569949, 0.05474164947480684, -0.048285431840674096),
    ("nut", "step", "bytes"): (12.081160258367845, 0.09806459483254824, -0.7248917540723306,
        -0.014044923513587779, 0.7000299007824499, 4.6401078272701016e-05, -0.012359019180166715),
    ("nut", "step", "seconds"): (-0.34864039742389485, 0.41877320675334223, -0.6998587677048579,
        -0.24054889041832564, 0.5299210115671444, -0.05478165043082735, -0.151464723275327),
    ("nut", "step", "peak"): (19.07759822430459, 0.09208069717309247, -0.10816512872686,
        -0.07262131153585069, 0.06981771588564518, 0.012521043967529668, -0.014383798680039622),
})
# R12's envelope e per model.
# fit.json, runs explore 40646117094 and spread 40646125666.
ENVELOPE: Final[Mapping[ModelKey, float]] = MappingProxyType({
    ("bolt", "stl-preview", "bytes"): 2.264581945786201,
    ("bolt", "stl-preview", "seconds"): 4.286137349093968,
    ("bolt", "stl-preview", "peak"): 2.040087854388461,
    ("bolt", "stl-fine", "bytes"): 0.5633622849303941,
    ("bolt", "stl-fine", "seconds"): 2.690232029900006,
    ("bolt", "stl-fine", "peak"): 2.170967259675211,
    ("bolt", "step", "bytes"): 0.9874058238127998,
    ("bolt", "step", "seconds"): 2.616422482555953,
    ("bolt", "step", "peak"): 0.45747877720379804,
    ("nut", "stl-preview", "bytes"): 0.7070121785110755,
    ("nut", "stl-preview", "seconds"): 1.061383246630594,
    ("nut", "stl-preview", "peak"): 0.556086702674923,
    ("nut", "stl-fine", "bytes"): 0.4996608149413484,
    ("nut", "stl-fine", "seconds"): 1.1069417227945801,
    ("nut", "stl-fine", "peak"): 0.5571452809681212,
    ("nut", "step", "bytes"): 0.3802587303182223,
    ("nut", "step", "seconds"): 0.8785228687431521,
    ("nut", "step", "peak"): 0.48786919655819627,
})
# G28's band of each head ratio, field / d: its [min, max] over the fitted
# points of its kind, an omitted field at its default (R11).
# The records of runs explore 40646117094 and spread 40646125666.
BANDS: Final[Mapping[tuple[str, str], tuple[float, float]]] = MappingProxyType({
    ("bolt", "k"): (0.6, 0.7),
    ("bolt", "s"): (1.5, 2.0),
    ("nut", "s"): (1.5, 4.0),
    ("nut", "m"): (0.7999999999999999, 3.0),
})
# B-01 of 07-OWNER-RULINGS.md (2026-10-29): C1 of R13, catalogue-complete.
# (raw bytes, cold build seconds, cgroup peak bytes); None is unbounded.
BUDGET: Final[Mapping[Artifact, Budget]] = MappingProxyType({
    "stl-preview": (55704726.47566052, 34.127968722622484, 1049185338.9620932),
    "stl-fine": (239508059.14804876, 94.42979276577135, 2930457561.336711),
    "step": (9748694.773917168, 15.000925691551677, 422239338.63724077),
})
# END emit-constants

# How the refusal text names an artifact: the page's words, then the id the 422's `ctx.artifact`
# carries, so a reader can match the two.
_NAMES: Final[Mapping[Artifact, str]] = MappingProxyType({
    "stl-preview": "preview STL (stl-preview)", "stl-fine": "fine STL (stl-fine)",
    "step": "STEP (step)"})


_LN_FLOAT_MAX: Final = math.log(sys.float_info.max)


class Cost(NamedTuple):
    """A predicted cost of one artifact, before the envelope: never printed (L02)."""

    bytes: float
    seconds: float
    peak: float


def _features(p: FastenerParams) -> tuple[str, list[float]]:
    hand = 1.0 if p.left_hand else 0.0
    if isinstance(p, BoltParams):
        turns = built_thread_length(p.thread_length, p.length) / p.pitch
        return "bolt", [math.log(p.d), math.log(p.pitch), math.log(turns), math.log(p.length),
                        math.log(p.s), math.log(p.k), hand]
    if isinstance(p, NutParams):
        return "nut", [math.log(p.d), math.log(p.pitch), math.log(p.s), math.log(p.m),
                       p.clearance, hand]
    raise TypeError(f"no cost model for kind {p.kind!r}")


def _raw(p: FastenerParams, artifact: Artifact) -> list[float]:
    kind, x = _features(p)
    values: list[float] = []
    for target in TARGETS:
        coefficients = COEFFICIENTS[kind, artifact, target]
        z = coefficients[0]
        for coefficient, feature in zip(coefficients[1:], x, strict=True):
            z += coefficient * feature
        # An unvalidated part (model_construct, d 1e200) can sum past exp's range: infinite is
        # over every finite budget, so it is refused, and no figure is printed either way (L02).
        values.append(math.exp(z) if z < _LN_FLOAT_MAX else math.inf)
    return values


def _edges(p: FastenerParams) -> list[FastenerParams]:
    """G28: `p` at every combination of band edges of its out-of-band head ratios, each such field
    set to edge x d and every other field held; empty when every ratio is in its band. A ratio
    above its band takes both edges, one below it the low edge only (ruling 5): a smaller head is
    assumed, unmeasured, never to cost more than one at the low edge."""
    out: list[tuple[str, tuple[float, ...]]] = []
    for (kind, field), (low, high) in BANDS.items():
        ratio = float(getattr(p, field)) / p.d if kind == p.kind else low
        if ratio > high:
            out.append((field, (low * p.d, high * p.d)))
        elif ratio < low:
            out.append((field, (low * p.d,)))
    names = [field for field, _ in out]
    # model_copy sets the fields without validating: the edge part is only ever predicted.
    return [p.model_copy(update=dict(zip(names, combo, strict=True)))
            for combo in itertools.product(*(values for _, values in out))] if out else []


def predict(p: FastenerParams, artifact: Artifact) -> Cost:
    """The fitted cost of `p`'s `artifact`, before the envelope (R11): the same sum, in the same
    order, as `bench.oper_fit.predict`, so the two agree to the last bit.

    G28: the fit saw each head ratio only in a narrow band (bolt k/d 0.6 to 0.7), where `ln_k`
    comes out negative on every bolt model, so k 1000 on an M100 predicted a 0.0063 s fine STL.
    A part with a ratio outside its band is predicted, target by target, as the largest of the
    raw prediction and the one at every combination of band edges, both edges for a ratio above
    its band and the low edge for one below it: above, for this log-linear model, the largest
    anywhere in the band; below, max(raw, low edge). A d-only M8 (s/d 1.25) is so judged at s
    1.5 d, not at the wide-head edge 2 d that refused its preview under ruling 4. Inside every
    band it is the raw prediction, bit for bit."""
    values = _raw(p, artifact)
    for edge in _edges(p):
        values = [max(a, b) for a, b in zip(values, _raw(edge, artifact), strict=True)]
    return Cost(*values)


def admitted(pred: float, e: float, budget: float | None) -> bool:
    """R12 for one target: admitted iff `pred x (1 + e)` is at most the budget, so at the budget
    is admitted and one float above it is refused. A None budget is unbounded and admits."""
    return budget is None or pred * (1.0 + e) <= budget


def fits(p: FastenerParams, artifact: Artifact) -> bool:
    """Whether every target of `p`'s `artifact` is admitted against B-01's budget (R12)."""
    kind = p.kind
    return all(admitted(pred, ENVELOPE[kind, artifact, target], budget)
               for pred, target, budget in zip(predict(p, artifact), TARGETS, BUDGET[artifact],
                                               strict=True))


def _listed(names: list[str]) -> str:
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def refusal(p: FastenerParams, artifact: Artifact) -> str | None:
    """Why `p`'s `artifact` is refused before any build, or None when it fits (D-05, D-06).

    The text begins with the kind's cost fields, so the CLI, which prints no `loc`, still names
    them; it names the artifact and L21 and says which artifacts of the part do fit. It prints no
    predicted figure: a prediction is not a measurement, and a number here is one someone would
    cut metal to (L02). No braces: pydantic would format them from its context.
    """
    if fits(p, artifact):
        return None
    others = [_NAMES[a] for a in ARTIFACTS if a != artifact and fits(p, a)]
    verb = "fits" if len(others) == 1 else "fit"
    served = (f"the {_listed(others)} of this part {verb}" if others
              else "no artifact of this part fits")
    advice = "change one of these fields, or download an artifact that fits" if others else (
        "change one of these fields")
    return (f"{_listed(list(FIELDS[p.kind]))}: the {_NAMES[artifact]} of this {p.kind} is "
            f"predicted over its measured budget (L21), so it is refused before any build; "
            f"{served}. To get it, {advice}")


# --- the default cap (07 D-06; B-03 and its clarification, 07-OWNER-RULINGS.md, 2026-10-29) ----

# B-03 (part-wide): the fields a cap may move, in the order it tries them, each with its form step,
# the `step` the schema publishes (tests/test_cost.py holds the two equal). d, pitch, s, k,
# clearance, head_chamfer and the hand never move.
CAP_STEPS: Final[Mapping[str, tuple[tuple[str, float], ...]]] = MappingProxyType({
    "bolt": (("thread_length", 0.5), ("length", 0.5)),
    "nut": (("m", 0.1),),
})


def fits_every_artifact(p: FastenerParams) -> bool:
    """Whether every artifact of `p` fits its budget: the test B-03's part-wide cap reads."""
    return all(fits(p, artifact) for artifact in ARTIFACTS)


def cap_defaults(p: FastenerParams, explicit: frozenset[str] = frozenset()
                 ) -> tuple[FastenerParams, tuple[str, ...]]:
    """`p` with one defaulted field capped so every artifact fits, and the one warning that says so;
    `(p, ())` when `p` fits already or no allowed cap admits it (D-06, B-03, L02).

    `explicit` is what the request named: the raw query keys on the API, the given flags and a
    preset's fields on the CLI, the same set the conflict rules read. A named field, or one that is
    not at its frozen default (direct construction), is never moved. Each other field of
    `CAP_STEPS` is tried in order, scanning down its form step from the default, and the first value
    at which every artifact fits wins, so it is the largest. B-03's clarification (ruling 1):
    `length` is never capped below a named `thread_length`, so the built thread stays what the user
    named; a part nothing admits keeps its per-artifact `over_budget` 422 (B-02).

    At most 39 + 39 candidates for a bolt and 51 for a nut, each three kernel-free predictions
    (T-07-32). The warning prints only the default, the capped value and the step, never a
    prediction (L02).
    """
    if fits_every_artifact(p):
        return p, ()
    model = type(p)

    def named(field: str) -> bool:
        return field in explicit or getattr(p, field) != model.model_fields[field].default

    for field, step in CAP_STEPS[p.kind]:
        if named(field):
            continue
        default = float(getattr(p, field))
        floor = p.thread_length if (
            isinstance(p, BoltParams) and field == "length" and named("thread_length")) else 0.0
        for i in range(round(default / step) - 1, 0, -1):
            value = round(i * step, 10)
            if value < floor:
                break
            try:
                capped = model.model_validate({**p.model_dump(), field: value})
            except ValidationError:
                continue
            if fits_every_artifact(capped):
                return capped, (_cap_warning(p, field, default, value, step),)
    return p, ()


def _cap_warning(p: FastenerParams, field: str, default: float, value: float, step: float) -> str:
    over = [_NAMES[a] for a in ARTIFACTS if not fits(p, a)]
    return (f"{field}: the default {_plain(default)} mm puts the {_listed(over)} of this {p.kind} "
            f"over its measured budget (L21), so {field} is capped at {_plain(value)} mm, the "
            f"largest value on its {_plain(step)} mm form step at which every artifact fits; give "
            f"{field} to choose it, and an artifact over the budget is then refused")
