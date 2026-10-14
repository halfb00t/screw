"""The info document: honest numbers, a standing warning, and no number that cannot be one."""

from __future__ import annotations

import math
from collections.abc import Callable

import pytest

from screw import calc
from screw.calc import (
    NUT_NO_ROW_WARNING,
    STANDING_WARNING,
    Download,
    PartInfo,
    PresetMatch,
    derive,
    download_refusal,
    explicit_conflict,
)
from screw.calc.presets import WITHDRAWN_DIN_WRENCH_MM, designation_for, match
from screw.calc.thread import (
    bolt_closed_volume,
    fine_stl_refusal,
    nut_closed_volume,
    section_radius,
    thread_length_conflict,
)
from screw.params import KINDS, BoltParams, FastenerParams, NutParams
from screw.tables.presets import catalogue

WARNING = "plain-cut thread ends, no tip chamfer or under-head fillet; not a product build"
PROFILE = "ISO 68-1:2023 basic profile"
NO_ROW = ("no ISO 4014:2022 or ISO 4017:2022 row matches these fields; "
          "row values not reported")
ROW_KEYS = ["s_min", "e_min", "k_max", "k_min", "dw_min", "b", "lg_max", "ls_min"]
# The default part is the ISO 4017 M6 x 20 row, so it carries that row's five head values.
KEYS = ["d", "pitch", "length", "thread_length", "shank_length", "turns", "thread_depth",
        "minor_diameter", "s", "across_corners", "k", "s_min", "e_min", "k_max", "k_min",
        "dw_min", "volume"]


def _rows(p: BoltParams) -> dict[str, float]:
    return {r.key: r.value for r in derive(p).rows}


def test_the_default_document_lists_the_inputs_the_thread_the_head_then_the_volume() -> None:
    info = derive(BoltParams())
    assert info.kind == "bolt"
    assert [r.key for r in info.rows] == KEYS
    assert [r.unit for r in info.rows] == [
        "mm", "mm", "mm", "mm", "mm", "", "mm", "mm", "mm", "mm", "mm", "mm", "mm", "mm", "mm",
        "mm", "mm³"]


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
    assert derive(p).warnings == [STANDING_WARNING, NO_ROW]


def test_the_rows_of_a_screw_shorter_than_the_default_thread_read_the_built_thread() -> None:
    # D-08: `?length=10` builds a 10 mm full-thread screw; the stored thread_length stays 20.
    rows = _rows(BoltParams(length=10.0))
    assert (rows["thread_length"], rows["shank_length"], rows["turns"]) == (10.0, 0.0, 10.0)
    assert rows["volume"] == bolt_closed_volume(6.0, 1.0, 10.0, 10.0, 4.0, 10.0)


def test_a_default_thread_below_an_explicit_length_is_built_to_the_length_and_warned() -> None:
    warnings = derive(BoltParams(length=10.0)).warnings
    assert warnings == [STANDING_WARNING,
                        "thread_length 20 (default) exceeds length 10: thread built to the "
                        "full length", NO_ROW]


def test_an_explicit_thread_length_above_the_length_is_built_to_the_length_and_warned() -> None:
    # D-25: direct construction; the model never refuses it.
    warnings = derive(BoltParams(thread_length=30.0)).warnings
    assert warnings[1:] == ["thread_length 30 exceeds length 20: thread built to the full length",
                            NO_ROW]
    warnings = derive(BoltParams(length=10.0, thread_length=30.0)).warnings
    assert warnings[1:] == ["thread_length 30 exceeds length 10: thread built to the full length",
                            NO_ROW]


def test_a_thread_length_equal_to_the_length_has_no_shank_and_no_warning() -> None:
    info = derive(BoltParams(length=30.0, thread_length=30.0))  # the ISO 4017 M6 x 30 row
    assert info.warnings == [STANDING_WARNING]
    assert {r.key: r.value for r in info.rows}["shank_length"] == 0.0


def test_a_shank_too_short_to_model_is_folded_into_the_thread_and_warned() -> None:
    # D-27: 0.0005 mm is below the 0.001 mm the builder can take.
    info = derive(BoltParams(thread_length=19.9995))
    assert info.warnings[1:] == [
        "thread_length 19.9995 leaves a plain shank of 0.0005 mm, shorter than the 0.001 mm the "
        "builder can model: thread built to the full length", NO_ROW]
    rows = {r.key: r.value for r in info.rows}
    assert (rows["thread_length"], rows["shank_length"]) == (20.0, 0.0)


