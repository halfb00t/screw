"""The parameter model is the one inbound boundary: what it accepts and refuses is the product.

Every refusal names the field (L02): a number that cannot be honoured is a 422, never a
quiet clamp, and a field the kind does not define is never ignored.
"""

from __future__ import annotations

import math
import re

import pytest
from pydantic import ValidationError

from screw.params import DEFAULT_KIND, INTERIM_MAX_MM, KINDS, BoltParams, FastenerParams, NutParams
from screw.tables import iso4032
from screw.tables.presets import expand

FIELDS = ("d", "pitch", "length", "s", "k", "thread_length")


def test_the_default_kind_is_the_literal_bolt_and_is_registered() -> None:
    # The literal, not `BoltParams.kind`: a link that omits `kind` means bolt forever, so
    # this must fail if someone moves the default to follow the registry (L02, D-09).
    assert DEFAULT_KIND == "bolt"
    assert DEFAULT_KIND in KINDS


def test_every_registry_key_equals_its_class_kind() -> None:
    assert len(KINDS) >= 1
    for key, model in KINDS.items():
        assert key == model.kind


def test_the_frozen_defaults_are_the_iso_4017_m6_row_the_owner_confirmed() -> None:
    # D-07, L02: the owner's opening read (04-OWNER-READS.md) confirmed s 10.0 and k 4.0 for
    # ISO 4017:2022 M6 and typed `permanent: accepted`. The literals, so moving one fails here.
    p = BoltParams()
    assert (p.d, p.pitch, p.length, p.s, p.k) == (6.0, 1.0, 20.0, 10.0, 4.0)


def test_the_nut_defaults_are_the_iso_4032_m6_values_the_owner_accepted() -> None:
    # D-15, L02, TYPE-03: the literals of 05-OWNER-READS.md (s max 10.0, m max 5.2, read from a
    # secondary source the owner approved), typed `permanent: accepted`. A link that omits s or m
    # means these values forever, so moving one fails here.
    p = NutParams(clearance=0.0)
    assert (p.d, p.pitch, p.left_hand, p.s, p.m) == (6.0, 1.0, False, 10.0, 5.2)
    assert NutParams.model_fields["s"].default == 10.0
    assert NutParams.model_fields["m"].default == 5.2


def test_the_frozen_nut_defaults_are_the_iso_4032_m6_row_the_owner_confirmed() -> None:
    # D-15, L14: the M6 cross-check of 05-OWNER-READS.md (2026-10-20, GOST ISO 4032-2014 Table 1)
    # matched the two frozen values: s 10.00 (nominal = max) and m max 5.20. The literals, so
    # moving one fails here whatever the table says.
    assert NutParams.model_fields["s"].default == 10.0
    assert NutParams.model_fields["m"].default == 5.2


def test_the_frozen_nut_defaults_are_the_iso_4032_m6_row() -> None:
    # The same two values, read back from the cited M6 row: a table edit that moves M6 fails here
    # instead of leaving the default link describing a part no standard has.
    m6 = next(nut for nut in iso4032.NUTS if nut.size == "M6")
    assert NutParams.model_fields["s"].default == m6.s
    assert NutParams.model_fields["m"].default == m6.m_max


def test_the_clearance_default_is_the_frozen_value_l17_records() -> None:
    # PAIR-02, L02, L17: the literal 0.15 mm, so moving it fails here. A link that omits clearance
    # means this value forever; the record it was read from is re-derived in test_print_rules.
    field = NutParams.model_fields["clearance"]
    assert not field.is_required()
    assert field.default == 0.15
    assert NutParams().clearance == 0.15


def test_a_nut_clearance_may_be_nominal_or_an_interference() -> None:
    # D-04: no lower bound, so 0 (nominal) and a negative value are inputs the model accepts.
    assert NutParams(clearance=0.0).clearance == 0.0
    assert NutParams(clearance=-0.05).clearance == -0.05


