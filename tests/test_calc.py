"""The info document: honest numbers, a standing warning, and no number that cannot be one."""

from __future__ import annotations

import math

import pytest

from screw.calc import STANDING_WARNING, derive, download_refusal
from screw.calc.thread import bolt_closed_volume, fine_stl_refusal
from screw.params import KINDS, BoltParams, FastenerParams

WARNING = "plain-cut thread ends, no tip chamfer or under-head fillet; not a product build"
PROFILE = "ISO 68-1:2023 basic profile"
KEYS = ["d", "pitch", "length", "thread_length", "shank_length", "turns", "thread_depth",
        "minor_diameter", "s", "across_corners", "k", "volume"]


def _rows(p: BoltParams) -> dict[str, float]:
    return {r.key: r.value for r in derive(p).rows}


def test_the_default_document_lists_the_inputs_the_thread_the_head_then_the_volume() -> None:
    info = derive(BoltParams())
    assert info.kind == "bolt"
    assert [r.key for r in info.rows] == KEYS
    assert [r.unit for r in info.rows] == [
        "mm", "mm", "mm", "mm", "mm", "", "mm", "mm", "mm", "mm", "mm", "mm³"]


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


def test_the_thread_rows_are_the_built_thread_and_the_plain_shank_left_over() -> None:
    # INFO-03: a default M6 x 20 is threaded to the head, so the shank is 0 and t is the length.
    rows = _rows(BoltParams())
    assert (rows["thread_length"], rows["shank_length"]) == (20.0, 0.0)
    labels = {r.key: r.label for r in derive(BoltParams()).rows}
    assert labels["thread_length"] == "Thread length (built)"
    assert labels["shank_length"] == "Plain shank length"
    # An ISO 4014 shape: 20 mm of thread under a 30 mm length leaves 10 mm of plain shank.
    p = BoltParams(length=30.0)
    rows = _rows(p)
    assert (rows["thread_length"], rows["shank_length"], rows["turns"]) == (20.0, 10.0, 20.0)
    assert rows["volume"] == bolt_closed_volume(6.0, 1.0, 30.0, 10.0, 4.0, 20.0)
    assert derive(p).warnings == [STANDING_WARNING]


def test_the_rows_of_a_screw_shorter_than_the_default_thread_read_the_built_thread() -> None:
    # D-08: `?length=10` builds a 10 mm full-thread screw; the stored thread_length stays 20.
    rows = _rows(BoltParams(length=10.0))
    assert (rows["thread_length"], rows["shank_length"], rows["turns"]) == (10.0, 0.0, 10.0)
    assert rows["volume"] == bolt_closed_volume(6.0, 1.0, 10.0, 10.0, 4.0, 10.0)


def test_a_default_thread_below_an_explicit_length_is_built_to_the_length_and_warned() -> None:
    warnings = derive(BoltParams(length=10.0)).warnings
    assert warnings == [STANDING_WARNING,
                        "thread_length 20 (default) exceeds length 10: thread built to the "
                        "full length"]


def test_an_explicit_thread_length_above_the_length_is_built_to_the_length_and_warned() -> None:
    # D-25: direct construction; the model never refuses it.
    warnings = derive(BoltParams(thread_length=30.0)).warnings
    assert warnings[1:] == ["thread_length 30 exceeds length 20: thread built to the full length"]
    warnings = derive(BoltParams(length=10.0, thread_length=30.0)).warnings
    assert warnings[1:] == ["thread_length 30 exceeds length 10: thread built to the full length"]


def test_a_thread_length_equal_to_the_length_has_no_shank_and_no_warning() -> None:
    info = derive(BoltParams(length=30.0, thread_length=30.0))
    assert info.warnings == [STANDING_WARNING]
    assert {r.key: r.value for r in info.rows}["shank_length"] == 0.0


def test_a_shank_too_short_to_model_is_folded_into_the_thread_and_warned() -> None:
    # D-27: 0.0005 mm is below the 0.001 mm the builder can take.
    info = derive(BoltParams(thread_length=19.9995))
    assert info.warnings[1:] == [
        "thread_length 19.9995 leaves a plain shank of 0.0005 mm, shorter than the 0.001 mm the "
        "builder can model: thread built to the full length"]
    rows = {r.key: r.value for r in info.rows}
    assert (rows["thread_length"], rows["shank_length"]) == (20.0, 0.0)


