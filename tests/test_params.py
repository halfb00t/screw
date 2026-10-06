"""The parameter model is the one inbound boundary: what it accepts and refuses is the product.

Every refusal names the field (L02): a number that cannot be honoured is a 422, never a
quiet clamp, and a field the kind does not define is never ignored.
"""

from __future__ import annotations

import math
import re

import pytest
from pydantic import ValidationError

from screw.params import DEFAULT_KIND, INTERIM_MAX_MM, KINDS, BoltParams

FIELDS = ("d", "pitch", "length")


def test_the_default_kind_is_the_literal_bolt_and_is_registered() -> None:
    # The literal, not `BoltParams.kind`: a link that omits `kind` means bolt forever, so
    # this must fail if someone moves the default to follow the registry (L02, D-09).
    assert DEFAULT_KIND == "bolt"
    assert DEFAULT_KIND in KINDS


def test_every_registry_key_equals_its_class_kind() -> None:
    assert len(KINDS) >= 1
    for key, model in KINDS.items():
        assert key == model.kind


def test_the_frozen_defaults_are_6_1_20_millimetres() -> None:
    p = BoltParams()
    assert (p.d, p.pitch, p.length) == (6.0, 1.0, 20.0)


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [0, -1, math.inf, -math.inf, math.nan])
def test_a_field_refuses_zero_negative_and_non_finite_naming_itself(
        field: str, value: float) -> None:
    # model_validate, not BoltParams(**{field: value}): the typed initialiser refuses a
    # foreign keyword statically, which is the boundary under test here.
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({field: value})
    assert [e["loc"] for e in caught.value.errors()] == [(field,)]


def test_a_foreign_field_is_refused_as_extra_forbidden_naming_it() -> None:
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"m": 5})
    [err] = caught.value.errors()
    assert err["type"] == "extra_forbidden"
    assert err["loc"] == ("m",)


@pytest.mark.parametrize("field", ["d", "length"])
def test_d_and_length_are_accepted_at_the_interim_bound_and_refused_above_it(
        field: str) -> None:
    assert INTERIM_MAX_MM == 1e5
    assert getattr(BoltParams.model_validate({field: 1e5}), field) == 1e5
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({field: math.nextafter(1e5, math.inf)})
    [err] = caught.value.errors()
    assert err["loc"] == (field,)
    assert err["type"] == "less_than_equal"


def test_pitch_has_no_upper_bound() -> None:
    # D-14 names d and length only; pitch against d is a Phase 3 question (D-07).
    assert BoltParams.model_validate({"pitch": 1e300}).pitch == 1e300


def test_the_schema_lists_d_pitch_length_with_ui_metadata() -> None:
    props = BoltParams.model_json_schema()["properties"]
    assert list(props) == ["d", "pitch", "length"]
    for name, prop in props.items():
        assert prop["group"] == "Size", name
        assert prop["unit"] == "mm", name
        assert "step" in prop, name
        # exclusiveMinimum, not minimum: gt=0 must not read as an inclusive HTML min.
        assert prop["exclusiveMinimum"] == 0, name
        assert "minimum" not in prop, name


def test_the_slug_of_the_default_bolt_is_stable() -> None:
    assert BoltParams().slug() == "bolt_d6_pitch1_length20"


@pytest.mark.parametrize("values", [{"d": 1e-9}, {"pitch": 1e300}, {"d": 1e5}])
def test_the_slug_is_filename_safe_for_extreme_values(values: dict[str, float]) -> None:
    # It becomes a Content-Disposition filename and a temp file name (T-01-06).
    assert re.fullmatch(r"[A-Za-z0-9_.+-]+", BoltParams.model_validate(values).slug())


def test_params_are_frozen_and_equal_by_value() -> None:
    a, b = BoltParams(d=8), BoltParams(d=8)
    assert a is not b
    assert a == b
    assert hash(a) == hash(b)
    with pytest.raises(ValidationError):
        a.d = 9  # type: ignore[misc]
