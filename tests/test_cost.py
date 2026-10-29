"""The per-artifact vocabulary the build timeout, the budgets and the cost model share (D-09).

One name per file a download can produce, so a timeout, a budget and a measured cost all key
on the same three strings.
"""

from __future__ import annotations

import ast
import functools
import itertools
import json
import math
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from bench import oper_fit
from screw.calc import cost, derive, download_refusal
from screw.calc.cost import ARTIFACTS, BUILD_TIMEOUT_S, artifact_of
from screw.calc.thread import built_thread_length
from screw.params import KINDS, BoltParams, FastenerParams, NutParams
from screw.tables.presets import catalogue, nut_catalogue


@pytest.mark.parametrize(("fmt", "quality", "want"), [
    ("stl", "preview", "stl-preview"),
    ("stl", "fine", "stl-fine"),
    ("step", "preview", "step"),
    ("step", "fine", "step"),
])
def test_an_artifact_is_named_by_the_file_a_download_produces(
        fmt: str, quality: str, want: str) -> None:
    """STEP ignores the quality, so both qualities are one artifact with one timeout."""
    assert artifact_of(fmt, quality) == want


@pytest.mark.parametrize(("fmt", "quality"), [
    ("obj", "fine"),
    ("stl", "draft"),
    ("step", "draft"),
    ("", ""),
])
def test_what_no_download_produces_is_not_an_artifact(fmt: str, quality: str) -> None:
    with pytest.raises(ValueError, match="artifact"):
        artifact_of(fmt, quality)


def test_the_artifacts_are_the_three_downloads() -> None:
    assert ARTIFACTS == ("stl-preview", "stl-fine", "step")


def test_every_artifact_has_a_positive_build_timeout_and_nothing_else_does() -> None:
    assert set(BUILD_TIMEOUT_S) == set(ARTIFACTS)
    assert all(seconds > 0 for seconds in BUILD_TIMEOUT_S.values())


# --- the cost model (07 D-05, D-07, D-17; R11, R12; B-01) --------------------------------------

REPO = Path(__file__).resolve().parents[1]
FIT = REPO / "bench" / "results" / "phase-07" / "fit.json"
RULINGS = REPO / ".planning" / "phases" / "07-operability-re-sweep" / "07-OWNER-RULINGS.md"
COST_PY = REPO / "src" / "screw" / "calc" / "cost.py"

# The explore point `bolt-d30-p1-n30-right`, which 07-BUDGET-TABLE.md lists as refused at stl-fine
# under C1 (B-01; run 40646117094). An R12 widening only refuses more, so it stays refused.
OVER = BoltParams(d=30.0, pitch=1.0, length=30.0, thread_length=30.0, s=48.0, k=18.0)


def _document() -> dict[str, object]:
    raw = json.loads(FIT.read_text())
    assert isinstance(raw, dict)
    return raw


@functools.cache
def _bands() -> dict[tuple[str, str], tuple[float, float]]:
    """G28's bands, recomputed from the committed runner records fit.json was fitted on."""
    results = FIT.parent
    points, _ = oper_fit.fit_points(
        oper_fit.load_set("explore", sorted(results.glob("explore-*")))[1],
        oper_fit.load_set("spread", sorted(results.glob("spread-*")))[1])
    return oper_fit.head_bands(points)


def test_the_shipped_constants_are_the_block_emit_constants_writes_from_the_evidence() -> None:
    # T-07-29: generated from fit.json, the committed records and B-01's table, never typed.
    block = oper_fit.emit_constants(_document(), RULINGS.read_text(), _bands())
    assert block in COST_PY.read_text()
    assert COST_PY.read_text().count(oper_fit.EMIT_BEGIN) == 1


def test_the_coefficients_and_envelopes_equal_fit_json() -> None:
    models = oper_fit.models_of(_document())
    assert set(cost.COEFFICIENTS) == set(models) == set(cost.ENVELOPE)
    for key, coefficients in cost.COEFFICIENTS.items():
        assert coefficients == models[key].coefficients, key
        assert cost.ENVELOPE[key] == models[key].envelope, key
    assert dict(cost.FEATURES) == oper_fit.FEATURES
    assert cost.TARGETS == oper_fit.TARGETS