def test_a_shank_of_exactly_the_floor_keeps_its_shank_and_warns_of_nothing() -> None:
    info = derive(BoltParams(thread_length=19.999))
    assert info.warnings == [STANDING_WARNING, NO_ROW]
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


def test_every_registered_kind_derives_a_document(part_of: Callable[[str], FastenerParams]) -> None:
    assert len(KINDS) >= 1
    for kind, model in KINDS.items():
        assert derive(part_of(kind)).kind == model.kind


def test_a_nut_document_has_its_rows_in_groups_the_closed_form_volume_and_no_row() -> None:
    p = NutParams(clearance=0.1)
    info = derive(p)
    assert info.kind == "nut"
    assert [(r.key, r.group) for r in info.rows] == [
        ("d", "Thread"), ("pitch", "Thread"), ("s", "Nut"), ("across_corners", "Nut"),
        ("m", "Nut"), ("clearance", "Pair"), ("volume", "Part")]
    values = {r.key: r.value for r in info.rows}
    assert (values["d"], values["pitch"], values["s"], values["m"], values["clearance"]) == (
        6.0, 1.0, 10.0, 5.2, 0.1)
    assert values["across_corners"] == pytest.approx(10.0 / math.cos(math.pi / 6))
    assert values["volume"] == nut_closed_volume(6.0, 1.0, 10.0, 5.2, 0.1)
    assert info.warnings == [STANDING_WARNING, NUT_NO_ROW_WARNING]
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert (info.designation, info.notes) == (None, [])


@pytest.mark.parametrize(("clearance", "text"), [
    (0.0, "clearance 0 is not positive: the pair cannot be proven (PAIR-03)"),
    (-0.05, "clearance -0.05 is not positive: the pair cannot be proven (PAIR-03)"),
])
def test_a_nut_with_a_non_positive_clearance_warns_once_after_the_standing_warning(
        clearance: float, text: str) -> None:
    info = derive(NutParams(clearance=clearance))
    assert info.warnings == [STANDING_WARNING, text, NUT_NO_ROW_WARNING]


@pytest.mark.parametrize("clearance", [5e-324, 0.1])
def test_a_nut_with_a_positive_clearance_has_no_clearance_warning(clearance: float) -> None:
    # 5e-324 is the smallest positive float: still positive, so no warning (PAIR-01, adjacency).
    info = derive(NutParams(clearance=clearance))
    assert info.warnings == [STANDING_WARNING, NUT_NO_ROW_WARNING]


def test_a_nut_download_is_never_refused_until_the_nut_fine_stl_caps_are_measured() -> None:
    # R12 (05-OWNER-READS.md): the probe does not show the rod caps hold on a nut, so no cap is
    # applied. The M10 right rod cap is 56 mm of thread; a nut that tall is served, and the rod's
    # rule is not routed through the nut. This test moves with the open debt item
    # docs/tech_debt/active/2026-10-14-nut-fine-stl-caps-unmeasured.md.
    tall = NutParams(d=10.0, pitch=1.5, s=17.0, m=57.0, clearance=0.1)
    for fmt, quality in (("stl", "fine"), ("stl", "preview"), ("step", "fine"),
                         ("step", "preview")):
        assert download_refusal(tall, fmt, quality) is None
    assert fine_stl_refusal(10.0, 1.5, 57.0, False) is not None, "the rod cap is the control"
    assert all(entry.refusal is None for entry in derive(tall).downloads)


def test_the_nut_closed_form_is_the_prism_less_the_section_times_the_height() -> None:
    # The hexagon written out, and the section by a midpoint sum of r^2 / 2 over the angle of
    # `section_radius`: a different path from `section_area`'s closed form.
    steps = 20000
    section = sum(section_radius(6.0, 1.0, 0.1, (i + 0.5) * 2 * math.pi / steps) ** 2 / 2
                  for i in range(steps)) * 2 * math.pi / steps
    expected = math.sqrt(3) / 2 * 10.0**2 * 5.2 - section * 5.2
    assert nut_closed_volume(6.0, 1.0, 10.0, 5.2, 0.1) == pytest.approx(expected, rel=1e-5)
    # A larger clearance removes more: the nut gets lighter.
    assert nut_closed_volume(6.0, 1.0, 10.0, 5.2, 0.2) < nut_closed_volume(6.0, 1.0, 10.0, 5.2, 0.1)


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


