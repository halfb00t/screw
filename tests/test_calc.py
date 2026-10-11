"""The info document: honest numbers, a standing warning, and no number that cannot be one."""

from __future__ import annotations

import math

import pytest

from screw.calc import STANDING_WARNING, derive, download_refusal
from screw.calc.thread import bolt_closed_volume, fine_stl_refusal
from screw.params import KINDS, BoltParams, FastenerParams

WARNING = "plain-cut thread ends, no tip chamfer or under-head fillet; not a product build"
PROFILE = "ISO 68-1:2023 basic profile"
KEYS = ["d", "pitch", "length", "turns", "thread_depth", "minor_diameter", "s", "across_corners",
        "k", "volume"]


def _rows(p: BoltParams) -> dict[str, float]:
    return {r.key: r.value for r in derive(p).rows}


def test_the_default_document_lists_the_inputs_the_thread_the_head_then_the_volume() -> None:
    info = derive(BoltParams())
    assert info.kind == "bolt"
    assert [r.key for r in info.rows] == KEYS
    assert [r.unit for r in info.rows] == [
        "mm", "mm", "mm", "", "mm", "mm", "mm", "mm", "mm", "mm³"]


def test_the_default_thread_numbers_come_from_the_pinned_profile() -> None:
    rows = _rows(BoltParams())
    assert rows["turns"] == 20.0
    # The whole-part closed form, never the kernel's Volume() (L02, INFO-03): the section area
    # times the thread plus the sharp-cornered hexagonal prism, (sqrt(3) / 2) * s^2 * k.
    assert rows["volume"] == bolt_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0)
    assert rows["volume"] == pytest.approx(459.14408096158724 + 200 * math.sqrt(3), abs=1e-9)
    # An independently typed 5/8 * sqrt(3)/2 for P = 1.
    assert rows["thread_depth"] == pytest.approx(0.541265877, abs=1e-9)
    assert rows["minor_diameter"] == pytest.approx(6 - 2 * 0.541265877, abs=1e-9)


def test_the_head_rows_are_the_fields_and_the_geometric_across_corners() -> None:
    rows = _rows(BoltParams())
    assert (rows["s"], rows["k"]) == (10.0, 4.0)
    # A float, never rounded by the server: the same expression the row is computed from.
    assert rows["across_corners"] == 10.0 / math.cos(math.pi / 6)
    assert rows["across_corners"] == pytest.approx(11.547005383792516, abs=1e-12)
    labels = {r.key: r.label for r in derive(BoltParams()).rows}
    assert "geometric" in labels["across_corners"]


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
    info = derive(BoltParams.model_construct(d=1e200, pitch=1.0, length=20.0, s=10.0, k=4.0))
    keys = [r.key for r in info.rows]
    assert "volume" not in keys
    assert "minor_diameter" in keys
    assert {"s", "across_corners", "k"} <= set(keys)  # the head rows do not depend on d
    assert any("volume" in w for w in info.warnings)
    assert info.warnings[0] == WARNING


def test_an_infinite_diameter_leaves_out_every_row_it_would_make_infinite() -> None:
    info = derive(BoltParams.model_construct(d=math.inf, pitch=1.0, length=20.0, s=10.0, k=4.0))
    keys = [r.key for r in info.rows]
    assert "volume" not in keys
    assert "minor_diameter" not in keys
    assert any("volume" in w for w in info.warnings)
    assert any("minor_diameter" in w for w in info.warnings)
    assert info.warnings[0] == WARNING
    computed = [r for r in info.rows if r.key not in ("d", "pitch", "length")]
    assert computed  # an empty list would pass the loop below vacuously
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


def test_only_the_fine_stl_of_a_capped_part_is_refused() -> None:
    capped = BoltParams(d=8.0, pitch=1.25, length=67.6)
    refusal = download_refusal(capped, "stl", "fine")
    assert refusal == fine_stl_refusal(8.0, 1.25, 67.6, False)
    assert refusal is not None
    assert download_refusal(capped, "stl", "preview") is None
    assert download_refusal(capped, "step", "fine") is None
    assert download_refusal(capped, "step", "preview") is None
    assert download_refusal(BoltParams(d=8.0, pitch=1.25, length=67.5), "stl", "fine") is None


def test_a_kind_without_a_download_rule_is_a_bug_not_a_user_error() -> None:
    class Orphan(FastenerParams):
        kind = "orphan"

    with pytest.raises(TypeError, match="orphan"):
        download_refusal(Orphan(), "step", "preview")


def test_every_registered_kind_has_a_download_rule() -> None:
    for model in KINDS.values():
        assert download_refusal(model(), "stl", "fine") is None


def test_a_capped_part_warns_about_its_fine_stl_after_the_standing_warning() -> None:
    # The page's Download STL link asks for the fine default, so the page says so first.
    capped = derive(BoltParams(d=8.0, pitch=1.25, length=67.6))
    assert capped.warnings == [STANDING_WARNING, fine_stl_refusal(8.0, 1.25, 67.6, False)]


def test_no_fine_stl_warning_at_the_cap_or_off_the_measured_rows() -> None:
    for p in (BoltParams(d=8.0, pitch=1.25, length=67.5),
              BoltParams(d=8.0, pitch=1.0, length=67.6)):
        assert derive(p).warnings == [STANDING_WARNING]


def test_a_left_hand_part_is_judged_by_its_own_measured_cap() -> None:
    # L11 measured the left-hand M10 x 60 inside the budget and the right-hand one over it, so
    # the same millimetres are served on one hand and refused on the other (D-21).
    left = BoltParams(d=10.0, pitch=1.5, length=60.0, left_hand=True, s=16.0, k=6.4)
    right = BoltParams(d=10.0, pitch=1.5, length=60.0, s=16.0, k=6.4)
    assert download_refusal(left, "stl", "fine") is None
    assert derive(left).warnings == [STANDING_WARNING]
    refusal = download_refusal(right, "stl", "fine")
    assert refusal == fine_stl_refusal(10.0, 1.5, 60.0, False)
    assert refusal is not None
    assert "right-hand" in refusal
    assert derive(right).warnings == [STANDING_WARNING, refusal]