def test_the_frozen_defaults_are_the_iso_4017_m6_x_20_row() -> None:
    # D-07: closes 01 D-05's ASSUMPTION. The defaults are absolute millimetres (L02) and must
    # also be a cited table row, so a table edit that moves M6 x 20 fails here instead of leaving
    # the default link describing a part no standard has.
    row = expand("iso4017:M6x20")
    assert row is not None
    p = BoltParams()
    assert {name: getattr(p, name) for name in row} == row


def test_the_default_thread_length_is_the_frozen_20_and_never_follows_the_length() -> None:
    # D-08, L02: a link that omits thread_length means 20.0 forever; the builder derives the
    # thread it builds, the stored field is never rewritten.
    assert BoltParams().thread_length == 20.0
    assert BoltParams.model_fields["thread_length"].default == 20.0
    assert BoltParams(length=10.0).thread_length == 20.0


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
    # d at the bound needs s above it, which s's own bound forbids: the whole value is refused by
    # head_too_small, so d is tested at the bound below.
    # 250 turns at pitch 400, root radius above 0 at d = 1000, a head wider than d (D-23): the
    # corner the bound admits (research built d=1e5, pitch=400 at 1e5 mm in 1.74 s).
    ("length", {"pitch": 400.0, "d": 1000.0, "s": 1500.0, "k": 600.0}),
    ("s", {}),
    ("k", {}),
    # 250 turns at pitch 400 needs the thread as long as the length (D-22, D-23).
    ("thread_length", {"pitch": 400.0, "d": 1000.0, "s": 1500.0, "k": 600.0, "length": 1e5}),
])
def test_length_s_k_and_thread_length_are_accepted_at_the_interim_bound_and_refused_above_it(
        field: str, extra: dict[str, float]) -> None:
    assert INTERIM_MAX_MM == 1e5
    assert getattr(BoltParams.model_validate({**extra, field: 1e5}), field) == 1e5
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({**extra, field: math.nextafter(1e5, math.inf)})
    [err] = caught.value.errors()
    assert err["loc"] == (field,)
    assert err["type"] == "less_than_equal"


def test_d_at_the_interim_bound_is_head_too_small_and_the_next_float_names_d() -> None:
    # s cannot exceed INTERIM_MAX_MM, so d = INTERIM_MAX_MM can never have a head wider than it
    # (D-23); one float above is the bound itself, caught on the field before any model rule.
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"d": 1e5, "s": 1e5})
    [err] = caught.value.errors()
    assert err["type"] == "head_too_small"
    assert err["loc"] == ()
    assert err["ctx"]["fields"] == ["s", "d"]
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"d": math.nextafter(1e5, math.inf)})
    [err] = caught.value.errors()
    assert (err["loc"], err["type"]) == (("d",), "less_than_equal")


def test_a_head_no_wider_than_the_shank_is_refused_naming_s_and_d() -> None:
    # D-23: product policy. s one float above d is a hex head and is accepted; s equal to d or
    # below is the model-level error, whose message starts `s and d: ` for the CLI (no loc).
    assert BoltParams.model_validate({"s": math.nextafter(6.0, math.inf)}).s > 6.0
    for s in (6.0, 5.0):
        with pytest.raises(ValidationError) as caught:
            BoltParams.model_validate({"s": s})
        [err] = caught.value.errors()
        assert err["type"] == "head_too_small"
        assert err["loc"] == ()
        assert err["ctx"]["fields"] == ["s", "d"]
        assert err["msg"].startswith("s and d: ")
        assert "must exceed" in err["msg"]


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


def test_a_thread_past_250_turns_is_refused_naming_thread_length_length_and_pitch() -> None:
    both = {"length": 250.0, "thread_length": 250.0}
    assert BoltParams.model_validate(both).thread_length == 250.0
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"length": 250.5, "thread_length": 250.5})
    [err] = caught.value.errors()
    assert err["type"] == "turn_cap"
    assert err["loc"] == ()
    assert err["ctx"]["fields"] == ["thread_length", "length", "pitch"]
    assert err["msg"].startswith("thread_length, length and pitch: ")