def test_the_budget_is_b01_and_b01_is_c1_recomputed_from_fit_json_and_the_catalogue() -> None:
    _, ruled = oper_fit.ruled_budget(RULINGS.read_text())
    assert dict(cost.BUDGET) == ruled
    models = oper_fit.models_of(_document())
    for artifact in ARTIFACTS:
        parts = oper_fit._catalogue_parts(artifact)
        c1 = tuple(max(oper_fit.enveloped(models[p.kind, artifact, t], p.params) for p in parts)
                   for t in oper_fit.TARGETS)
        assert cost.BUDGET[artifact] == c1, artifact


# The orchestrator's two G28 bypass cases at d869b87: admitted on a raw prediction that fell as
# the head ratio left its band (bolt k/d 10, nut s/d 33.3).
TALL_HEAD = BoltParams(d=100.0, pitch=1.0, length=30.0, thread_length=30.0, s=200.0, k=1000.0)
WIDE_NUT = NutParams(d=30.0, pitch=0.35, s=999.0, m=24.0, clearance=0.15)


@pytest.mark.parametrize("part", [BoltParams(), NutParams(), OVER,
                                  BoltParams(d=8.0, pitch=1.25, length=70.0, thread_length=80.0,
                                             left_hand=True),
                                  NutParams(d=30.0, pitch=0.35, s=48.0, m=24.0, clearance=0.15),
                                  TALL_HEAD, WIDE_NUT,
                                  BoltParams(d=10.0, s=99.0, k=1.0),
                                  NutParams(d=10.0, pitch=1.5, s=11.0, m=40.0)],
                         ids=["bolt", "nut", "over", "bolt-left-past", "nut-fine-pitch",
                              "tall-head", "wide-nut", "bolt-two-out", "nut-two-out"])
def test_the_prediction_is_the_fits_own_for_every_artifact(part: FastenerParams) -> None:
    # Bit for bit, under G28 too: the same sums, the same edges, the same max.
    models = oper_fit.models_of(_document())
    params = part.model_dump()
    for artifact in ARTIFACTS:
        predicted = cost.predict(part, artifact)
        for target, value in zip(cost.TARGETS, predicted, strict=True):
            want = oper_fit.predict(models[part.kind, artifact, target], params, cost.BANDS)
            assert value == want, (artifact, target)


# --- G28: a head ratio outside the band the fit saw -------------------------------------------


def test_the_shipped_bands_are_the_ones_recomputed_from_the_committed_records() -> None:
    assert dict(cost.BANDS) == _bands()
    assert {kind for kind, _ in cost.BANDS} == set(oper_fit.RATIOS)
    assert [f for _, f in cost.BANDS] == [f for k in oper_fit.RATIOS for f in oper_fit.RATIOS[k]]


def test_every_catalogue_row_and_default_part_is_inside_every_band() -> None:
    # Otherwise G28 would move a catalogue row's prediction and B-01's C1 with it.
    rows = ([BoltParams.model_validate(dict(r.fields)) for r in catalogue()]
            + [NutParams.model_validate(dict(r.fields)) for r in nut_catalogue()])
    for part in [BoltParams(), NutParams(), *rows]:
        for (kind, field), (low, high) in cost.BANDS.items():
            if kind == part.kind:
                assert low <= getattr(part, field) / part.d <= high, (part, field)


@pytest.mark.parametrize("part", [BoltParams(), NutParams(), OVER],
                         ids=["bolt", "nut", "over"])
def test_an_in_band_prediction_is_the_raw_fit(part: FastenerParams) -> None:
    models = oper_fit.models_of(_document())
    for artifact in ARTIFACTS:
        raw = tuple(oper_fit.predict(models[part.kind, artifact, t], part.model_dump())
                    for t in cost.TARGETS)
        assert tuple(cost.predict(part, artifact)) == raw, artifact