def test_a_shank_of_exactly_the_floor_keeps_its_shank_and_warns_of_nothing() -> None:
    info = derive(BoltParams(thread_length=19.999))
    assert info.warnings == [STANDING_WARNING]
    assert {r.key: r.value for r in info.rows}["thread_length"] == 19.999


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
    info = derive(BoltParams.model_construct(
        d=6.0, pitch=1.0, length=math.inf, thread_length=math.inf))
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
    capped = BoltParams(d=8.0, pitch=1.25, length=67.6, thread_length=67.6)
    refusal = download_refusal(capped, "stl", "fine")
    assert refusal == fine_stl_refusal(8.0, 1.25, 67.6, False)
    assert refusal is not None
    assert download_refusal(capped, "stl", "preview") is None
    assert download_refusal(capped, "step", "fine") is None
    assert download_refusal(capped, "step", "preview") is None
    at_cap = BoltParams(d=8.0, pitch=1.25, length=67.5, thread_length=67.5)
    assert download_refusal(at_cap, "stl", "fine") is None


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
    capped = derive(BoltParams(d=8.0, pitch=1.25, length=67.6, thread_length=67.6))
    assert capped.warnings == [STANDING_WARNING, fine_stl_refusal(8.0, 1.25, 67.6, False)]


def test_no_fine_stl_warning_at_the_cap_or_off_the_measured_rows() -> None:
    for p in (BoltParams(d=8.0, pitch=1.25, length=67.5, thread_length=67.5),
              BoltParams(d=8.0, pitch=1.0, length=67.6, thread_length=67.6)):
        assert derive(p).warnings == [STANDING_WARNING]


def test_the_fine_stl_cap_reads_the_built_thread_not_the_length() -> None:
    # D-22: M8 x 1.25 is capped at 67.5 mm of thread; a 100 mm bolt with 60 mm of it is inside.
    inside = BoltParams(d=8.0, pitch=1.25, length=100.0, thread_length=60.0)
    assert derive(inside).warnings == [STANDING_WARNING]
    assert download_refusal(inside, "stl", "fine") is None
    over = BoltParams(d=8.0, pitch=1.25, length=100.0, thread_length=67.6)
    assert download_refusal(over, "stl", "fine") == fine_stl_refusal(8.0, 1.25, 67.6, False)


def test_a_left_hand_part_is_judged_by_its_own_measured_cap() -> None:
    # L11 measured the left-hand M10 x 60 inside the budget and the right-hand one over it, so
    # the same millimetres are served on one hand and refused on the other (D-21).
    left = BoltParams(d=10.0, pitch=1.5, length=60.0, thread_length=60.0, left_hand=True, s=16.0,
                      k=6.4)
    right = BoltParams(d=10.0, pitch=1.5, length=60.0, thread_length=60.0, s=16.0, k=6.4)
    assert download_refusal(left, "stl", "fine") is None
    assert derive(left).warnings == [STANDING_WARNING]
    refusal = download_refusal(right, "stl", "fine")
    assert refusal == fine_stl_refusal(10.0, 1.5, 60.0, False)
    assert refusal is not None
    assert "right-hand" in refusal
    assert derive(right).warnings == [STANDING_WARNING, refusal]


SHORT_THREAD_WARNING = (
    "thread_length and length: a thread of {t} mm is shorter than the 0.001 mm the builder can "
    "model, so this part is not built; turns and volume not reported")


@pytest.mark.parametrize(("params", "t"), [
    (BoltParams(length=0.0005), "0.0005"),                  # the whole length is the thread
    (BoltParams(length=30.0, thread_length=0.0005), "0.0005"),   # a short thread on a long shank
])
def test_a_thread_too_short_to_build_gets_a_warning_and_no_turns_or_volume(
        params: BoltParams, t: str) -> None:
    # IN-01, L02: the builder refuses this part, so the document prints no number derived from it.
    info = derive(params)
    assert SHORT_THREAD_WARNING.format(t=t) in info.warnings
    keys = [r.key for r in info.rows]
    assert "turns" not in keys
    assert "volume" not in keys
    assert "thread_length" in keys


def test_a_thread_of_exactly_the_floor_is_built_and_reports_turns_and_volume() -> None:
    info = derive(BoltParams(length=0.001))
    assert not any("shorter than the 0.001 mm the builder can model, so this part" in w
                   for w in info.warnings)
    keys = [r.key for r in info.rows]
    assert "turns" in keys
    assert "volume" in keys
