"""The info document: honest numbers, a standing warning, and no number that cannot be one."""

from __future__ import annotations

import math

import pytest

from screw.calc import SKELETON_WARNING, derive
from screw.params import KINDS, BoltParams, FastenerParams

WARNING = "walking skeleton: plain unthreaded cylinder, not a product build"


def test_the_default_document_lists_d_pitch_length_then_volume() -> None:
    info = derive(BoltParams())
    assert info.kind == "bolt"
    assert [r.key for r in info.rows] == ["d", "pitch", "length", "volume"]
    assert [r.unit for r in info.rows] == ["mm", "mm", "mm", "mm³"]
    volume = info.rows[-1].value
    assert volume == pytest.approx(math.pi * 9 * 20)


def test_the_standing_warning_is_first_and_verbatim() -> None:
    assert SKELETON_WARNING == WARNING
    assert derive(BoltParams()).warnings[0] == WARNING


def test_no_row_is_a_turn_count() -> None:
    # A turns number on an unthreaded body would be a plausible number for a feature that
    # does not exist (CONTEXT specifics).
    assert not any("turn" in r.key.lower() or "turn" in r.label.lower()
                   for r in derive(BoltParams()).rows)


def test_a_volume_that_overflows_is_absent_and_explained_not_a_500() -> None:
    # model_construct skips validation: D-14's bound keeps validated input finite, but
    # derive() promises no non-finite number on its own account (D-15, F2).
    info = derive(BoltParams.model_construct(d=1e200, pitch=1.0, length=20.0))
    assert "volume" not in [r.key for r in info.rows]
    assert any("volume" in w for w in info.warnings)
    assert info.warnings[0] == WARNING


def test_a_non_finite_volume_is_absent_and_explained() -> None:
    info = derive(BoltParams.model_construct(d=math.inf, pitch=1.0, length=20.0))
    assert "volume" not in [r.key for r in info.rows]
    assert any("volume" in w for w in info.warnings)


def test_a_kind_without_an_info_entry_is_a_bug_not_a_user_error() -> None:
    class Orphan(FastenerParams):
        kind = "orphan"

    with pytest.raises(TypeError, match="orphan"):
        derive(Orphan())


def test_every_registered_kind_derives_a_document() -> None:
    assert len(KINDS) >= 1
    for model in KINDS.values():
        assert derive(model()).kind == model.kind
