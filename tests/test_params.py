"""The parameter model is the one inbound boundary: what it accepts and refuses is the product.

Every refusal names the field (L02): a number that cannot be honoured is a 422, never a
quiet clamp, and a field the kind does not define is never ignored.
"""

from __future__ import annotations

import math
import re

import pytest
from pydantic import ValidationError

from screw.params import DEFAULT_KIND, INTERIM_MAX_MM, KINDS, BoltParams, FastenerParams

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


@pytest.mark.parametrize(("field", "extra"), [
    ("d", {}),
    # 250 turns at pitch 400, root radius above 0 at d = 1000: the corner the bound admits
    # (research built d=1e5, pitch=400 at 1e5 mm in 1.74 s).
    ("length", {"pitch": 400.0, "d": 1000.0}),
])
def test_d_and_length_are_accepted_at_the_interim_bound_and_refused_above_it(
        field: str, extra: dict[str, float]) -> None:
    assert INTERIM_MAX_MM == 1e5
    assert getattr(BoltParams.model_validate({**extra, field: 1e5}), field) == 1e5
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({**extra, field: math.nextafter(1e5, math.inf)})
    [err] = caught.value.errors()
    assert err["loc"] == (field,)
    assert err["type"] == "less_than_equal"


def test_a_pitch_with_no_root_radius_is_refused_naming_d_and_pitch() -> None:
    # d = 6 gives a root radius of 0 at pitch 5.5426 (D-04); the refusal is on the model.
    assert BoltParams.model_validate({"pitch": 5.5}).pitch == 5.5
    for pitch in (5.6, 1e300):
        with pytest.raises(ValidationError) as caught:
            BoltParams.model_validate({"pitch": pitch})
        [err] = caught.value.errors()
        assert err["type"] == "pitch_too_coarse"
        assert err["loc"] == ()
        assert err["ctx"]["fields"] == ["d", "pitch"]
        assert err["msg"].startswith("d and pitch: ")


def test_a_length_past_250_turns_is_refused_naming_length_and_pitch() -> None:
    assert BoltParams.model_validate({"length": 250.0}).length == 250.0
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"length": 250.5})
    [err] = caught.value.errors()
    assert err["type"] == "turn_cap"
    assert err["loc"] == ()
    assert err["ctx"]["fields"] == ["length", "pitch"]
    assert err["msg"].startswith("length and pitch: ")


@pytest.mark.parametrize(("pitch", "length"), [(5e-324, 20.0), (1e-310, 1e5)])
def test_a_pitch_past_the_float_range_of_turns_is_a_turn_cap_error_not_an_overflow(
        pitch: float, length: float) -> None:
    # length / pitch is above 1.8e308 here; float() of that quotient used to raise OverflowError,
    # which pydantic does not convert, so the API answered 500 (CR-01).
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"pitch": pitch, "length": length})
    [err] = caught.value.errors()
    assert err["type"] == "turn_cap"
    assert err["ctx"]["fields"] == ["length", "pitch"]
    assert err["msg"].startswith("length and pitch: inf turns is past the 250-turn cap")


def test_the_measured_m4_250_turn_row_is_accepted() -> None:
    # 175 / 0.7 is a float above 250; the user typed exactly 250 turns (Pitfall 2).
    p = BoltParams.model_validate({"d": 4.0, "pitch": 0.7, "length": 175.0})
    assert (p.d, p.pitch, p.length) == (4.0, 0.7, 175.0)


def test_a_field_error_hides_the_model_rules_that_need_every_field() -> None:
    # After-validators run only when every field validated: d = 0 reports d alone, not a
    # pitch_too_coarse computed from a d that was never accepted.
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"d": 0, "pitch": 1e300})
    assert [e["loc"] for e in caught.value.errors()] == [("d",)]


def test_the_schema_lists_d_pitch_left_hand_length_with_ui_metadata() -> None:
    props = BoltParams.model_json_schema()["properties"]
    assert list(props) == ["d", "pitch", "left_hand", "length"]
    for name, prop in props.items():
        assert "title" in prop, name
        assert "unit" in prop, name
        if name == "left_hand":
            continue
        assert prop["group"] == "Size", name
        assert prop["unit"] == "mm", name
        assert "step" in prop, name
        # exclusiveMinimum, not minimum: gt=0 must not read as an inclusive HTML min.
        assert prop["exclusiveMinimum"] == 0, name
        assert "minimum" not in prop, name


def test_the_hand_is_a_boolean_in_the_thread_group_with_no_numeric_bounds() -> None:
    hand = BoltParams.model_json_schema()["properties"]["left_hand"]
    assert hand["type"] == "boolean"
    assert hand["default"] is False
    assert hand["group"] == "Thread"
    assert hand["unit"] == ""
    assert hand["title"]
    assert not {"exclusiveMinimum", "minimum", "maximum", "step"} & set(hand)


def test_the_default_hand_is_right_and_frozen() -> None:
    # A link that omits left_hand means right-hand, forever (D-09, L02).
    assert BoltParams().left_hand is False
    assert FastenerParams.model_fields["left_hand"].default is False


def test_left_hand_parses_a_boolean_and_refuses_anything_else() -> None:
    assert BoltParams.model_validate({"left_hand": "true"}).left_hand is True
    assert BoltParams.model_validate({"left_hand": "false"}).left_hand is False
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"left_hand": "banana"})
    assert [e["loc"] for e in caught.value.errors()] == [("left_hand",)]


def test_the_slug_of_the_default_bolt_is_stable() -> None:
    assert BoltParams().slug() == "bolt_d6_pitch1_left_hand0_length20"


def test_the_slug_tells_the_hands_apart() -> None:
    assert BoltParams(left_hand=True).slug() == "bolt_d6_pitch1_left_hand1_length20"


@pytest.mark.parametrize("values", [
    {"d": 1e5},
    {"d": 0.001, "pitch": 0.0001, "length": 0.01},
    {"length": 1e5, "pitch": 400.0, "d": 1000.0},
])
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