@pytest.mark.parametrize("part", [TALL_HEAD, WIDE_NUT, BoltParams(d=10.0, s=99.0, k=1.0),
                                  NutParams(d=10.0, pitch=1.5, s=11.0, m=40.0)],
                         ids=["tall-head", "wide-nut", "bolt-two-out", "nut-two-out"])
def test_an_out_of_band_prediction_is_the_largest_over_raw_and_every_band_edge(
        part: FastenerParams) -> None:
    # Ruling 5: a ratio above its band takes both edges, one below it the low edge only.
    models = oper_fit.models_of(_document())
    out: list[tuple[str, tuple[float, ...]]] = []
    for (kind, field), (low, high) in cost.BANDS.items():
        if kind == part.kind and getattr(part, field) / part.d > high:
            out.append((field, (low * part.d, high * part.d)))
        elif kind == part.kind and getattr(part, field) / part.d < low:
            out.append((field, (low * part.d,)))
    assert out
    params = part.model_dump()
    trials = [params] + [params | dict(zip([f for f, _ in out], combo, strict=True))
                         for combo in itertools.product(*(edges for _, edges in out))]
    assert len(trials) == 1 + math.prod(len(edges) for _, edges in out)
    for artifact in ARTIFACTS:
        want = tuple(max(oper_fit.predict(models[part.kind, artifact, t], q) for q in trials)
                     for t in cost.TARGETS)
        assert tuple(cost.predict(part, artifact)) == want, artifact


@pytest.mark.parametrize("part", [TALL_HEAD, WIDE_NUT], ids=["tall-head", "wide-nut"])
def test_the_bypass_cases_are_refused_wherever_their_raw_prediction_admitted_them(
        part: FastenerParams) -> None:
    models = oper_fit.models_of(_document())
    raw_admitted = [a for a in ARTIFACTS if all(
        cost.admitted(oper_fit.predict(models[part.kind, a, t], part.model_dump()),
                      cost.ENVELOPE[part.kind, a, t], b)
        for t, b in zip(cost.TARGETS, cost.BUDGET[a], strict=True))]
    assert raw_admitted, "not a bypass: the raw prediction admits no artifact"
    for artifact in raw_admitted:
        # Against the rule: above the band, the largest prediction anywhere in it refuses it.
        assert not oper_fit.admitted(models, oper_fit.Part("p", part.kind, artifact,
                                                           part.model_dump(), False),
                                     cost.BUDGET[artifact], cost.BANDS), artifact
        assert not cost.fits(part, artifact), artifact
        assert cost.refusal(part, artifact) is not None, artifact


def _admitted_under_the_rule(part: FastenerParams) -> list[str]:
    models = oper_fit.models_of(_document())
    return [a for a in ARTIFACTS
            if oper_fit.admitted(models, oper_fit.Part("p", part.kind, a, part.model_dump(), False),
                                 cost.BUDGET[a], cost.BANDS)]


def test_a_d_only_m8_bolt_below_both_bands_keeps_all_three_artifacts() -> None:
    # Ruling 5: s/d 1.25 and k/d 0.5 are judged at the low edges, s 12 and k 4.8, not at the
    # wide-head edge s 16 whose preview peak is over budget (the 22 gate failures of ruling 4).
    m8 = BoltParams(d=8.0)
    assert [e.model_dump() for e in cost._edges(m8)] == [m8.model_copy(
        update={"k": cost.BANDS["bolt", "k"][0] * 8.0, "s": cost.BANDS["bolt", "s"][0] * 8.0}
    ).model_dump()]
    assert _admitted_under_the_rule(m8) == list(ARTIFACTS)
    assert all(cost.fits(m8, a) for a in ARTIFACTS)