def test_every_registered_kind_has_a_download_rule(
        part_of: Callable[[str], FastenerParams]) -> None:
    for kind in KINDS:
        assert download_refusal(part_of(kind), "stl", "fine") is None


def test_a_capped_part_warns_about_its_fine_stl_after_the_standing_warning() -> None:
    # The document names the refused download in `downloads`; this sentence is the reason the
    # page and `screw info` show.
    capped = derive(BoltParams(d=8.0, pitch=1.25, length=67.6, thread_length=67.6))
    assert capped.warnings == [STANDING_WARNING, NO_ROW,
                               fine_stl_refusal(8.0, 1.25, 67.6, False)]


def test_no_fine_stl_warning_at_the_cap_or_off_the_measured_rows() -> None:
    for p in (BoltParams(d=8.0, pitch=1.25, length=67.5, thread_length=67.5),
              BoltParams(d=8.0, pitch=1.0, length=67.6, thread_length=67.6)):
        assert derive(p).warnings == [STANDING_WARNING, NO_ROW]


def test_the_fine_stl_cap_reads_the_built_thread_not_the_length() -> None:
    # D-22: M8 x 1.25 is capped at 67.5 mm of thread; a 100 mm bolt with 60 mm of it is inside.
    inside = BoltParams(d=8.0, pitch=1.25, length=100.0, thread_length=60.0)
    assert derive(inside).warnings == [STANDING_WARNING, NO_ROW]
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
    assert derive(left).warnings == [STANDING_WARNING]  # an ISO 4017 M10 x 60 row, left-hand
    refusal = download_refusal(right, "stl", "fine")
    assert refusal == fine_stl_refusal(10.0, 1.5, 60.0, False)
    assert refusal is not None
    assert "right-hand" in refusal
    assert derive(right).warnings == [STANDING_WARNING, refusal]


# --- the download state: one entry per served format and quality, from the shared rule ---------

ALL_SERVED = [Download(format="stl", quality="fine", refusal=None),
              Download(format="stl", quality="preview", refusal=None),
              Download(format="step", quality="fine", refusal=None),
              Download(format="step", quality="preview", refusal=None)]


def test_the_default_part_lists_its_four_downloads_in_the_pages_order_none_refused() -> None:
    assert derive(BoltParams()).downloads == ALL_SERVED


def test_a_capped_part_refuses_exactly_its_fine_stl_download_by_the_shared_rule() -> None:
    capped = BoltParams(d=8.0, pitch=1.25, length=67.6, thread_length=67.6)
    downloads = derive(capped).downloads
    assert [(e.format, e.quality) for e in downloads] == [
        ("stl", "fine"), ("stl", "preview"), ("step", "fine"), ("step", "preview")]
    for entry in downloads:
        assert entry.refusal == download_refusal(capped, entry.format, entry.quality)
    sentence = fine_stl_refusal(8.0, 1.25, 67.6, False)
    assert sentence is not None
    assert [e.refusal for e in downloads] == [sentence, None, None, None]


def test_the_fine_stl_warning_is_the_refused_downloads_reasons_once_in_entry_order() -> None:
    info = derive(BoltParams(d=8.0, pitch=1.25, length=67.6, thread_length=67.6))
    reasons = [e.refusal for e in info.downloads if e.refusal is not None]
    assert info.warnings == [STANDING_WARNING, NO_ROW, *reasons]
    assert len(reasons) == 1


def test_a_left_hand_part_refuses_no_download_and_the_right_hand_one_only_its_fine_stl() -> None:
    left = BoltParams(d=10.0, pitch=1.5, length=60.0, thread_length=60.0, left_hand=True, s=16.0,
                      k=6.4)
    right = BoltParams(d=10.0, pitch=1.5, length=60.0, thread_length=60.0, s=16.0, k=6.4)
    assert derive(left).downloads == ALL_SERVED
    sentence = fine_stl_refusal(10.0, 1.5, 60.0, False)
    assert sentence is not None
    assert "right-hand" in sentence
    assert [e.refusal for e in derive(right).downloads] == [sentence, None, None, None]


