"""The info document: honest numbers, a standing warning, and no number that cannot be one."""

from __future__ import annotations

import math

import pytest

from screw.calc import STANDING_WARNING, derive
from screw.calc.thread import closed_volume
from screw.params import KINDS, BoltParams, FastenerParams

WARNING = "threaded rod: no head, plain-cut thread ends; not a product build"
PROFILE = "ISO 68-1:2023 basic profile"
KEYS = ["d", "pitch", "length", "turns", "volume", "thread_depth", "minor_diameter"]


def _rows(p: BoltParams) -> dict[str, float]:
    return {r.key: r.value for r in derive(p).rows}


def test_the_default_document_lists_the_inputs_then_the_thread_in_a_fixed_order() -> None:
    info = derive(BoltParams())
    assert info.kind == "bolt"
    assert [r.key for r in info.rows] == KEYS
    assert [r.unit for r in info.rows] == ["mm", "mm", "mm", "", "mm³", "mm", "mm"]


def test_the_default_thread_numbers_come_from_the_pinned_profile() -> None:
    rows = _rows(BoltParams())
    assert rows["turns"] == 20.0
    assert rows["volume"] == closed_volume(6.0, 1.0, 20.0)
    # An independently typed 5/8 * sqrt(3)/2 for P = 1.
    assert rows["thread_depth"] == pytest.approx(0.541265877, abs=1e-9)
    assert rows["minor_diameter"] == pytest.approx(6 - 2 * 0.541265877, abs=1e-9)


def test_the_derived_rows_name_the_profile_and_the_hand_is_not_a_row() -> None:
    by_key = {r.key: r for r in derive(BoltParams()).rows}
    assert PROFILE in by_key["thread_depth"].label
    assert PROFILE in by_key["minor_diameter"].label
    assert not any("pitch diameter" in r.label.lower() for r in by_key.values())


def test_turns_is_the_exact_decimal_quotient_not_a_float_division() -> None:
    assert 5.4 / 0.6 != 9.0
    assert _rows(BoltParams(d=3.5, pitch=0.6, length=5.4))["turns"] == 9.0


def test_the_standing_warning_is_first_and_verbatim() -> None:
    assert STANDING_WARNING == WARNING
    assert derive(BoltParams()).warnings[0] == WARNING


def test_a_volume_that_overflows_is_absent_and_explained_not_a_500() -> None:
    # model_construct skips validation: the bounds keep validated input finite, but derive()
    # promises no non-finite number on its own account (D-15, F2). d = 1e200 squares past a
    # float; its minor diameter, 1e200 - 1.08, is finite and stays.
    info = derive(BoltParams.model_construct(d=1e200, pitch=1.0, length=20.0))
    keys = [r.key for r in info.rows]
    assert "volume" not in keys
    assert "minor_diameter" in keys
    assert any("volume" in w for w in info.warnings)
    assert info.warnings[0] == WARNING


def test_an_infinite_diameter_leaves_out_every_row_it_would_make_infinite() -> None:
    info = derive(BoltParams.model_construct(d=math.inf, pitch=1.0, length=20.0))
    keys = [r.key for r in info.rows]
    assert "volume" not in keys
    assert "minor_diameter" not in keys
    assert any("volume" in w for w in info.warnings)
    assert any("minor_diameter" in w for w in info.warnings)
    assert info.warnings[0] == WARNING
    computed = [r for r in info.rows if r.key not in ("d", "pitch", "length")]
    assert all(math.isfinite(r.value) for r in computed)


def test_a_turn_count_that_cannot_be_read_is_absent_and_explained() -> None:
    # Fraction(repr(inf)) raises, which must not leave derive() as an exception.
    info = derive(BoltParams.model_construct(d=6.0, pitch=1.0, length=math.inf))
    assert "turns" not in [r.key for r in info.rows]
    assert any("turns" in w for w in info.warnings)


def test_a_kind_without_an_info_entry_is_a_bug_not_a_user_error() -> None:
    class Orphan(FastenerParams):
        kind = "orphan"

    with pytest.raises(TypeError, match="orphan"):
        derive(Orphan())


def test_every_registered_kind_derives_a_document() -> None:
    assert len(KINDS) >= 1
    for model in KINDS.values():
        assert derive(model()).kind == model.kind