def test_a_d_only_m5_bolt_above_the_k_band_loses_its_preview_only() -> None:
    # The owner OK'd this refusal with ruling 5: k/d 0.8 is above the band, so the shortest head
    # in the band, k 0.6 d, sets the preview's prediction.
    m5 = BoltParams(d=5.0)
    assert {field for e in cost._edges(m5) for field in ("k", "s")
            if getattr(e, field) != getattr(m5, field)} == {"k"}
    assert _admitted_under_the_rule(m5) == ["stl-fine", "step"]
    assert [a for a in ARTIFACTS if not cost.fits(m5, a)] == ["stl-preview"]
    assert cost.refusal(m5, "stl-preview") is not None


def test_admission_at_the_budget_is_admitted_and_one_float_above_is_refused() -> None:
    # OPER-03 adjacency: R12's `pred x (1 + e) <= budget`, at the float boundary.
    for budget in cost.BUDGET["stl-fine"]:
        assert budget is not None
        assert cost.admitted(budget, 0.0, budget)
        assert not cost.admitted(math.nextafter(budget, math.inf), 0.0, budget)
    # With an envelope: the enveloped figure at the budget is admitted, one float under is not.
    for e in cost.ENVELOPE.values():
        enveloped = 239508059.0 * (1.0 + e)
        assert cost.admitted(239508059.0, e, enveloped)
        assert not cost.admitted(239508059.0, e, math.nextafter(enveloped, 0.0))
    assert cost.admitted(1e300, 0.0, None)   # an unbounded component admits


def test_the_all_default_parts_fit_every_artifact() -> None:
    # OPER-03's empty edge: a link that names no field always serves (L02).
    for part in (BoltParams(), NutParams()):
        for artifact in ARTIFACTS:
            assert cost.fits(part, artifact), (part.kind, artifact)
            assert cost.refusal(part, artifact) is None, (part.kind, artifact)


def test_the_refusal_names_the_fields_the_artifact_and_l21_and_prints_no_figure() -> None:
    refusal = cost.refusal(OVER, "stl-fine")
    assert refusal is not None
    assert refusal.startswith("d, pitch, length, s, k and thread_length: ")
    assert "fine STL (stl-fine)" in refusal
    assert "L21" in refusal
    # L02: no predicted figure; the only digits are L21's.
    assert re.findall(r"\d+", refusal) == ["21"]
    fitting = [a for a in ARTIFACTS if a != "stl-fine" and cost.fits(OVER, a)]
    if fitting:
        assert "of this part fit" in refusal
    else:
        assert "no artifact of this part fits" in refusal


def test_an_unvalidated_part_past_exps_range_is_refused_not_an_error() -> None:
    huge = BoltParams.model_construct(d=1e200, pitch=1.0, length=20.0, thread_length=20.0, s=10.0,
                                      k=4.0, left_hand=False)
    assert math.isinf(cost.predict(huge, "stl-fine").bytes)
    assert cost.refusal(huge, "stl-fine") is not None