def test_every_registered_kinds_document_agrees_with_its_download_rule(
        part_of: Callable[[str], FastenerParams]) -> None:
    for kind in KINDS:
        part = part_of(kind)
        downloads = derive(part).downloads
        assert downloads, kind
        for entry in downloads:
            assert entry.refusal == download_refusal(part, entry.format, entry.quality)


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


# --- the preset match and the designation (TABL-06, TABL-07, D-09, D-17) -----------------------


def test_the_default_part_matches_the_iso_4017_m6_x_20_row() -> None:
    info = derive(BoltParams())
    assert info.preset == PresetMatch(
        status="exact", id="iso4017:M6x20", display="ISO 4017 M6 \u00d7 20")
    # The owner's Clause 7 form: ASCII hyphen and x, no property class (04-OWNER-READS.md).
    assert info.designation == "Hexagon head screw ISO 4017 - M6 x 20"


def test_the_designation_never_carries_a_property_class() -> None:
    # TABL-07: printed plastic has no strength grade, so no grade can appear in the text.
    for row in catalogue():
        assert "8.8" not in row.designation
        assert "property" not in row.designation.lower()


def test_a_part_matching_no_row_is_custom_with_no_designation() -> None:
    # M8 x 22 is not a length of the M8 series (16, 20, 25, ...), so this M8 part is no row.
    info = derive(BoltParams(d=8.0, pitch=1.25, s=13.0, k=5.3, length=22.0, thread_length=22.0))
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert info.designation is None


@pytest.mark.parametrize(
    "change",
    [{"s": 10.5}, {"k": 4.5}, {"pitch": 0.75}, {"thread_length": 18.0}, {"length": 22.0}],
    ids=lambda c: next(iter(c)),
)
def test_one_field_off_its_row_reads_custom_and_never_the_nearest_row(
        change: dict[str, float]) -> None:
    # D-09, L02: exact float equality over every field a row defines; a part one field off a
    # row is custom, never snapped to the closest one.
    info = derive(BoltParams.model_validate(change))
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert info.designation is None


def test_another_catalogue_length_matches_its_own_row() -> None:
    info = derive(BoltParams(length=25.0, thread_length=25.0))
    assert info.preset is not None
    assert (info.preset.status, info.preset.id) == ("exact", "iso4017:M6x25")
    assert info.designation == "Hexagon head screw ISO 4017 - M6 x 25"


def test_a_left_hand_part_matches_its_row_but_withholds_the_designation() -> None:
    # left_hand is not a row field, so the part still matches; Clause 7 of both standards gives
    # no left-hand form, so the designation is withheld rather than invented (04-OWNER-READS.md).
    info = derive(BoltParams(left_hand=True))
    assert info.preset == PresetMatch(
        status="exact", id="iso4017:M6x20", display="ISO 4017 M6 \u00d7 20")
    assert info.designation is None


def test_match_and_designation_for_read_the_catalogue_directly() -> None:
    row = match(BoltParams())
    assert row is not None
    assert row.id == "iso4017:M6x20"
    assert designation_for(BoltParams(), row) == row.designation
    assert designation_for(BoltParams(left_hand=True), row) is None
    assert match(BoltParams(s=10.1)) is None


def test_every_catalogue_row_matches_itself_exactly() -> None:
    for row in catalogue():
        part = BoltParams.model_validate(dict(row.fields))
        found = match(part)
        assert found is not None
        assert found.id == row.id