def test_a_long_length_with_a_short_thread_is_accepted_the_cap_reads_the_built_thread() -> None:
    # D-22: the 250-turn cap bounds the thread, the shank is one cylinder.
    assert BoltParams.model_validate({"length": 1e5}).length == 1e5
    assert BoltParams.model_validate({"length": 250.5}).length == 250.5


def test_a_thread_length_above_the_length_is_accepted_by_the_model() -> None:
    # D-25, the owner's ruling: direct construction is built to the length and warned by derive;
    # the refusal of two explicit values lives at the request boundary (plan 04-05), not here.
    p = BoltParams(length=10.0, thread_length=30.0)
    assert (p.length, p.thread_length) == (10.0, 30.0)


@pytest.mark.parametrize(("pitch", "length"), [(5e-324, 20.0), (1e-310, 1e5)])
def test_a_pitch_past_the_float_range_of_turns_is_a_turn_cap_error_not_an_overflow(
        pitch: float, length: float) -> None:
    # length / pitch is above 1.8e308 here; float() of that quotient used to raise OverflowError,
    # which pydantic does not convert, so the API answered 500 (CR-01).
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"pitch": pitch, "length": length})
    [err] = caught.value.errors()
    assert err["type"] == "turn_cap"
    assert err["ctx"]["fields"] == ["thread_length", "length", "pitch"]
    assert err["msg"].startswith(
        "thread_length, length and pitch: inf turns of built thread is past the 250-turn cap")


def test_the_measured_m4_250_turn_row_is_accepted() -> None:
    # 175 / 0.7 is a float above 250; the user typed exactly 250 turns (Pitfall 2).
    p = BoltParams.model_validate({"d": 4.0, "pitch": 0.7, "length": 175.0, "thread_length": 175.0})
    assert (p.d, p.pitch, p.length, p.thread_length) == (4.0, 0.7, 175.0, 175.0)


def test_a_field_error_hides_the_model_rules_that_need_every_field() -> None:
    # After-validators run only when every field validated: d = 0 reports d alone, not a
    # pitch_too_coarse computed from a d that was never accepted.
    with pytest.raises(ValidationError) as caught:
        BoltParams.model_validate({"d": 0, "pitch": 1e300})
    assert [e["loc"] for e in caught.value.errors()] == [("d",)]


def test_the_schema_lists_the_fields_with_ui_metadata() -> None:
    props = BoltParams.model_json_schema()["properties"]
    assert list(props) == ["d", "pitch", "left_hand", "length", "s", "k", "thread_length"]
    for name, prop in props.items():
        assert "title" in prop, name
        assert "unit" in prop, name
        if name == "left_hand":
            continue
        group = {"s": "Head", "k": "Head", "thread_length": "Thread"}.get(name, "Size")
        assert prop["group"] == group, name
        assert prop["unit"] == "mm", name
        assert "step" in prop, name
        # exclusiveMinimum, not minimum: gt=0 must not read as an inclusive HTML min.
        assert prop["exclusiveMinimum"] == 0, name
        assert "minimum" not in prop, name


def test_the_thread_length_is_a_millimetre_field_in_the_thread_group() -> None:
    prop = BoltParams.model_json_schema()["properties"]["thread_length"]
    assert (prop["title"], prop["group"], prop["unit"]) == ("Thread length", "Thread", "mm")
    assert prop["default"] == 20.0


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
    assert BoltParams().slug() == "bolt_d6_pitch1_left_hand0_length20_s10_k4_thread_length20"


def test_the_slug_tells_the_hands_apart() -> None:
    assert BoltParams(left_hand=True).slug() == (
        "bolt_d6_pitch1_left_hand1_length20_s10_k4_thread_length20")


@pytest.mark.parametrize("values", [
    {"d": 99999.0, "s": 1e5, "k": 1e5},
    {"d": 0.001, "pitch": 0.0001, "length": 0.01, "s": 0.002, "k": 0.001},
    {"length": 1e5, "pitch": 400.0, "d": 1000.0, "s": 1500.0, "k": 600.0},
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