def test_the_cost_module_imports_no_kernel_no_numpy_and_no_logger() -> None:
    # The import-boundary prohibition of 07-11: `predict` runs on every keystroke via `derive`.
    tree = ast.parse(COST_PY.read_text())
    names = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
             for alias in node.names]
    names += [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    for name in names:
        root = name.split(".")[0]
        assert root not in {"cadquery", "OCP", "numpy", "logging"}, name
        assert not name.startswith("screw.records"), name


# --- every artifact of both kinds through the one rule (07 D-06, D-08, D-17) -------------------

DOWNLOAD_PAIRS = (("stl", "fine"), ("stl", "preview"), ("step", "fine"), ("step", "preview"))


def _explore_parts() -> list[FastenerParams]:
    """Every explore point the parameter model takes: a grid over both kinds and the walls."""
    raw = json.loads((REPO / "bench" / "points" / "explore.json").read_text())
    parts: dict[str, FastenerParams] = {}
    for point in raw["points"]:
        try:
            parts[point["label"]] = KINDS[point["kind"]].model_validate(point["params"])
        except ValidationError:
            continue
    return list(parts.values())


EXPLORE = _explore_parts()


def test_the_explore_grid_holds_refused_and_admitted_parts_of_both_kinds() -> None:
    # The grid below is only a test if it reaches both outcomes on both kinds.
    for kind in ("bolt", "nut"):
        outcomes = {download_refusal(p, fmt, q) is None for p in EXPLORE if p.kind == kind
                    for fmt, q in DOWNLOAD_PAIRS}
        assert outcomes == {True, False}, kind


def test_the_download_rule_is_the_cost_models_for_both_kinds_and_every_pair() -> None:
    for p in EXPLORE:
        for fmt, quality in DOWNLOAD_PAIRS:
            assert download_refusal(p, fmt, quality) == cost.refusal(
                p, artifact_of(fmt, quality)), (p, fmt, quality)
        # STEP ignores the quality: one artifact, one answer.
        assert download_refusal(p, "step", "fine") == download_refusal(p, "step", "preview")


def test_the_all_default_parts_refuse_no_download() -> None:
    for part in (BoltParams(), NutParams()):
        for fmt, quality in DOWNLOAD_PAIRS:
            assert download_refusal(part, fmt, quality) is None, (part.kind, fmt, quality)


def test_each_refusal_is_one_warning_in_download_order_with_the_step_pair_once() -> None:
    # OPER-03's ordering edge: the refusals follow `_DOWNLOADS`, and the STEP pair, one artifact,
    # adds one sentence.
    seen = 0
    for p in EXPLORE:
        reasons = [download_refusal(p, fmt, q) for fmt, q in DOWNLOAD_PAIRS]
        refused = [r for r in dict.fromkeys(reasons) if r is not None]
        if not refused:
            continue
        seen += 1
        warnings = derive(p).warnings
        assert [w for w in warnings if w in refused] == refused, p
        assert all(warnings.count(r) == 1 for r in refused), p
    assert seen


# --- B-03: a defaulted value that pushes a part over is capped and warned (D-06) ---------------

# Bolt d 30, s 48, k 18 at the default pitch, length and thread_length: no row of the table's D-06
# section trims a thread_length, so the part is built from the model as plan 07-12 says. Refused at
# stl-preview and stl-fine (B-03 clarification, 07-OWNER-RULINGS.md, 2026-10-29).
CAP_QUERY = {"d": 30.0, "s": 48.0, "k": 18.0}
CAP_PART = BoltParams.model_validate(CAP_QUERY)


def _grid_between(low: float, high: float, step: float) -> list[float]:
    """The form-step values strictly between `low` and `high`."""
    return [round(i * step, 10) for i in range(round(low / step) + 1, round(high / step))]


def _assert_the_largest_admitted(before: FastenerParams, after: FastenerParams, field: str,
                                 step: float) -> None:
    """`after` is `before` with `field` at the largest form-step value below it that fits every
    artifact, and only that field moved (B-03)."""
    old, new = getattr(before, field), getattr(after, field)
    assert new < old
    assert round(new / step) * step == pytest.approx(new)
    assert after == before.model_copy(update={field: new})
    assert cost.fits_every_artifact(after)
    for value in _grid_between(new, old, step):
        assert not cost.fits_every_artifact(before.model_copy(update={field: value})), value


def test_the_cap_steps_are_the_form_steps_the_schema_publishes() -> None:
    for kind, fields in cost.CAP_STEPS.items():
        properties = KINDS[kind].model_json_schema()["properties"]
        assert [(field, properties[field]["step"]) for field, _ in fields] == list(fields)
    assert {kind: [f for f, _ in fields] for kind, fields in cost.CAP_STEPS.items()} == {
        "bolt": ["thread_length", "length"], "nut": ["m"]}


def test_a_part_admitted_at_every_artifact_is_never_capped_whatever_was_named() -> None:
    # OPER-03's empty edge for the cap path: the defaults and every catalogue row fit (C1).
    rows = ([BoltParams.model_validate(dict(r.fields)) for r in catalogue()]
            + [NutParams.model_validate(dict(r.fields)) for r in nut_catalogue()])
    for part in [BoltParams(), NutParams(), *rows]:
        for explicit in (frozenset(), frozenset(type(part).model_fields)):
            capped, warnings = cost.cap_defaults(part, explicit)
            assert capped is part
            assert warnings == ()


def test_a_defaulted_thread_length_over_the_budget_is_capped_to_the_largest_that_fits() -> None:
    assert [a for a in ARTIFACTS if not cost.fits(CAP_PART, a)] == ["stl-preview", "stl-fine"]
    capped, (warning,) = cost.cap_defaults(CAP_PART, frozenset(CAP_QUERY))
    _assert_the_largest_admitted(CAP_PART, capped, "thread_length", 0.5)
    value = repr(capped.thread_length).removesuffix(".0")
    assert warning == (
        f"thread_length: the default 20 mm puts the preview STL (stl-preview) and fine STL "
        f"(stl-fine) of this bolt over its measured budget (L21), so thread_length is capped at "
        f"{value} mm, the largest value on its 0.5 mm form step at which every artifact fits; give "
        f"thread_length to choose it, and an artifact over the budget is then refused")
    assert "{" not in warning
    # The model's frozen default never moves (L02).
    assert BoltParams.model_fields["thread_length"].default == 20.0


@pytest.mark.parametrize("named", [{"thread_length"}, {"thread_length", "length"}])
def test_a_named_thread_length_keeps_the_part_and_its_refusals(named: set[str]) -> None:
    # Task 1 behaviour 3 and the B-03 clarification: the length cap never goes below a named
    # thread_length, and here no length from 20 down to 20 is left, so the 422s stand (B-02).
    assert cost.cap_defaults(CAP_PART, frozenset(CAP_QUERY) | named) == (CAP_PART, ())
    refusals = {e.quality: e.refusal for e in derive(CAP_PART).downloads if e.format == "stl"}
    assert refusals["fine"] is not None
    assert refusals["preview"] is not None


@pytest.mark.parametrize("thread_length", [20.0, 10.0, 8.0, 0.5])
def test_the_length_cap_never_shortens_a_named_thread_length(thread_length: float) -> None:
    # B-03 clarification, ruling 1, asserted against the rule: whatever a named thread_length is,
    # the capped part builds at least that thread and keeps the field as named.
    for query in ({"d": 30.0, "s": 48.0, "k": 18.0},
                  {"d": 3.0, "pitch": 0.2, "s": 4.5, "k": 1.8}):
        try:
            part = BoltParams.model_validate({**query, "thread_length": thread_length})
        except ValidationError:
            continue    # the M3 at pitch 0.2 is past the 90-turn wall at a 20 mm thread (L20)
        capped, _ = cost.cap_defaults(part, frozenset(query) | {"thread_length"})
        assert capped.thread_length == thread_length
        assert capped.length >= thread_length
        assert built_thread_length(capped.thread_length, capped.length) == built_thread_length(
            part.thread_length, part.length)


def test_a_length_cap_above_a_named_thread_length_is_the_largest_that_fits() -> None:
    # Only the STEP of this M3 is over; with thread_length named, length takes the cap and stops at
    # the largest value that fits, at or above the named 8 mm.
    query = {"d": 3.0, "pitch": 0.2, "s": 4.5, "k": 1.8, "thread_length": 8.0}
    part = BoltParams.model_validate(query)
    assert [a for a in ARTIFACTS if not cost.fits(part, a)] == ["step"]
    capped, (warning,) = cost.cap_defaults(part, frozenset(query))
    _assert_the_largest_admitted(part, capped, "length", 0.5)
    assert capped.length >= 8.0
    assert warning.startswith("length: the default 20 mm puts the STEP (step) of this bolt ")


def test_a_value_off_its_default_counts_as_named_on_direct_construction() -> None:
    # A Python caller that passes no explicit set still never has a chosen value moved.
    part = CAP_PART.model_copy(update={"thread_length": 19.0, "length": 19.0})
    assert not cost.fits_every_artifact(part)
    assert cost.cap_defaults(part) == (part, ())