def test_an_iso_4014_bolt_is_recognised_with_the_owners_designation() -> None:
    # THRD-03: b = 26 is the thread length of an M10 x 80 bolt, so this part is the row.
    part = BoltParams(
        d=10.0, pitch=1.5, length=80.0, s=16.0, k=6.4, thread_length=26.0)
    info = derive(part)
    assert info.preset == PresetMatch(
        status="exact", id="iso4014:M10x80", display="ISO 4014 M10 \u00d7 80")
    assert info.designation == "Hexagon head bolt ISO 4014 - M10 x 80"
    # The same length threaded to the head is the ISO 4017 screw, not the bolt.
    full = derive(part.model_copy(update={"thread_length": 80.0}))
    assert full.preset == PresetMatch(
        status="exact", id="iso4017:M10x80", display="ISO 4017 M10 \u00d7 80")
    assert full.designation == "Hexagon head screw ISO 4017 - M10 x 80"
    # A thread length that is neither is custom, never the nearest row.
    other = derive(part.model_copy(update={"thread_length": 30.0}))
    assert other.preset == PresetMatch(status="custom", id=None, display=None)
    assert other.designation is None


# --- the grouped, traceable panel (INFO-03, TYPE-01, D-17, D-18) -------------------------------

M10X80 = BoltParams(d=10.0, pitch=1.5, length=80.0, s=16.0, k=6.4, thread_length=26.0)


def _groups(info: PartInfo) -> list[tuple[str, str]]:
    return [(r.group, r.key) for r in info.rows]


def test_the_rows_sit_in_three_groups_in_server_order() -> None:
    info = derive(BoltParams())
    shank = ["d", "pitch", "length", "thread_length", "shank_length", "turns", "thread_depth",
             "minor_diameter"]
    head = ["s", "across_corners", "k", "s_min", "e_min", "k_max", "k_min", "dw_min"]
    assert _groups(info) == ([("Shank and thread", k) for k in shank]
                             + [("Head", k) for k in head] + [("Part", "volume")])


def test_an_iso_4014_match_adds_b_lg_max_and_ls_min_to_the_shank_group() -> None:
    info = derive(M10X80)
    shank = [k for g, k in _groups(info) if g == "Shank and thread"]
    assert shank == ["d", "pitch", "length", "thread_length", "shank_length", "turns",
                     "thread_depth", "minor_diameter", "b", "lg_max", "ls_min"]
    assert [k for g, k in _groups(info) if g == "Head"] == [
        "s", "across_corners", "k", "s_min", "e_min", "k_max", "k_min", "dw_min"]


def test_a_matched_rows_values_carry_their_sense_and_source_in_the_label() -> None:
    # ISO 4017 prints M6 in Table 1 and M10 in Table 2; the label reads the row's own source.
    labels = {r.key: r.label for r in derive(BoltParams()).rows}
    assert labels["s_min"] == "Across flats, min (ISO 4017:2022 Table 1)"
    assert labels["e_min"] == "Across corners, min (ISO 4017:2022 Table 1)"
    assert labels["k_max"] == "Head height, max (ISO 4017:2022 Table 1)"
    assert labels["k_min"] == "Head height, min (ISO 4017:2022 Table 1)"
    assert labels["dw_min"] == "Bearing face diameter, min (ISO 4017:2022 Table 1)"
    # The geometric number stays a separate row beside the standard's e,min (PITFALLS C7).
    assert labels["across_corners"].startswith("Across corners, geometric")
    m10 = BoltParams(d=10.0, pitch=1.5, length=20.0, s=16.0, k=6.4, thread_length=20.0)
    assert {r.key: r.label for r in derive(m10).rows}["s_min"] == (
        "Across flats, min (ISO 4017:2022 Table 2)")


def test_the_default_rows_equal_the_stored_iso_4017_m6_head() -> None:
    row = match(BoltParams())
    assert row is not None
    values = _rows(BoltParams())
    head = row.head
    assert (values["s_min"], values["e_min"], values["k_max"], values["k_min"],
            values["dw_min"]) == (head.s_min, head.e_min, head.k_max, head.k_min, head.dw_min)
    assert {"b", "lg_max", "ls_min"}.isdisjoint(values)  # TYPE-01: a screw has no b


def test_an_iso_4014_match_reports_the_stored_band_and_cell() -> None:
    row = match(M10X80)
    assert row is not None
    assert row.band is not None
    assert row.cell is not None
    info = derive(M10X80)
    values = _rows(M10X80)
    assert (values["b"], values["lg_max"], values["ls_min"]) == (
        row.band.b_short, row.cell.lg_max, row.cell.ls_min)
    labels = {r.key: r.label for r in info.rows}
    assert labels["b"] == f"Thread length b, ref (ISO 4014:2022 {row.band.source.table})"
    assert labels["lg_max"] == f"Grip length lg, max (ISO 4014:2022 {row.cell.source.table})"
    assert labels["ls_min"] == (
        f"Plain shank length ls, min (ISO 4014:2022 {row.cell.source.table})")
    assert labels["s_min"] == f"Across flats, min (ISO 4014:2022 {row.head.source.table})"


