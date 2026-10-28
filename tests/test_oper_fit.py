"""The cost model's fit and envelope (07-09, R11, R12): synthetic records with known coefficients,
the fit input's exclusions, the provenance guard, and the committed fit.json against the code.

No Docker and no kernel: every record here is written by the test, except the committed runner
records the last test refits.
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Mapping
from pathlib import Path

import pytest

from bench import oper_fit
from bench.oper import summarize
from bench.oper_fit import FEATURES, TARGETS, Model
from bench.oper_sets import ProtocolStop
from screw.calc.cost import ARTIFACTS

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "bench" / "results" / "phase-07"
type Raw = dict[str, object]

# Known coefficients, intercept first, every one non-zero so a relative comparison is meaningful.
TRUE: dict[str, tuple[float, ...]] = {
    "bolt": (2.0, 0.9, -0.4, 0.7, 0.3, 0.25, -0.15, 0.05),
    "nut": (3.0, 1.1, -0.6, 0.35, 0.45, 0.08, 0.04),
}
# Each target is the same model shifted, so the three fits are distinct but known.
SHIFT = {"bytes": 10.0, "seconds": -2.5, "peak": 18.0}


def _params(kind: str, rng: random.Random) -> Raw:
    d = rng.uniform(2.0, 40.0)
    pitch = rng.uniform(0.2, 0.12 * d)
    hand = rng.random() < 0.5
    if kind == "bolt":
        length = rng.uniform(5.0, 80.0)
        return {"d": d, "pitch": pitch, "length": length,
                "thread_length": rng.uniform(0.3, 1.0) * length, "s": rng.uniform(1.3, 2.0) * d,
                "k": rng.uniform(0.4, 0.9) * d, "left_hand": hand}
    return {"d": d, "pitch": pitch, "s": rng.uniform(1.5, 2.2) * d, "m": rng.uniform(0.5, 1.2) * d,
            "clearance": rng.uniform(0.0, 1.0), "left_hand": hand}


def _truth(kind: str, artifact: str, target: str) -> Model:
    coef = (TRUE[kind][0] + SHIFT[target] + 0.1 * ARTIFACTS.index(artifact), *TRUE[kind][1:])
    return Model(kind, artifact, target, coef, 0, 0, 0.0, "")


def _reading(label: str, kind: str, params: Mapping[str, object], artifact: str, rep: int = 1,
             status: str = "ok", scale: float = 1.0) -> Raw:
    values = {t: oper_fit.predict(_truth(kind, artifact, t), params) * scale for t in TARGETS}
    return {"type": "reading", "label": label, "kind": kind, "params": dict(params),
            "artifact": artifact, "rep": rep, "status": status,
            "build_s": values["seconds"] * 0.75, "export_s": values["seconds"] * 0.25,
            "bytes": values["bytes"], "memory_peak_bytes": values["peak"]}


def _explore(n: int = 30, seed: int = 7) -> list[Raw]:
    rng = random.Random(seed)
    readings: list[Raw] = []
    for kind in FEATURES:
        for i in range(n):
            params = _params(kind, rng)
            readings += [_reading(f"{kind}-{i}", kind, params, a) for a in ARTIFACTS]
    return readings


def _params_of(reading: Raw) -> Mapping[str, object]:
    params = reading["params"]
    assert isinstance(params, dict)
    return params


def _close(a: float, b: float, rel: float) -> bool:
    return math.isclose(a, b, rel_tol=rel, abs_tol=0.0)


def test_noise_free_records_give_back_their_coefficients_and_no_envelope() -> None:
    points, excluded = oper_fit.fit_points(_explore(), [])
    assert excluded == []
    models = oper_fit.fit(points)
    assert len(models) == 2 * 3 * 3
    for model in models:
        truth = _truth(model.kind, model.artifact, model.target)
        assert all(_close(got, want, 1e-9) for got, want in
                   zip(model.coefficients, truth.coefficients, strict=True)), model
        assert model.n == 30
        assert model.rank == len(truth.coefficients)
        # Noise-free, the worst ratio is 1 within a few ulps; the envelope is at most those ulps.
        assert model.envelope < 1e-12


def test_one_record_twenty_percent_over_its_model_sets_an_envelope_of_0_2() -> None:
    readings = _explore()
    readings[0] = _reading("bolt-0", "bolt", _params_of(readings[0]), "stl-preview", scale=1.2)
    points, _ = oper_fit.fit_points(readings, [])
    truth = _truth("bolt", "stl-preview", "bytes")
    sample = [p for p in points if p.kind == "bolt" and p.artifact == "stl-preview"]
    e, by = oper_fit.envelope(truth, sample)
    assert _close(e, 0.2, 1e-12)
    assert by == "explore:bolt-0"


def test_every_fitted_point_is_covered_once_multiplied_by_one_plus_e() -> None:
    rng = random.Random(11)
    readings = [{**r, **{key: oper_fit._num(r[key]) * rng.uniform(0.7, 1.4)
                         for key in ("bytes", "build_s", "memory_peak_bytes")}}
                for r in _explore()]
    points, _ = oper_fit.fit_points(readings, [])
    for model in oper_fit.fit(points):
        assert model.envelope > 0
        for p in points:
            if (p.kind, p.artifact) == (model.kind, model.artifact):
                assert oper_fit.enveloped(model, p.params) >= p.target(model.target)


def _spread(label: str, reps: list[int], statuses: list[str] | None = None) -> list[Raw]:
    params = {"d": 6.0, "pitch": 1.0, "length": 20.0, "thread_length": 20.0, "s": 10.0, "k": 4.0}
    statuses = statuses or ["ok"] * len(reps)
    return [_reading(label, "bolt", params, "stl-fine", rep=r, status=s)
            for r, s in zip(reps, statuses, strict=True)]


def test_a_non_ok_or_incomplete_point_is_excluded_and_listed() -> None:
    explore = _explore()
    explore += [_reading("twice", "bolt", _params_of(explore[0]), "step")] * 2
    spread = (_spread("killed-one", [1, 2, 3, 4, 5], ["ok", "ok", "killed", "ok", "ok"])
              + _spread("four", [1, 2, 3, 4]) + _spread("five", [1, 2, 3, 4, 5]))
    points, excluded = oper_fit.fit_points(explore, spread)
    by_label = {str(x["label"]): x for x in excluded}
    assert set(by_label) == {"twice", "killed-one", "four"}
    assert by_label["killed-one"]["status"] == "killed"
    assert by_label["killed-one"]["counts"] == {"ok": 4, "killed": 1}
    assert by_label["four"]["status"] == "incomplete"
    assert by_label["four"]["reps"] == [1, 2, 3, 4]
    assert by_label["twice"]["status"] == "incomplete"
    assert by_label["twice"]["reps"] == [1, 1]
    assert by_label["twice"]["set"] == "explore"
    assert [p.label for p in points if p.set == "spread"] == ["five"]


def test_the_cold_wall_is_summed_per_reading_before_the_max() -> None:
    spread = _spread("five", [1, 2, 3, 4, 5])
    for reading, (build, export) in zip(spread, [(3.0, 0.0), (0.5, 2.9), (1.0, 1.0), (1.0, 1.0),
                                                 (1.0, 1.0)], strict=True):
        reading["build_s"], reading["export_s"] = build, export
    points, _ = oper_fit.fit_points([], spread)
    assert [p.seconds for p in points] == [0.5 + 2.9]


def test_the_fit_input_is_the_ok_rows_of_summarize_with_each_sets_reps() -> None:
    explore = _explore(n=10)
    explore[0] = {**explore[0], "status": "capped"}
    spread = _spread("five", [1, 2, 3, 4, 5]) + _spread("four", [1, 2, 3, 4])
    points, _ = oper_fit.fit_points(explore, spread)
    want = [(name, row["label"], row["artifact"])
            for name, readings, reps in (("explore", explore, (1,)),
                                         ("spread", spread, (1, 2, 3, 4, 5)))
            for row in summarize(readings, reps) if row["status"] == "ok"]
    assert [(p.set, p.label, p.artifact) for p in points] == want


def test_too_few_points_for_a_model_stop_the_fit_naming_it() -> None:
    explore = [r for r in _explore() if not (r["kind"] == "nut" and r["artifact"] == "step"
                                             and int(str(r["label"]).split("-")[1]) >= 7)]
    points, _ = oper_fit.fit_points(explore, [])
    with pytest.raises(ProtocolStop, match="nut step bytes: 7 fitted points, 8 needed"):
        oper_fit.fit(points)


def test_admission_at_the_budget_is_admitted_and_one_float_above_is_refused() -> None:
    pred, e = 3.0, 0.1
    budget = pred * (1.0 + e)
    assert oper_fit.admit(pred, e, budget)
    assert not oper_fit.admit(pred, e, math.nextafter(budget, -math.inf))
    assert oper_fit.admit(pred, e, None)


def test_the_bolt_turns_feature_is_the_built_thread_over_the_pitch() -> None:
    # thread_length above length is built to the length; a shank under MIN_TAIL_MM is folded in.
    over = oper_fit.features("bolt", {"d": 6.0, "pitch": 0.5, "length": 10.0,
                                      "thread_length": 30.0, "s": 10.0, "k": 4.0})
    assert _close(over[2], math.log(10.0 / 0.5), 1e-15)
    sliver = oper_fit.features("bolt", {"d": 6.0, "pitch": 0.5, "length": 10.0,
                                        "thread_length": 10.0 - 1e-5, "s": 10.0, "k": 4.0})
    assert _close(sliver[2], math.log(10.0 / 0.5), 1e-15)
    # A part with no fields is the frozen default part (the spread's default bolt and nut).
    assert oper_fit.features("bolt", {}) == oper_fit.features(
        "bolt", {"d": 6.0, "pitch": 1.0, "length": 20.0, "thread_length": 20.0, "s": 10.0,
                 "k": 4.0, "left_hand": False})
    assert oper_fit.features("nut", {})[4] == 0.15


def _record_dir(root: Path, name: str, head: Raw, readings: list[Raw]) -> Path:
    shard = root / f"{name}-1-1"
    shard.mkdir(parents=True)
    lines = [json.dumps({"type": "header", **head})] + [json.dumps(r) for r in readings]
    (shard / f"{name}-1-1.jsonl").write_text("\n".join(lines) + "\n")
    return root


RUNNER: Raw = {"machine": "x86_64", "GITHUB_RUN_ID": "1"}


@pytest.mark.parametrize(("name", "head", "extra", "message"), [
    ("oper-explore", {"machine": "arm64", "GITHUB_RUN_ID": "1"}, {}, "not a linux/amd64 runner"),
    ("oper-explore", {"machine": "x86_64"}, {}, "not a linux/amd64 runner"),
    ("oper-bound-smoke", RUNNER, {}, "not a record of the explore set"),
    ("oper-explore", RUNNER, {"lift": {"max_turns": 260}}, "is not a part reading"),
    ("oper-explore", RUNNER, {"kind": "probe"}, "is not a part reading"),
])
def test_only_runner_records_of_the_set_are_taken(tmp_path: Path, name: str, head: Raw,
                                                  extra: Raw, message: str) -> None:
    reading = {**_explore(n=1)[0], **extra}
    root = _record_dir(tmp_path / "set", name, head, [reading])
    with pytest.raises(ValueError, match=message):
        oper_fit.load_set("explore", [root])


def test_a_runner_record_is_taken_with_its_run_id(tmp_path: Path) -> None:
    root = _record_dir(tmp_path / "set", "oper-explore", RUNNER, _explore(n=1))
    runs, readings = oper_fit.load_set("explore", [root])
    assert runs == ["1"]
    assert len(readings) == 6


def test_the_fit_is_the_same_on_two_invocations() -> None:
    points, _ = oper_fit.fit_points(_explore(), [])
    assert oper_fit.fit(points) == oper_fit.fit(points)


def _committed_dirs(name: str) -> list[Path]:
    return sorted(RESULTS.glob(f"{name}-*"))


def test_the_committed_fit_json_is_what_the_code_fits_from_the_committed_records() -> None:
    # Bytes match on the machine that wrote fit.json (the plan's `cmp`); another BLAS may move
    # the last bits of a coefficient, so here the floats are compared to 1e-9 relative.
    committed = json.loads((RESULTS / "fit.json").read_text())
    fresh = oper_fit.fit_document(_committed_dirs("explore"), _committed_dirs("spread"))
    assert fresh["run_ids"] == committed["run_ids"] == {"explore": ["40646117094"],
                                                        "spread": ["40646125666"]}
    assert fresh["fitted"] == committed["fitted"]
    assert fresh["excluded"] == committed["excluded"]
    assert len(oper_fit.models_of(fresh)) == len(oper_fit.models_of(committed)) == 18
    for new, old in zip(oper_fit.models_of(fresh).values(), oper_fit.models_of(committed).values(),
                        strict=True):
        assert (new.kind, new.artifact, new.target, new.n, new.rank) == (
            old.kind, old.artifact, old.target, old.n, old.rank)
        assert all(_close(a, b, 1e-9) for a, b in zip(new.coefficients, old.coefficients,
                                                      strict=True))
        assert _close(new.envelope, old.envelope, 1e-9)


def test_the_committed_envelopes_cover_every_fitted_point() -> None:
    explore = oper_fit.load_set("explore", _committed_dirs("explore"))[1]
    spread = oper_fit.load_set("spread", _committed_dirs("spread"))[1]
    points, _ = oper_fit.fit_points(explore, spread)
    models = oper_fit.models_of(json.loads((RESULTS / "fit.json").read_text()))
    for p in points:
        for t in TARGETS:
            assert oper_fit.enveloped(models[p.kind, p.artifact, t], p.params) >= p.target(t)
