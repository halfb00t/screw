"""The per-artifact vocabulary the build timeout, the budgets and the cost model share (D-09).

One name per file a download can produce, so a timeout, a budget and a measured cost all key
on the same three strings.
"""

from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path

import pytest

from bench import oper_fit
from screw.calc import cost
from screw.calc.cost import ARTIFACTS, BUILD_TIMEOUT_S, artifact_of
from screw.params import BoltParams, FastenerParams, NutParams


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


def test_the_shipped_constants_are_the_block_emit_constants_writes_from_the_evidence() -> None:
    # T-07-29: generated from fit.json and the owner's B-01 table, never typed.
    block = oper_fit.emit_constants(_document(), RULINGS.read_text())
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


@pytest.mark.parametrize("part", [BoltParams(), NutParams(), OVER,
                                  BoltParams(d=8.0, pitch=1.25, length=70.0, thread_length=80.0,
                                             left_hand=True),
                                  NutParams(d=30.0, pitch=0.35, s=48.0, m=24.0, clearance=0.15)],
                         ids=["bolt", "nut", "over", "bolt-left-past", "nut-fine-pitch"])
def test_the_prediction_is_the_fits_own_for_every_artifact(part: FastenerParams) -> None:
    models = oper_fit.models_of(_document())
    params = part.model_dump()
    for artifact in ARTIFACTS:
        predicted = cost.predict(part, artifact)
        for target, value in zip(cost.TARGETS, predicted, strict=True):
            want = oper_fit.predict(models[part.kind, artifact, target], params)
            assert value == pytest.approx(want, rel=1e-12), (artifact, target)


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