def test_every_catalogue_row_reports_its_own_stored_values_with_its_own_source() -> None:
    for row in catalogue():
        info = derive(BoltParams.model_validate(dict(row.fields)))
        by_key = {r.key: r for r in info.rows}
        head = row.head
        for key, value in (("s_min", head.s_min), ("e_min", head.e_min), ("k_max", head.k_max),
                           ("k_min", head.k_min), ("dw_min", head.dw_min)):
            assert by_key[key].value == value, (row.id, key)
            assert by_key[key].label.endswith(f"({head.source.standard}:2022 {head.source.table})")
        if row.band is None or row.cell is None:
            assert {"b", "lg_max", "ls_min"}.isdisjoint(by_key), row.id
            continue
        b = row.band.b_short if row.length <= 125 else row.band.b_long
        assert by_key["b"].value == b, row.id
        assert by_key["lg_max"].value == row.cell.lg_max, row.id
        assert by_key["ls_min"].value == row.cell.ls_min, row.id


def test_a_non_coarse_pitch_builds_with_no_row_value_and_one_honest_warning() -> None:
    info = derive(BoltParams(pitch=0.75))
    assert {r.key for r in info.rows}.isdisjoint(ROW_KEYS)
    assert info.warnings == [STANDING_WARNING, NO_ROW]
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert info.designation is None
    assert {r.group for r in info.rows} == {"Shank and thread", "Head", "Part"}


def test_an_edited_field_drops_every_row_value_never_the_nearest_row() -> None:
    for change in ({"length": 21.0}, {"s": 10.5}, {"k": 4.1}, {"d": 6.5}, {"thread_length": 19.0}):
        info = derive(BoltParams.model_validate(change))
        assert {r.key for r in info.rows}.isdisjoint(ROW_KEYS), change
        assert info.warnings[-1] == NO_ROW, change


def test_an_iso_4014_part_with_an_edited_thread_length_reports_no_b_lg_max_or_ls_min() -> None:
    # TYPE-01: b is the standard's, not the user's; 30 is not it, so no row and no b.
    info = derive(M10X80.model_copy(update={"thread_length": 30.0}))
    assert {r.key for r in info.rows}.isdisjoint(ROW_KEYS)
    assert info.warnings[-1] == NO_ROW


def test_the_no_row_warning_follows_the_thread_warnings_and_precedes_the_fine_stl_one() -> None:
    # M8 x 1.25 over 67.5 mm of thread is capped (D-22); thread_length 80 exceeds length 70.
    info = derive(BoltParams(d=8.0, pitch=1.25, length=70.0, thread_length=80.0))
    refusal = fine_stl_refusal(8.0, 1.25, 70.0, False)
    assert info.warnings == [
        STANDING_WARNING,
        "thread_length 80 exceeds length 70: thread built to the full length",
        NO_ROW, refusal]


# --- the notes: product grade and the ISO versus withdrawn DIN wrench size (D-20, INFO-05) -----

GRADE_A = "product grade A (ISO 4017:2022: l ≤ 150 mm and l ≤ 10 d)"


def _row_part(row_id: str) -> BoltParams:
    row = next(r for r in catalogue() if r.id == row_id)
    return BoltParams.model_validate(dict(row.fields))


def test_the_default_part_notes_its_product_grade_and_nothing_else() -> None:
    assert derive(BoltParams()).notes == [GRADE_A]


def test_a_grade_b_row_notes_grade_b() -> None:
    notes = derive(_row_part("iso4017:M16x160")).notes
    assert notes == ["product grade B (ISO 4017:2022: l > 150 mm)"]


def test_the_grade_note_names_the_matched_standard() -> None:
    notes = derive(M10X80).notes
    assert notes[0] == "product grade A (ISO 4014:2022: l ≤ 150 mm and l ≤ 10 d)"


@pytest.mark.parametrize(("row_id", "note"), [
    ("iso4017:M10x40", "wrench size 16 mm (ISO 4017:2022); the withdrawn DIN 933 used 17 mm"),
    ("iso4017:M12x40", "wrench size 18 mm (ISO 4017:2022); the withdrawn DIN 933 used 19 mm"),
    ("iso4017:M14x40", "wrench size 21 mm (ISO 4017:2022); the withdrawn DIN 933 used 22 mm"),
    ("iso4014:M10x80", "wrench size 16 mm (ISO 4014:2022); the withdrawn DIN 931 used 17 mm"),
    ("iso4014:M12x80", "wrench size 18 mm (ISO 4014:2022); the withdrawn DIN 931 used 19 mm"),
    ("iso4014:M14x80", "wrench size 21 mm (ISO 4014:2022); the withdrawn DIN 931 used 22 mm"),
])
def test_the_wrench_note_at_m10_m12_and_m14_is_the_second_note(row_id: str, note: str) -> None:
    notes = derive(_row_part(row_id)).notes
    assert len(notes) == 2
    assert notes[1] == note


def test_the_wrench_note_appears_on_those_three_sizes_and_no_others() -> None:
    # INFO-05: only M10, M12 and M14 differ between the ISO and the withdrawn DIN wrench size.
    sizes_with_note = {row.size for row in catalogue()
                       if len(derive(BoltParams.model_validate(dict(row.fields))).notes) == 2}
    assert sizes_with_note == {"M10", "M12", "M14"}
    for row_id in ("iso4017:M8x40", "iso4017:M16x40", "iso4017:M20x40", "iso4014:M8x80"):
        assert len(derive(_row_part(row_id)).notes) == 1, row_id


def test_the_iso_wrench_size_differs_from_the_cited_din_one_wherever_a_note_is_made() -> None:
    # The note's premise: if the shipped s ever equalled the DIN value, "used 17" would be noise.
    for row in catalogue():
        din = WITHDRAWN_DIN_WRENCH_MM.get(row.size)
        if din is not None:
            assert row.head.s != din, row.id


def test_a_part_that_matches_no_row_has_no_notes_at_m10_either() -> None:
    off = _row_part("iso4017:M10x40").model_copy(update={"length": 41.0, "thread_length": 41.0})
    info = derive(off)
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert info.notes == []
    assert derive(BoltParams(length=10.0)).notes == []


# ------------------------------------ explicit-conflict rule per kind (D-25, WR-02)


def test_every_registered_kind_states_its_explicit_conflict_rule() -> None:
    # A kind without an entry would raise here, so a new kind cannot inherit the bolt's rule or
    # escape it unnoticed; an empty request conflicts with nothing.
    for kind in KINDS:
        assert explicit_conflict(kind, {}) is None


def test_a_kind_without_an_entry_has_no_rule_and_says_so(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # `nut` is registered, so the missing entry is made by dropping its own: the lookup raises
    # instead of falling back to the bolt's rule.
    monkeypatch.setattr(
        calc, "_EXPLICIT_CONFLICTS",
        {k: v for k, v in calc._EXPLICIT_CONFLICTS.items() if k != "nut"})
    with pytest.raises(TypeError, match="no explicit-conflict rule registered for kind 'nut'"):
        explicit_conflict("nut", {"length": 10.0, "thread_length": 30.0})


def test_the_bolt_rule_judges_two_explicit_floats_and_names_both_fields() -> None:
    conflict = explicit_conflict("bolt", {"length": 10.0, "thread_length": 30.0})
    assert conflict is not None
    assert conflict.type == "thread_length_conflict"
    assert conflict.fields == ("thread_length", "length")
    assert conflict.msg == thread_length_conflict(10.0, 30.0)
    assert explicit_conflict("bolt", {"length": 10.0, "thread_length": 10.0}) is None


def test_the_bolt_rule_needs_both_values_as_floats() -> None:
    # One value alone is the default's case (a warning, not a 422); a string is the model's to
    # refuse by name.
    assert explicit_conflict("bolt", {"length": 10.0}) is None
    assert explicit_conflict("bolt", {"thread_length": 30.0}) is None
    assert explicit_conflict("bolt", {"length": 10.0, "thread_length": "30"}) is None
