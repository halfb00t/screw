"""The info document: honest numbers, a standing warning, and no number that cannot be one."""

from __future__ import annotations

import math
import subprocess
import sys
from collections.abc import Callable
from typing import cast

import pytest
from fastapi.testclient import TestClient

from screw import calc
from screw.app import app, build_backend
from screw.calc import (
    NO_FILLET_NOTE,
    NUT_NO_ROW_WARNING,
    SHARP_HEAD_NOTE,
    STANDING_WARNING,
    Counterpart,
    Download,
    ExplicitConflict,
    PartInfo,
    PresetMatch,
    derive,
    download_refusal,
    explicit_conflict,
    printability,
)
from screw.calc.presets import WITHDRAWN_DIN_WRENCH_MM, designation_for, match
from screw.calc.thread import (
    TIP_ANGLE_DEG,
    axial_play,
    basic_minor_diameter,
    bolt_end_closed_volume,
    fine_stl_refusal,
    flank_normal_gap,
    head_chamfer_conflict,
    head_chamfer_depths,
    head_chamfer_warnings,
    nut_closed_volume,
    nut_end_closed_volume,
    nut_fine_stl_refusal,
    pitch_diameter,
    section_radius,
    thread_depth,
    thread_length_conflict,
    tip_cone_length,
    tip_cone_volume,
)
from screw.params import KINDS, BoltParams, FastenerParams, NutParams
from screw.solid import Format, Quality, export
from screw.tables import iso262
from screw.tables.gost16093 import BOLT_LIMITS, NUT_LIMITS
from screw.tables.iso4017 import HEADS
from screw.tables.iso4032 import NUTS
from screw.tables.presets import catalogue, expand_nut
from screw.tables.rows import HexNut

WARNING = ("ends modelled per L15 and L19: bolt tip chamfer, hex head chamfer, under-head fillet "
           "on an ISO 4014 plain shank, nut lead-in countersinks and face chamfers; nominal, "
           "not toleranced; not a product build")
PROFILE = "ISO 68-1:2023 basic profile"
NO_ROW = ("no ISO 4014:2022 or ISO 4017:2022 row matches these fields; "
          "row values not reported")
# L14 Citations: the nut's rows cite the GOST text actually read, with the ISO edition it adopts.
NUT_NO_ROW = ("no GOST ISO 4032-2014 (ISO 4032:2012) row matches these fields; "
              "row values not reported")
GOST = "GOST ISO 4032-2014 (ISO 4032:2012)"
NUT_CITED_KEYS = ["s_min", "e_min", "m_max", "m_min", "mw_min", "dw_min"]
ROW_KEYS = ["s_min", "e_min", "k_max", "k_min", "dw_min", "b", "lg_max", "ls_min"]
# The default part is the ISO 4017 M6 x 20 row, so it carries that row's five head values.
# M6 x 1 is an exact ISO 262 size, so the default part carries the 6g limits group (INFO-02).
LIMITS_KEYS = ["d_max", "d_min", "d2_max", "d2_min"]
PAIR_KEYS = ["clearance", "clearance_diametral", "flank_gap", "axial_play", "nut_major_diameter",
             "nut_pitch_diameter", "nut_minor_diameter", "engagement_turns"]
NUT_LIMITS_KEYS = ["D1_min", "D1_max", "D2_min", "D2_max"]
CHAMFER_KEYS = ["head_chamfer", "chamfer_depth", "chamfer_circle_diameter", "corner_edge_left"]
KEYS = ["d", "pitch", "length", "thread_length", "shank_length", "turns", "thread_depth",
        "minor_diameter", "pitch_diameter", *LIMITS_KEYS, "s", "across_corners", "k", "s_min",
        "e_min", "k_max", "k_min", "dw_min", *CHAMFER_KEYS, "volume"]


def _rows(p: BoltParams) -> dict[str, float]:
    return {r.key: r.value for r in derive(p).rows}


def test_the_default_document_lists_the_inputs_the_thread_the_head_then_the_volume() -> None:
    info = derive(BoltParams())
    assert info.kind == "bolt"
    assert [r.key for r in info.rows] == KEYS
    assert [r.unit for r in info.rows] == [
        "mm", "mm", "mm", "mm", "mm", "", *["mm"] * 15, "°", "mm", "mm", "mm", "mm³"]


def test_the_default_thread_numbers_come_from_the_pinned_profile() -> None:
    rows = _rows(BoltParams())
    assert rows["turns"] == 20.0
    # The whole-part closed form, never the kernel's Volume() (L02, INFO-03): the section area
    # times the thread plus the hexagonal prism, (sqrt(3) / 2) * s^2 * k, less the 30 degree head
    # chamfer (06.1, pinned in tests/test_end_oracles.py). The closed form less the 45 degree tip
    # cone (D-09): a threaded-to-the-head screw has no ring.
    assert rows["volume"] == bolt_end_closed_volume(
        6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 30.0)
    assert rows["volume"] == pytest.approx(
        459.14408096158724 + 200 * math.sqrt(3) - tip_cone_volume(6.0, 1.0, 45.0)
        - 1.0855309493921927, abs=1e-9)
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
    # The 10 mm plain shank is at least the cited r = 0.25 mm of an M6 under the head: a ring.
    assert rows["volume"] == bolt_end_closed_volume(
        6.0, 1.0, 30.0, 10.0, 4.0, 20.0, True, 0.25, 30.0)
    assert derive(p).warnings == [STANDING_WARNING, NO_ROW]


def test_the_rows_of_a_screw_shorter_than_the_default_thread_read_the_built_thread() -> None:
    # D-08: `?length=10` builds a 10 mm full-thread screw; the stored thread_length stays 20.
    rows = _rows(BoltParams(length=10.0))
    assert (rows["thread_length"], rows["shank_length"], rows["turns"]) == (10.0, 0.0, 10.0)
    assert rows["volume"] == bolt_end_closed_volume(
        6.0, 1.0, 10.0, 10.0, 4.0, 10.0, True, None, 30.0)


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


def test_a_chamfered_head_reports_its_angle_depth_as_cut_circle_and_edge_left() -> None:
    info = derive(BoltParams())
    by_key = {r.key: r for r in info.rows}
    depth = head_chamfer_depths(10.0, 4.0, 30.0)[1]
    assert (by_key["head_chamfer"].value, by_key["head_chamfer"].unit) == (30.0, "°")
    assert "stated model" in by_key["head_chamfer"].label
    assert (by_key["chamfer_depth"].value, by_key["chamfer_depth"].unit) == (depth, "mm")
    assert by_key["chamfer_circle_diameter"].value == 10.0
    assert by_key["corner_edge_left"].value == 4.0 - depth
    assert {by_key[k].group for k in CHAMFER_KEYS} == {"Head"}
    assert info.notes == [GRADE_A, NO_FILLET_NOTE]


def test_a_capped_head_chamfer_reports_the_depth_as_cut_not_the_model_depth() -> None:
    # 80 degrees asks for a 4.39 mm model depth; the builder cuts k / 2 = 2 mm, and a number
    # someone cuts metal to is the one that was cut (L02).
    full = head_chamfer_depths(10.0, 4.0, 80.0)[0]
    assert full > 4.0
    rows = _rows(BoltParams(head_chamfer=80.0))
    assert rows["head_chamfer"] == 80.0
    assert rows["chamfer_depth"] == 2.0
    assert rows["corner_edge_left"] == 2.0


def test_a_sharp_head_has_no_chamfer_rows_and_carries_the_sharp_head_note() -> None:
    assert SHARP_HEAD_NOTE == "sharp hex head corners: head_chamfer 0 cuts no top chamfer (L19)"
    for angle in (0.0, -0.0):
        info = derive(BoltParams(head_chamfer=angle))
        assert set(CHAMFER_KEYS).isdisjoint(r.key for r in info.rows)
        assert info.notes == [GRADE_A, NO_FILLET_NOTE, SHARP_HEAD_NOTE]
        assert SHARP_HEAD_NOTE not in info.warnings


def test_the_sharp_head_note_shows_on_a_part_that_matches_no_row() -> None:
    info = derive(BoltParams(length=21.0, head_chamfer=0.0))
    assert info.preset is not None
    assert info.preset.status == "custom"
    assert info.notes == [SHARP_HEAD_NOTE]
    # A chamfered part that matches no row carries no note.
    assert derive(BoltParams(length=21.0)).notes == []


def test_the_derived_rows_name_the_profile_and_the_hand_is_not_a_row() -> None:
    by_key = {r.key: r for r in derive(BoltParams()).rows}
    assert PROFILE in by_key["thread_depth"].label
    assert PROFILE in by_key["minor_diameter"].label
    assert PROFILE in by_key["pitch_diameter"].label  # INFO-01 adds d2 beside the minor diameter


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


def test_an_angle_the_oracle_refuses_is_an_info_document_that_says_the_part_is_not_built() -> None:
    # 06.1 WR-01, D-18, L02: 5e-324 degrees underflows the tangent, so `head_chamfer_volume`
    # raises and the build is refused before the kernel runs. The document agrees with the build:
    # no chamfer row (the "no chamfer, 4 mm edge left" reading was the wrong number), no volume
    # row, one warning that names the field and says the part is not built, and neither the band
    # warning's "built as asked" nor the "not a finite number" volume reason.
    tiny = derive(BoltParams(head_chamfer=5e-324))
    keys = {r.key for r in tiny.rows}
    assert set(CHAMFER_KEYS).isdisjoint(keys)
    assert "volume" not in keys
    assert {"s", "k", "thread_length"} <= keys  # the rest of the document is still there
    refusal = [w for w in tiny.warnings if "this part is not built" in w]
    assert len(refusal) == 1
    assert refusal[0].startswith("head_chamfer 5e-324:")
    assert not any("built as asked" in w or "not a finite number" in w for w in tiny.warnings)
    assert not any(w.startswith("volume not reported") for w in tiny.warnings)


def test_a_small_angle_the_oracle_accepts_keeps_its_chamfer_rows_and_volume() -> None:
    # The control for the refusal above: 1e-4 degrees builds (single macOS arm64 measurement in
    # tests/test_solid.py), and the oracle accepts it, so its document is whole.
    info = derive(BoltParams(head_chamfer=1e-4))
    keys = {r.key for r in info.rows}
    assert set(CHAMFER_KEYS) <= keys
    assert "volume" in keys
    assert not any("this part is not built" in w for w in info.warnings)


def test_derive_never_raises_on_a_tiny_or_near_right_head_chamfer() -> None:
    # 06.1 D-18, L02: every value reports a finite volume below the sharp head's, except where the
    # oracle refuses it (the test above).
    sharp = bolt_end_closed_volume(6.0, 1.0, 20.0, 10.0, 4.0, 20.0, True, None, 0.0)
    for angle in (1e-9, 1e-4, 89.99999999999999):
        volume = _rows(BoltParams(head_chamfer=angle))["volume"]
        assert math.isfinite(volume)
        assert 0 < volume < sharp, angle


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


def test_a_nut_document_has_its_rows_in_groups_the_closed_form_volume_and_its_m6_row() -> None:
    p = NutParams(clearance=0.1)
    info = derive(p)
    assert info.kind == "nut"
    # The cited values follow the across-corners row, inside the Nut group (D-17).
    assert [(r.key, r.group) for r in info.rows] == [
        ("d", "Thread"), ("pitch", "Thread"), ("thread_depth", "Thread"),
        ("pitch_diameter", "Thread"), ("minor_diameter", "Thread"),
        *[(key, calc.LIMITS) for key in NUT_LIMITS_KEYS],
        ("s", "Nut"), ("across_corners", "Nut"),
        *[(key, "Nut") for key in NUT_CITED_KEYS],
        ("m", "Nut"), *[(key, "Pair") for key in PAIR_KEYS], ("volume", "Part")]
    values = {r.key: r.value for r in info.rows}
    assert (values["d"], values["pitch"], values["s"], values["m"], values["clearance"]) == (
        6.0, 1.0, 10.0, 5.2, 0.1)
    assert values["across_corners"] == pytest.approx(10.0 / math.cos(math.pi / 6))
    assert values["volume"] == nut_end_closed_volume(6.0, 1.0, 10.0, 5.2, 0.1)
    assert info.warnings == [STANDING_WARNING]


def test_the_default_nut_reads_its_gost_iso_4032_m6_row() -> None:
    info = derive(NutParams(clearance=0.1))
    m6 = next(nut for nut in NUTS if nut.size == "M6")
    assert info.preset == PresetMatch(status="exact", id="iso4032:M6", display="ISO 4032 M6")
    assert info.designation == "Hexagon regular nut GOST ISO 4032 - M6"
    labels = {r.key: r.label for r in info.rows}
    values = {r.key: r.value for r in info.rows}
    assert labels["s_min"] == f"Across flats, min ({GOST} Table 1)"
    assert labels["e_min"] == f"Across corners, min ({GOST} Table 1)"
    assert labels["m_max"] == f"Height, max ({GOST} Table 1)"
    assert labels["m_min"] == f"Height, min ({GOST} Table 1)"
    assert labels["mw_min"] == f"Wrench height, min ({GOST} Table 1)"
    assert labels["dw_min"] == f"Bearing face diameter, min ({GOST} Table 1)"
    assert [values[key] for key in NUT_CITED_KEYS] == [
        m6.s_min, m6.e_min, m6.m_max, m6.m_min, m6.mw_min, m6.dw_min]
    assert {r.unit for r in info.rows if r.key in NUT_CITED_KEYS} == {"mm"}
    assert info.notes == [f"product grade A ({GOST}: D \u2264 16 mm)"]
    assert NUT_NO_ROW not in info.warnings


def test_the_nut_no_row_warning_is_pinned_to_the_text_naming_the_gost_document() -> None:
    assert NUT_NO_ROW_WARNING == NUT_NO_ROW


def test_clearance_and_hand_take_no_part_in_the_nut_match() -> None:
    base = derive(NutParams(clearance=0.1))
    wide = derive(NutParams(clearance=0.25))
    assert wide.preset == base.preset
    assert [(r.key, r.label, r.value) for r in wide.rows if r.key in NUT_CITED_KEYS] == [
        (r.key, r.label, r.value) for r in base.rows if r.key in NUT_CITED_KEYS]
    # No left-hand form in clause 5, so the designation is withheld and nothing else changes.
    left = derive(NutParams(clearance=0.1, left_hand=True))
    assert left.preset == base.preset
    assert left.designation is None
    assert left.notes == base.notes
    assert [r.key for r in left.rows] == [r.key for r in base.rows]


def test_a_nut_one_float_off_the_m6_row_is_custom_and_cites_nothing() -> None:
    # INFO-01 boundary (T-05-17): exact equality only, so one ulp off the row's m is no row.
    off = derive(NutParams(m=math.nextafter(5.2, math.inf), clearance=0.1))
    assert off.preset == PresetMatch(status="custom", id=None, display=None)
    assert not {r.key for r in off.rows} & set(NUT_CITED_KEYS)
    assert (off.designation, off.notes) == (None, [])
    assert off.warnings == [STANDING_WARNING, NUT_NO_ROW]


def test_an_m7_nut_is_custom_because_the_gost_text_prints_no_m7() -> None:
    info = derive(NutParams(d=7.0, pitch=1.0, s=11.0, m=5.5, clearance=0.1))
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert info.warnings == [STANDING_WARNING, NUT_NO_ROW]
    assert not {r.key for r in info.rows} & set(NUT_CITED_KEYS)


@pytest.mark.parametrize("nut", NUTS, ids=lambda n: n.size)
def test_every_nut_row_reads_back_as_its_own_exact_row(nut: HexNut) -> None:
    fields = expand_nut(f"iso4032:{nut.size}")
    assert fields is not None
    info = derive(NutParams.model_validate({**fields, "clearance": 0.1}))
    assert info.preset is not None
    assert info.preset.id == f"iso4032:{nut.size}"
    table = nut.source.table
    assert all(r.label.endswith(f"({GOST} {table})") for r in info.rows
               if r.key in NUT_CITED_KEYS)
    above_m16 = nut.size in {"M18", "M20"}
    limit = "D > 16 mm" if above_m16 else "D \u2264 16 mm"
    # D-20: M18's row also carries the pair-proof label, after the grade note.
    assert info.notes == [f"product grade {'B' if above_m16 else 'A'} ({GOST}: {limit})",
                          *([calc.M18_NOTE] if nut.size == "M18" else [])]


def test_the_grade_note_changes_at_m16_and_the_second_choice_rows_cite_table_2() -> None:
    def nut(size: str) -> list[str]:
        fields = expand_nut(f"iso4032:{size}")
        assert fields is not None
        return derive(NutParams.model_validate({**fields, "clearance": 0.1})).notes

    assert nut("M16") == [f"product grade A ({GOST}: D \u2264 16 mm)"]
    assert nut("M18") == [f"product grade B ({GOST}: D > 16 mm)", calc.M18_NOTE]
    fields = expand_nut("iso4032:M3.5")
    assert fields is not None
    labels = [r.label for r in derive(NutParams.model_validate({**fields, "clearance": 0.1})).rows
              if r.key in NUT_CITED_KEYS]
    assert len(labels) == 6
    assert all(label.endswith("Table 2)") for label in labels)


@pytest.mark.parametrize(("clearance", "text"), [
    (0.0, "clearance 0 is not positive: the pair cannot be proven (PAIR-03)"),
    (-0.05, "clearance -0.05 is not positive: the pair cannot be proven (PAIR-03)"),
])
def test_a_nut_with_a_non_positive_clearance_warns_once_after_the_standing_warning(
        clearance: float, text: str) -> None:
    info = derive(NutParams(clearance=clearance))
    assert info.warnings == [STANDING_WARNING, text]


@pytest.mark.parametrize("clearance", [5e-324, 0.1])
def test_a_nut_with_a_positive_clearance_has_no_clearance_warning(clearance: float) -> None:
    # 5e-324 is the smallest positive float: still positive, so no warning (PAIR-01, adjacency).
    info = derive(NutParams(clearance=clearance))
    assert info.warnings == [STANDING_WARNING]


def test_a_tall_nut_fine_stl_is_refused_by_the_nuts_cap_and_nothing_else_is() -> None:
    # R16, R17: the M10 x 1.5 nut's cap is 36 mm (not the rod's 56): a nut one mm above it is
    # refused on its fine STL, with the sentence the info document and the warnings carry.
    tall = NutParams(d=10.0, pitch=1.5, s=16.0, m=37.0, clearance=0.1)
    sentence = nut_fine_stl_refusal(10.0, 1.5, 37.0, 0.1, False)
    assert sentence is not None
    assert sentence.startswith("m: ")
    assert download_refusal(tall, "stl", "fine") == sentence
    for fmt, quality in (("stl", "preview"), ("step", "fine"), ("step", "preview")):
        assert download_refusal(tall, fmt, quality) is None
    info = derive(tall)
    refusals = {(e.format, e.quality): e.refusal for e in info.downloads}
    assert refusals == {("stl", "fine"): sentence, ("stl", "preview"): None,
                        ("step", "fine"): None, ("step", "preview"): None}
    assert info.warnings.count(sentence) == 1
    at_cap = NutParams(d=10.0, pitch=1.5, s=16.0, m=36.0, clearance=0.1)
    assert download_refusal(at_cap, "stl", "fine") is None
    assert sentence not in derive(at_cap).warnings
    # a clearance above the ceiling is refused on the fine STL too, naming the clearance
    loose = NutParams(d=10.0, pitch=1.5, s=26.0, m=5.0, clearance=5.5)
    loose_refusal = download_refusal(loose, "stl", "fine")
    assert loose_refusal is not None
    assert loose_refusal.startswith("clearance: ")


@pytest.mark.parametrize("left_hand", [False, True])
def test_nut_fine_stl_serves_every_catalogue_row_at_its_own_s_and_m_max(left_hand: bool) -> None:
    """No cap lands below a GOST ISO 4032-2014 catalogue height (plan 05-19, stop condition)."""
    diameters = {size.label: size.d for size in iso262.SIZES}
    for row in NUTS:
        nut = NutParams(d=diameters[row.size], pitch=row.pitch, s=row.s, m=row.m_max,
                        clearance=0.1, left_hand=left_hand)
        assert download_refusal(nut, "stl", "fine") is None, row.size


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
        # M8 at pitch 1.25 is a size; pitch 1.0 is not, so the second also warns on the nut side.
        assert derive(p).warnings[:2] == [STANDING_WARNING, NO_ROW]
        assert derive(p).warnings[2:] == ([] if p.pitch == 1.25 else [
            "no GOST ISO 4032-2014 (ISO 4032:2012) row for d 8 pitch 1; set s and m on the nut"])


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
             "minor_diameter", "pitch_diameter"]
    head = ["s", "across_corners", "k", "s_min", "e_min", "k_max", "k_min", "dw_min",
            *CHAMFER_KEYS]
    assert _groups(info) == ([("Shank and thread", k) for k in shank]
                             + [(calc.LIMITS, k) for k in LIMITS_KEYS]
                             + [("Head", k) for k in head] + [("Part", "volume")])


def test_an_iso_4014_match_adds_b_lg_max_and_ls_min_to_the_shank_group() -> None:
    info = derive(M10X80)
    shank = [k for g, k in _groups(info) if g == "Shank and thread"]
    assert shank == ["d", "pitch", "length", "thread_length", "shank_length", "turns",
                     "thread_depth", "minor_diameter", "pitch_diameter", "b", "lg_max", "ls_min"]
    assert [k for g, k in _groups(info) if g == "Head"] == [
        "s", "across_corners", "k", "s_min", "e_min", "k_max", "k_min", "dw_min", *CHAMFER_KEYS]


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
    # The third is the counterpart's off-row warning: pitch 0.75 is no ISO 262 coarse size.
    assert info.warnings == [
        STANDING_WARNING, NO_ROW,
        "no GOST ISO 4032-2014 (ISO 4032:2012) row for d 6 pitch 0.75; set s and m on the nut"]
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert info.designation is None
    assert {r.group for r in info.rows} == {"Shank and thread", "Head", "Part"}


def test_an_edited_field_drops_every_row_value_never_the_nearest_row() -> None:
    for change in ({"length": 21.0}, {"s": 10.5}, {"k": 4.1}, {"d": 6.5}, {"thread_length": 19.0}):
        info = derive(BoltParams.model_validate(change))
        assert {r.key for r in info.rows}.isdisjoint(ROW_KEYS), change
        assert NO_ROW in info.warnings, change


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


def test_an_off_band_head_chamfer_builds_as_asked_and_warns_naming_the_band() -> None:
    # D-02: the band text is plain strings; the texts themselves are pinned in test_thread_maths.
    for angle in (14.999, 30.001, 45.0):
        band = head_chamfer_warnings(10.0, 4.0, angle)
        assert len(band) == 1
        warnings = derive(BoltParams(head_chamfer=angle)).warnings
        assert warnings.count(band[0]) == 1, angle
        assert "head_chamfer" in band[0]
        assert "15 to 30 degree band" in band[0]
        assert _rows(BoltParams(head_chamfer=angle))["head_chamfer"] == angle
    for angle in (0.0, 15.0, 30.0):
        assert not any("degree band" in w for w in derive(BoltParams(head_chamfer=angle)).warnings)


def test_a_defaulted_head_chamfer_deeper_than_half_k_is_cut_at_half_k_and_warned() -> None:
    # D-04: s = 100 with the default 30 degrees asks for a model depth far over k / 2 = 2 mm.
    info = derive(BoltParams(s=100.0))
    cap = head_chamfer_warnings(100.0, 4.0, 30.0)
    assert len(cap) == 1
    assert cap[0].startswith("head_chamfer 30 and k 4:")
    assert info.warnings == [STANDING_WARNING, cap[0], NO_ROW]
    assert _rows(BoltParams(s=100.0))["chamfer_depth"] == 2.0


def test_a_direct_head_chamfer_of_80_is_capped_and_warned_not_refused() -> None:
    # D-06: direct construction never refuses; the 422 is the request boundary's (plan 04).
    info = derive(BoltParams(head_chamfer=80.0))
    assert info.warnings == [STANDING_WARNING, *head_chamfer_warnings(10.0, 4.0, 80.0)]
    assert len(info.warnings) == 3
    assert "head_chamfer 80" in info.warnings[1]
    assert "head_chamfer 80 and k 4" in info.warnings[2]
    assert _rows(BoltParams(head_chamfer=80.0))["chamfer_depth"] == 2.0


def test_the_head_chamfer_warnings_follow_the_thread_warnings_and_precede_the_no_row_warning(
) -> None:
    p = BoltParams(d=8.0, pitch=1.25, length=70.0, thread_length=80.0, head_chamfer=80.0)
    s, k = p.s, p.k
    info = derive(p)
    refusal = fine_stl_refusal(8.0, 1.25, 70.0, False)
    assert info.warnings == [
        STANDING_WARNING,
        "thread_length 80 exceeds length 70: thread built to the full length",
        *head_chamfer_warnings(s, k, 80.0), NO_ROW, refusal]


# --- the notes: product grade and the ISO versus withdrawn DIN wrench size (D-20, INFO-05) -----

GRADE_A = "product grade A (ISO 4017:2022: l ≤ 150 mm and l ≤ 10 d)"


def _row_part(row_id: str) -> BoltParams:
    row = next(r for r in catalogue() if r.id == row_id)
    return BoltParams.model_validate(dict(row.fields))


def _without_fillet_note(notes: list[str]) -> list[str]:
    return [n for n in notes if n != NO_FILLET_NOTE]


def test_the_default_part_notes_its_product_grade_and_that_it_has_no_fillet() -> None:
    assert derive(BoltParams()).notes == [GRADE_A, NO_FILLET_NOTE]


def test_a_grade_b_row_notes_grade_b() -> None:
    notes = derive(_row_part("iso4017:M16x160")).notes
    assert notes == ["product grade B (ISO 4017:2022: l > 150 mm)", NO_FILLET_NOTE]


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
    notes = _without_fillet_note(derive(_row_part(row_id)).notes)
    assert len(notes) == 2
    assert notes[1] == note


def test_the_wrench_note_appears_on_those_three_sizes_and_no_others() -> None:
    # INFO-05: only M10, M12 and M14 differ between the ISO and the withdrawn DIN wrench size.
    sizes_with_note = {row.size for row in catalogue()
                       if len(_without_fillet_note(
                           derive(BoltParams.model_validate(dict(row.fields))).notes)) == 2}
    assert sizes_with_note == {"M10", "M12", "M14"}
    for row_id in ("iso4017:M8x40", "iso4017:M16x40", "iso4017:M20x40", "iso4014:M8x80"):
        assert len(_without_fillet_note(derive(_row_part(row_id)).notes)) == 1, row_id


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


def test_the_bolt_rule_refuses_an_explicit_head_chamfer_deeper_than_half_k_reading_defaults(
) -> None:
    # D-04, D-05: s 10 and k 4 come from the model's defaults when the request does not name them.
    msg = head_chamfer_conflict(10.0, 4.0, 80.0)
    assert msg is not None
    conflict = explicit_conflict("bolt", {"head_chamfer": 80.0})
    assert conflict == ExplicitConflict("head_chamfer_conflict", ("head_chamfer", "k"), msg)
    wide = explicit_conflict("bolt", {"head_chamfer": 30.0, "s": 100.0})
    assert wide is not None
    assert wide.msg == head_chamfer_conflict(100.0, 4.0, 30.0)
    assert explicit_conflict("bolt", {"head_chamfer": 80.0, "k": 10.0}) is None
    assert explicit_conflict("bolt", {"head_chamfer": 30.0}) is None


def test_a_defaulted_head_chamfer_is_never_a_conflict() -> None:
    assert explicit_conflict("bolt", {"s": 100.0}) is None
    assert explicit_conflict("bolt", {}) is None


def test_the_thread_length_rule_is_judged_before_the_head_chamfer_rule() -> None:
    conflict = explicit_conflict(
        "bolt", {"length": 10.0, "thread_length": 30.0, "head_chamfer": 80.0})
    assert conflict is not None
    assert conflict.type == "thread_length_conflict"


@pytest.mark.parametrize("angle", ["80", math.nan, math.inf, 90.0, -1.0, 0.0])
def test_a_head_chamfer_that_is_not_a_usable_float_is_the_models_to_refuse(
        angle: object) -> None:
    assert explicit_conflict("bolt", {"head_chamfer": angle, "s": 100.0}) is None


# --- the nominal diameters and the bought-part limits (INFO-01, INFO-02, D-16, L14) ------------

LIMITS_HEADING = "limits for a bought part; this model is nominal and not toleranced"
LIMITS_LABEL_SOURCE = ("(derived: GOST 24705-2004 (ISO 724:1993, MOD) + "
                       "GOST 16093-2004 (based on ISO 965-1:1998 and ISO 965-3:1998))")
JUST_ABOVE_M6 = math.nextafter(6.0, math.inf)


def _limit_rows(info: PartInfo) -> list[tuple[str, str, float, str]]:
    return [(r.key, r.label, r.value, r.unit) for r in info.rows if r.group == LIMITS_HEADING]


def test_the_limits_heading_is_the_ascii_text_of_info_02() -> None:
    assert calc.LIMITS == LIMITS_HEADING
    assert LIMITS_HEADING.encode("ascii") == (
        b"limits for a bought part; this model is nominal and not toleranced")


def test_the_pitch_diameter_follows_the_minor_diameter_on_the_bolt() -> None:
    info = derive(BoltParams())
    keys = [r.key for r in info.rows]
    assert keys[keys.index("minor_diameter") + 1] == "pitch_diameter"
    row = next(r for r in info.rows if r.key == "pitch_diameter")
    assert row.label == f"Pitch diameter d2 ({PROFILE})"
    assert (row.value, row.unit, row.group) == (pitch_diameter(6.0, 1.0), "mm", "Shank and thread")


def test_the_nut_thread_group_reads_d_pitch_depth_pitch_diameter_and_minor_diameter() -> None:
    info = derive(NutParams(clearance=0.1))
    thread = [r for r in info.rows if r.group == "Thread"]
    assert [r.key for r in thread] == ["d", "pitch", "thread_depth", "pitch_diameter",
                                       "minor_diameter"]
    by_key = {r.key: r for r in thread}
    assert by_key["pitch_diameter"].label == f"Pitch diameter D2 ({PROFILE})"
    assert by_key["minor_diameter"].label == f"Minor diameter D1 ({PROFILE})"
    assert by_key["pitch_diameter"].value == pitch_diameter(6.0, 1.0)
    assert by_key["minor_diameter"].value == basic_minor_diameter(6.0, 1.0)
    assert by_key["thread_depth"].value == thread_depth(1.0)


def test_the_m6_bolt_carries_its_four_6g_rows_with_the_derived_label() -> None:
    limits = next(b for b in BOLT_LIMITS if b.size == "M6")
    assert _limit_rows(derive(BoltParams())) == [
        ("d_max", f"Major diameter, max, 6g {LIMITS_LABEL_SOURCE}", limits.d_max, "mm"),
        ("d_min", f"Major diameter, min, 6g {LIMITS_LABEL_SOURCE}", limits.d_min, "mm"),
        ("d2_max", f"Pitch diameter, max, 6g {LIMITS_LABEL_SOURCE}", limits.d2_max, "mm"),
        ("d2_min", f"Pitch diameter, min, 6g {LIMITS_LABEL_SOURCE}", limits.d2_min, "mm")]


def test_the_m6_nut_carries_its_four_6h_rows_with_the_derived_label() -> None:
    limits = next(n for n in NUT_LIMITS if n.size == "M6")
    assert _limit_rows(derive(NutParams(clearance=0.1))) == [
        ("D1_min", f"Minor diameter, min, 6H {LIMITS_LABEL_SOURCE}", limits.D1_min, "mm"),
        ("D1_max", f"Minor diameter, max, 6H {LIMITS_LABEL_SOURCE}", limits.D1_max, "mm"),
        ("D2_min", f"Pitch diameter, min, 6H {LIMITS_LABEL_SOURCE}", limits.D2_min, "mm"),
        ("D2_max", f"Pitch diameter, max, 6H {LIMITS_LABEL_SOURCE}", limits.D2_max, "mm")]


def test_every_iso_262_size_shows_its_own_stored_limits_on_both_kinds() -> None:
    for size in iso262.SIZES:
        bolt = {k: v for k, _, v, _ in _limit_rows(
            derive(BoltParams.model_construct(d=size.d, pitch=size.pitch)))}
        nut = {k: v for k, _, v, _ in _limit_rows(derive(NutParams(
            d=size.d, pitch=size.pitch, s=size.d + 5.0, m=size.d, clearance=0.1)))}
        stored_bolt = next(b for b in BOLT_LIMITS if b.size == size.label)
        stored_nut = next(n for n in NUT_LIMITS if n.size == size.label)
        assert bolt == {"d_max": stored_bolt.d_max, "d_min": stored_bolt.d_min,
                        "d2_max": stored_bolt.d2_max, "d2_min": stored_bolt.d2_min}, size.label
        assert nut == {"D1_min": stored_nut.D1_min, "D1_max": stored_nut.D1_max,
                       "D2_min": stored_nut.D2_min, "D2_max": stored_nut.D2_max}, size.label


def test_the_limits_do_not_depend_on_the_hand_the_clearance_or_the_catalogue_row() -> None:
    base = _limit_rows(derive(NutParams(clearance=0.1)))
    assert base
    for clearance in (0.0, 0.05, 0.1, 0.25, -0.05):
        for hand in (False, True):
            nut = derive(NutParams(clearance=clearance, left_hand=hand))
            assert _limit_rows(nut) == base, (clearance, hand)
    bolt = _limit_rows(derive(BoltParams()))
    assert _limit_rows(derive(BoltParams(left_hand=True))) == bolt
    # A size that is no catalogue row still has the limits: they depend on (d, pitch) alone.
    assert _limit_rows(derive(BoltParams(length=21.0, thread_length=21.0))) == bolt
    assert _limit_rows(derive(NutParams(s=11.0, clearance=0.1))) == base


@pytest.mark.parametrize("fields", [
    {"d": JUST_ABOVE_M6}, {"d": 6.0001}, {"pitch": 0.9}, {"pitch": math.nextafter(1.0, math.inf)},
])
def test_off_an_exact_iso_262_size_there_is_no_limits_group_and_the_no_row_warning(
        fields: dict[str, float]) -> None:
    bolt = derive(BoltParams.model_validate(fields))
    nut = derive(NutParams.model_validate({**fields, "clearance": 0.1}))
    for info, no_row in ((bolt, NO_ROW), (nut, NUT_NO_ROW)):
        # INFO-02: no group, no empty heading, and the row list holds no row of that group.
        assert _limit_rows(info) == []
        assert LIMITS_HEADING not in {r.group for r in info.rows}
        assert no_row in info.warnings


def test_at_the_exact_m6_size_the_limits_are_present_on_both_hands_and_every_clearance() -> None:
    for hand in (False, True):
        assert len(_limit_rows(derive(BoltParams(left_hand=hand)))) == 4
        for clearance in (-0.05, 0.0, 0.05, 0.1, 0.5):
            assert len(_limit_rows(derive(NutParams(left_hand=hand, clearance=clearance)))) == 4


def test_the_limit_labels_name_both_gost_texts_and_never_an_unread_edition() -> None:
    for info in (derive(BoltParams()), derive(NutParams(clearance=0.1))):
        for row in info.rows:
            if row.group != LIMITS_HEADING:
                continue
            assert "GOST 24705-2004 (ISO 724:1993, MOD)" in row.label
            assert "GOST 16093-2004 (based on ISO 965-1:1998 and ISO 965-3:1998)" in row.label
            assert "ISO 724:2023" not in row.label
            assert "965-2" not in row.label


# --- the nut's Pair group (PAIR-01, D-19, PAIR-04) ----------------------------------------------

def _pair(p: NutParams) -> dict[str, float]:
    return {r.key: r.value for r in derive(p).rows if r.group == "Pair"}


def test_the_nut_pair_rows_are_the_eight_keys_in_the_fixed_order() -> None:
    info = derive(NutParams(clearance=0.1))
    assert [r.key for r in info.rows if r.group == "Pair"] == PAIR_KEYS
    assert [r.label for r in info.rows if r.group == "Pair"] == [
        "Clearance (radial)", "Clearance (diametral, 2c)", "Flank-normal gap (closed form)",
        "Axial play, both flanks (closed form)", "Nut major diameter (d + 2c)",
        "Nut pitch diameter (D2 + 2c)", "Nut minor diameter (D1 + 2c)", "Engagement (m / P)"]
    assert [r.unit for r in info.rows if r.group == "Pair"] == ["mm"] * 7 + ["turns"]
    # The Pair group is contiguous and the bolt has none (D-19).
    keys = [r.key for r in info.rows]
    assert keys[keys.index("clearance"):][:8] == PAIR_KEYS
    assert "Pair" not in {r.group for r in derive(BoltParams()).rows}


def test_the_nut_pair_values_are_the_unrounded_closed_forms() -> None:
    c = 0.1
    pair = _pair(NutParams(clearance=c))
    assert pair["clearance"] == c
    assert pair["clearance_diametral"] == 2 * c
    assert pair["flank_gap"] == flank_normal_gap(c)
    assert pair["axial_play"] == axial_play(c)
    assert pair["nut_major_diameter"] == 6.0 + 2 * c
    assert pair["nut_pitch_diameter"] == pitch_diameter(6.0, 1.0) + 2 * c
    assert pair["nut_minor_diameter"] == basic_minor_diameter(6.0, 1.0) + 2 * c
    assert pair["engagement_turns"] == 5.2 / 1.0
    assert pair["flank_gap"] == pytest.approx(0.5 * c, abs=1e-15)
    assert pair["axial_play"] == pytest.approx(2 * c / math.sqrt(3), abs=1e-15)


def test_the_engagement_is_the_exact_quotient_of_the_height_and_the_pitch() -> None:
    # 5.4 / 0.6 is 9.000000000000002 in floats; the panel prints the exact quotient, like turns.
    assert _pair(NutParams(d=3.5, pitch=0.6, s=6.0, m=5.4, clearance=0.1))[
        "engagement_turns"] == 9.0


def test_zero_clearance_gives_zero_gaps_and_the_warning_and_interference_is_reported() -> None:
    zero = derive(NutParams(clearance=0.0))
    pair = {r.key: r.value for r in zero.rows if r.group == "Pair"}
    assert (pair["clearance_diametral"], pair["flank_gap"], pair["axial_play"]) == (0.0, 0.0, 0.0)
    assert any("is not positive" in w for w in zero.warnings)
    tight = derive(NutParams(clearance=-0.05))
    pair = {r.key: r.value for r in tight.rows if r.group == "Pair"}
    assert pair["clearance_diametral"] == -0.1
    assert pair["flank_gap"] < 0
    assert pair["axial_play"] < 0
    assert pair["nut_major_diameter"] == 6.0 - 0.1
    assert any("is not positive" in w for w in tight.warnings)


def test_the_pair_rows_do_not_depend_on_the_hand() -> None:
    assert _pair(NutParams(clearance=0.1, left_hand=True)) == _pair(NutParams(clearance=0.1))


def test_a_pair_value_that_is_not_finite_is_left_out_with_a_warning() -> None:
    # model_construct skips the bounds (D-15): the quotient overflows and is dropped, not printed.
    info = derive(NutParams.model_construct(d=6.0, pitch=5e-324, s=10.0, m=5.2, clearance=0.1,
                                            left_hand=False))
    assert "engagement_turns" not in [r.key for r in info.rows]
    assert any(w.startswith("engagement_turns not reported") for w in info.warnings)


# --- the M18 label (D-20, SC6): from the cited record, keyed on the size alone -----------------

M18_TEXT = "kernel pair proof inconclusive at K = 3 (2026-10-08-a-pair)"


def test_the_m18_note_text_and_key_are_the_campaigns() -> None:
    assert calc.M18_NOTE == M18_TEXT
    assert calc.M18_KEY == (18.0, 2.5)


@pytest.mark.parametrize("clearance", [0.05, 0.1, -0.05])
@pytest.mark.parametrize("hand", [False, True])
def test_an_m18_nut_carries_the_note_exactly_once_whatever_the_hand_and_clearance(
        clearance: float, hand: bool) -> None:
    nut = NutParams(d=18.0, pitch=2.5, s=27.0, m=14.8, clearance=clearance, left_hand=hand)
    notes = derive(nut).notes
    assert notes.count(M18_TEXT) == 1
    assert notes[-1] == M18_TEXT


def test_the_m18_row_keeps_its_grade_note_before_the_label() -> None:
    row = expand_nut("iso4032:M18")
    assert row is not None
    info = derive(NutParams.model_validate({**row, "clearance": 0.1}))
    assert info.preset == PresetMatch(status="exact", id="iso4032:M18", display="ISO 4032 (M18)")
    assert info.notes == [f"product grade B ({GOST}: D > 16 mm)", M18_TEXT]


def test_a_nut_that_is_no_row_still_carries_the_m18_note() -> None:
    info = derive(NutParams(d=18.0, pitch=2.5, s=30.0, m=10.0, clearance=0.1))
    assert info.preset == PresetMatch(status="custom", id=None, display=None)
    assert info.notes == [M18_TEXT]


def test_only_the_exact_m18_key_carries_the_note() -> None:
    above = math.nextafter(18.0, math.inf)
    for nut in (NutParams(d=above, pitch=2.5, s=27.0, m=14.8, clearance=0.1),
                NutParams(d=18.0, pitch=2.0, s=27.0, m=14.8, clearance=0.1),
                NutParams(d=18.0, pitch=math.nextafter(2.5, math.inf), s=27.0, m=14.8,
                          clearance=0.1),
                NutParams(clearance=0.1)):
        assert M18_TEXT not in derive(nut).notes
    # The bolt gets no note (SC6: the label is on the nut's pair section).
    assert M18_TEXT not in derive(BoltParams(d=18.0, pitch=2.5, s=27.0, k=11.0)).notes


def test_the_m18_note_is_derived_without_the_kernel_loaded() -> None:
    code = ("import sys; from screw.calc import derive; from screw.params import NutParams; "
            "i = derive(NutParams(d=18.0, pitch=2.5, s=27.0, m=14.8, clearance=0.1)); "
            f"print({M18_TEXT!r} in i.notes, 'cadquery' in sys.modules)")
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True,
                         check=True).stdout
    assert out.split() == ["True", "False"]


# ------------------------------------------------------- the counterpart (TYPE-04, D-02, D-03)

NO_NUT_ROW = "no GOST ISO 4032-2014 (ISO 4032:2012) row for d {d}; set s and m on the nut"
NO_BOLT_ROW = "no ISO 4017:2022 row for d {d}; set s, k, length and thread_length on the bolt"
CARRIED = {"d": 6.0, "pitch": 1.0, "left_hand": False}


def _counterpart(p: FastenerParams) -> Counterpart:
    counterpart = derive(p).counterpart
    assert counterpart is not None
    return counterpart


def test_the_default_bolt_names_its_nut_with_the_iso_4032_m6_row_and_no_warning() -> None:
    nut = next(n for n in NUTS if n.size == "M6")
    info = derive(BoltParams())
    assert _counterpart(BoltParams()) == Counterpart(
        kind="nut", fields={**CARRIED, "s": nut.s, "m": nut.m_max})
    assert list(_counterpart(BoltParams()).fields) == ["d", "pitch", "left_hand", "s", "m"]
    assert not any(w.startswith("no GOST ISO 4032-2014 (ISO 4032:2012) row for") for w in
                   info.warnings)


def test_the_default_nut_names_its_bolt_with_the_iso_4017_m6_head_and_no_warning() -> None:
    head = BoltParams()
    nut = NutParams(clearance=0.1)
    assert _counterpart(nut) == Counterpart(
        kind="bolt", fields={**CARRIED, "s": head.s, "k": head.k})
    assert not any(w.startswith("no ISO 4017:2022 row for") for w in derive(nut).warnings)


@pytest.mark.parametrize("p", [BoltParams(left_hand=True),
                               NutParams(left_hand=True, clearance=0.1)])
def test_left_hand_carries_over_as_a_json_boolean_in_both_directions(p: FastenerParams) -> None:
    counterpart = _counterpart(p)
    assert counterpart.fields["left_hand"] is True
    assert '"left_hand":true' in counterpart.model_dump_json()


def test_a_bolt_off_the_nut_rows_carries_d_pitch_and_hand_and_warns_naming_the_row_source() -> None:
    info = derive(BoltParams(d=6.5))
    assert _counterpart(BoltParams(d=6.5)) == Counterpart(
        kind="nut", fields={**CARRIED, "d": 6.5})
    assert info.warnings[-1] == NO_NUT_ROW.format(d="6.5 pitch 1")


def test_an_iso_4017_m7_bolt_is_off_the_nut_rows_because_gost_iso_4032_prints_no_m7() -> None:
    head = next(h for h in HEADS if h.size == "M7")
    m7 = BoltParams(d=7.0, pitch=1.0, s=head.s, k=head.k)
    assert _counterpart(m7) == Counterpart(kind="nut", fields={**CARRIED, "d": 7.0})
    assert derive(m7).warnings[-1] == NO_NUT_ROW.format(d="7 pitch 1")


def test_a_nut_off_the_iso_4017_rows_carries_d_pitch_and_hand_and_warns() -> None:
    nut = NutParams(d=6.5, clearance=0.1)
    assert _counterpart(nut) == Counterpart(kind="bolt", fields={**CARRIED, "d": 6.5})
    assert derive(nut).warnings[-1] == NO_BOLT_ROW.format(d="6.5 pitch 1")


def test_a_value_one_float_off_a_row_gets_no_nearest_row() -> None:
    for p in (BoltParams(d=math.nextafter(6.0, 7.0)), BoltParams(pitch=math.nextafter(1.0, 2.0)),
              NutParams(d=math.nextafter(6.0, 7.0), clearance=0.1)):
        assert set(_counterpart(p).fields) == {"d", "pitch", "left_hand"}


@pytest.mark.parametrize("p", [
    BoltParams(), BoltParams(d=6.5), BoltParams(length=30.0, thread_length=18.0),
    NutParams(clearance=0.1), NutParams(d=6.5, clearance=0.1)])
def test_clearance_length_and_thread_length_are_never_in_a_counterpart(p: FastenerParams) -> None:
    assert {"clearance", "length", "thread_length"}.isdisjoint(_counterpart(p).fields)


@pytest.mark.parametrize("nut", NUTS, ids=lambda n: n.size)
def test_following_a_bolts_counterpart_gives_the_nut_row_of_its_size(nut: HexNut) -> None:
    size = next(s for s in iso262.SIZES if s.label == nut.size)
    head = next(h for h in HEADS if h.size == nut.size)
    bolt = BoltParams(d=size.d, pitch=size.pitch, s=head.s, k=head.k, length=40.0,
                      thread_length=40.0)
    follow = NutParams.model_validate({**_counterpart(bolt).fields, "clearance": 0.1})
    assert (follow.d, follow.pitch, follow.s, follow.m) == (size.d, size.pitch, nut.s, nut.m_max)
    assert follow.clearance == 0.1
    preset = derive(follow).preset
    assert preset is not None
    assert (preset.status, preset.id) == ("exact", f"iso4032:{nut.size}")


def test_following_a_nuts_counterpart_gives_a_bolt_with_the_nuts_d_pitch_and_hand() -> None:
    nut = NutParams(left_hand=True, clearance=0.1)
    bolt = BoltParams.model_validate(_counterpart(nut).fields)
    assert (bolt.d, bolt.pitch, bolt.left_hand) == (nut.d, nut.pitch, nut.left_hand)


# --- the bolt's ends: the tip cone, the fillet ring, their notes and warnings (D-09, D-11, 05-12)


def test_the_volume_row_is_the_closed_form_less_the_tip_and_plus_the_ring() -> None:
    # An ISO 4014 M10 x 80 row: 26 mm of thread under a 54 mm plain shank, r = 0.4 (cited).
    rows = _rows(M10X80)
    assert rows["volume"] == bolt_end_closed_volume(
        10.0, 1.5, 80.0, 16.0, 6.4, 26.0, True, 0.4, 30.0)
    assert rows["volume"] != bolt_end_closed_volume(
        10.0, 1.5, 80.0, 16.0, 6.4, 26.0, True, None, 30.0)


def test_the_volume_formula_text_names_the_tip_cone_the_ring_and_the_head_chamfer() -> None:
    # The formula is spoken only when the row cannot be reported (L02); d = 1e200 overflows it.
    info = derive(BoltParams.model_construct(d=1e200, pitch=1.0, length=20.0, s=10.0, k=4.0))
    text = next(w for w in info.warnings if w.startswith("volume not reported"))
    assert "tip cone" in text
    assert "fillet ring" in text
    assert "head chamfer" in text


def test_a_thread_no_longer_than_the_tip_cone_gets_no_cone_and_a_warning_naming_thread() -> None:
    cone = tip_cone_length(1.0, TIP_ANGLE_DEG)
    assert cone == pytest.approx(thread_depth(1.0))  # tan 45 degrees is 1
    for t, cut in ((cone, False), (math.nextafter(cone, math.inf), True)):
        p = BoltParams(d=6.0, pitch=1.0, length=10.0, thread_length=t)
        info = derive(p)
        warned = [w for w in info.warnings if w.startswith("thread_length: the built thread")]
        assert bool(warned) is not cut, t
        values = {r.key: r.value for r in info.rows}
        assert values["volume"] == bolt_end_closed_volume(
            6.0, 1.0, 10.0, 10.0, 4.0, t, cut, 0.25, 30.0)
    short = derive(BoltParams(d=6.0, pitch=1.0, length=10.0, thread_length=cone)).warnings
    assert any("thread_length" in w and "no tip cone is cut" in w for w in short)


def test_an_iso_4017_screw_notes_that_it_has_no_fillet_and_an_iso_4014_bolt_does_not() -> None:
    assert NO_FILLET_NOTE == "no under-head fillet: the thread runs to the head (ISO 4017:2022)"
    assert NO_FILLET_NOTE in derive(BoltParams()).notes
    assert NO_FILLET_NOTE not in derive(M10X80).notes
    # A note, not a warning.
    assert all(NO_FILLET_NOTE not in w for w in derive(BoltParams()).warnings)


# --- the nut's ends: the end-aware closed form and its warnings (05-13) ------------------------


def test_the_nut_end_closed_form_is_the_nut_less_two_countersinks_and_two_chamfers() -> None:
    # Written out from the owner's models (R3 1.16 and 90 degrees included, R4 30 degrees from the
    # inscribed circle), not from the constants, so a changed model cannot change both sides.
    from screw.calc.thread import countersink_volume, face_chamfer_volume

    face = 1.16 * 6.0 / 2
    root = 3.0 - thread_depth(1.0) + 0.1
    csk = countersink_volume(6.0, 1.0, 0.1, 10.0, face, 45.0, face - root)
    chamfer = face_chamfer_volume(10.0, 5.0, 30.0, (5.0 / math.cos(math.pi / 6) - 5.0)
                                  * math.tan(math.radians(30.0)))
    assert csk > 1.0
    assert chamfer > 1.0
    assert nut_end_closed_volume(6.0, 1.0, 10.0, 5.2, 0.1) == pytest.approx(
        nut_closed_volume(6.0, 1.0, 10.0, 5.2, 0.1) - 2 * csk - 2 * chamfer, rel=1e-12)


def test_a_countersink_that_cannot_cross_the_void_is_left_out_of_the_volume_and_warned() -> None:
    # R3: M2 at clearance 0.2 has a crest radius of 1.2 mm and the cone opens to 1.16 mm.
    from screw.calc.thread import face_chamfer_volume

    chamfer = face_chamfer_volume(4.0, 2.0, 30.0, (2.0 / math.cos(math.pi / 6) - 2.0)
                                  * math.tan(math.radians(30.0)))
    assert nut_end_closed_volume(2.0, 0.4, 4.0, 1.6, 0.2) == pytest.approx(
        nut_closed_volume(2.0, 0.4, 4.0, 1.6, 0.2) - 2 * chamfer, rel=1e-12)
    info = derive(NutParams(d=2.0, pitch=0.4, s=4.0, m=1.6, clearance=0.2))
    assert info.warnings[0] == WARNING
    [named] = [w for w in info.warnings if w.startswith("clearance 0.2:")]
    assert "left out" in named


def test_a_nut_too_thin_for_its_countersinks_is_capped_and_warned_naming_m() -> None:
    # R5 a: m 0.8 on M6 caps both depths at m / 2, and the volume integrates the capped depth.
    from screw.calc.thread import countersink_volume, face_chamfer_volume

    info = derive(NutParams(clearance=0.1, m=0.8))
    named = [w for w in info.warnings if w.startswith("m 0.8:")]
    assert len(named) == 2
    assert "countersinks are cut 0.4 mm deep" in named[0]
    assert "chamfers are cut 0.4 mm deep" in named[1]
    expected = (nut_closed_volume(6.0, 1.0, 10.0, 0.8, 0.1)
                - 2 * countersink_volume(6.0, 1.0, 0.1, 10.0, 3.48, 45.0, 0.4)
                - 2 * face_chamfer_volume(10.0, 5.0, 30.0, 0.4))
    assert nut_end_closed_volume(6.0, 1.0, 10.0, 0.8, 0.1) == pytest.approx(expected, rel=1e-12)


def test_a_nut_with_room_for_its_ends_carries_no_end_warning_and_its_formula_names_them() -> None:
    info = derive(NutParams(clearance=0.1))
    assert info.warnings[0] == WARNING
    assert not any("(L15)" in w for w in info.warnings)
    assert info.model_dump()["rows"]  # the document is whole
    broken = derive(NutParams.model_construct(d=math.inf, pitch=1.0, s=10.0, m=5.2, clearance=0.1))
    text = next(w for w in broken.warnings if w.startswith("volume not reported"))
    assert "lead-in countersinks" in text
    assert "face chamfers" in text


MEASURED_RANGE = ("d {d} mm is outside M6 to M12, the sizes the clearance default was measured on "
                  "(L17, run 06-print-run-1)")


def _measured_range_warnings(p: FastenerParams) -> list[str]:
    return [w for w in derive(p).warnings if "the sizes the clearance default was measured on" in w]


@pytest.mark.parametrize(("d", "pitch", "s"), [(5.0, 0.8, 8.0), (14.0, 2.0, 22.0)])
def test_a_nut_outside_the_measured_range_warns_with_or_without_a_typed_clearance(
        d: float, pitch: float, s: float) -> None:
    omitted = NutParams(d=d, pitch=pitch, s=s)
    typed = NutParams(d=d, pitch=pitch, s=s, clearance=0.3)
    expected = [MEASURED_RANGE.format(d=f"{d:g}")]
    assert _measured_range_warnings(omitted) == expected
    assert _measured_range_warnings(typed) == expected


@pytest.mark.parametrize(("d", "is_warned"), [
    (5.0, True), (6.0, False), (8.0, False), (10.0, False), (12.0, False), (14.0, True),
    (math.nextafter(6.0, 0.0), True), (math.nextafter(12.0, math.inf), True),
    (math.nextafter(6.0, math.inf), False), (math.nextafter(12.0, 0.0), False)])
def test_the_measured_range_edges_warn_on_the_outside_only(d: float, is_warned: bool) -> None:
    # model_construct: the edges are about the rule, not about which d the parameter model admits.
    nut = NutParams.model_construct(d=d, pitch=1.0, s=30.0, m=5.0, clearance=0.15, left_hand=False)
    assert bool(_measured_range_warnings(nut)) is is_warned


@pytest.mark.parametrize("d", [3.0, 5.0, 6.0, 12.0, 14.0])
def test_a_bolt_never_carries_the_measured_range_warning(d: float) -> None:
    assert _measured_range_warnings(BoltParams(d=d, s=2 * d)) == []


def test_the_measured_range_warning_changes_no_row_and_keeps_the_warning_order(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # The sentence sits after the download refusal and before the counterpart's off-row sentence,
    # which stays last (D-09, D-15): M5 x 0.8 and a tall m draws the refusal, d 5.5 the off-row.
    outside = NutParams(d=5.0, pitch=0.8, s=9.0, m=40.0, clearance=0.1)
    info = derive(outside)
    new = MEASURED_RANGE.format(d="5")
    refusal = download_refusal(outside, "stl", "fine")
    assert refusal is not None
    assert info.warnings[0] == STANDING_WARNING
    assert info.warnings.index(refusal) < info.warnings.index(new)
    off_row = derive(NutParams(d=5.5, pitch=0.8, s=9.0, m=5.0, clearance=0.1)).warnings
    assert off_row[-2] == MEASURED_RANGE.format(d="5.5")
    assert off_row[-1].startswith("no ISO 4017:2022 row for")
    # With the sentence switched off the rows and every other warning are the same: the warning is
    # the only change (L02, T-06-15).
    with monkeypatch.context() as m:
        m.setattr(calc, "measured_range_warning", lambda d, pitch: None)
        plain = derive(outside)
    assert info.rows == plain.rows
    assert [w for w in info.warnings if w != new] == plain.warnings


# --- the printability warning (INFO-04, D-11, D-13) ---------------------------------------------

THRESHOLD_TAIL = ("M4 is the smallest size that printed and threaded by hand in run "
                  "06-print-run-2 (L18); parameters left as set")


def _printability_warnings(p: FastenerParams) -> list[str]:
    return [w for w in derive(p).warnings if "run 06-print-run-2" in w]


def _at(kind: str, d: float, pitch: float) -> FastenerParams:
    # model_construct: the edges are about the rule, not about which (d, pitch) the model admits.
    if kind == "bolt":
        return BoltParams.model_construct(d=d, pitch=pitch, length=20.0, s=2 * d, k=d,
                                          thread_length=20.0, left_hand=False)
    return NutParams.model_construct(d=d, pitch=pitch, s=2 * d, m=d, clearance=0.15,
                                     left_hand=False)


def test_the_printability_warning_promises_no_build_only_unchanged_parameters() -> None:
    # Another rule can still refuse the part: this bolt also reports "this part is not built", so
    # the sentence says what the warning leaves alone and nothing about whether a part comes out.
    info = derive(BoltParams(d=3.0, pitch=0.5, length=1e-9))
    assert any("this part is not built" in w for w in info.warnings)
    (text,) = [w for w in info.warnings if "run 06-print-run-2" in w]
    assert text.endswith("parameters left as set")
    assert "built" not in text


@pytest.mark.parametrize("kind", ["bolt", "nut"])
def test_the_printability_edges_are_strict(kind: str) -> None:
    d, pitch = printability.D_MIN_MM, printability.P_MIN_MM
    assert _printability_warnings(_at(kind, d, pitch)) == []
    assert _printability_warnings(_at(kind, math.nextafter(d, math.inf), pitch)) == []
    assert _printability_warnings(_at(kind, d, math.nextafter(pitch, math.inf))) == []
    (d_only,) = _printability_warnings(_at(kind, math.nextafter(d, 0.0), pitch))
    assert d_only.startswith("d ")
    assert "pitch" not in d_only.split(":")[0]
    (pitch_only,) = _printability_warnings(_at(kind, d, math.nextafter(pitch, 0.0)))
    assert pitch_only.startswith("pitch ")
    assert "d_min" not in pitch_only


@pytest.mark.parametrize("kind", ["bolt", "nut"])
def test_a_part_below_the_printability_threshold_warns_naming_each_edge_crossed(
        kind: str) -> None:
    # M12 x 0.5 is a big part with a fine pitch: pitch only, one sentence.
    assert _printability_warnings(_at(kind, 12.0, 0.5)) == [
        f"pitch 0.5 mm is below P_min 0.7 mm: {THRESHOLD_TAIL}"]
    # M3 x 0.5 crosses both: d first, one sentence, joined by "and".
    assert _printability_warnings(_at(kind, 3.0, 0.5)) == [
        f"d 3 mm is below d_min 4 mm and pitch 0.5 mm is below P_min 0.7 mm: {THRESHOLD_TAIL}"]
    # A small d with a coarse-enough pitch: d only.
    assert _printability_warnings(_at(kind, 3.0, 0.7)) == [
        f"d 3 mm is below d_min 4 mm: {THRESHOLD_TAIL}"]
    # Above both edges: no printability entry at all.
    assert _printability_warnings(_at(kind, 8.0, 1.25)) == []


@pytest.mark.parametrize("kind", ["bolt", "nut"])
@pytest.mark.parametrize(("size", "d", "pitch"), [("M2", 2.0, 0.4), ("M2.5", 2.5, 0.45)])
def test_m2_and_m2_5_warn_on_both_printability_edges(
        kind: str, size: str, d: float, pitch: float) -> None:
    (text,) = _printability_warnings(_at(kind, d, pitch))
    assert text == (f"d {d:g} mm is below d_min 4 mm and pitch {pitch:g} mm is below P_min "
                    f"0.7 mm: {THRESHOLD_TAIL}"), size
    assert text.index("d ") < text.index("pitch ")


@pytest.mark.parametrize(("d", "pitch", "head"), [
    (3.999999, 0.7, "d 3.999999 mm is below d_min 4 mm"),
    (4.0, 0.6999999, "pitch 0.6999999 mm is below P_min 0.7 mm"),
    (3.999999, 0.6999999,
     "d 3.999999 mm is below d_min 4 mm and pitch 0.6999999 mm is below P_min 0.7 mm")])
def test_the_printability_warning_prints_the_exact_value_just_below_each_edge(
        d: float, pitch: float, head: str) -> None:
    # L02: a number the tool prints is a number someone cuts metal to. Six significant digits
    # would print d 3.999999 as "4" and call it below d_min 4 mm.
    assert printability.printability_warning(d, pitch) == f"{head}: {THRESHOLD_TAIL}"


@pytest.mark.parametrize("d", [5.999999, 12.000001])
def test_the_measured_range_warning_prints_the_exact_value_just_outside_each_edge(
        d: float) -> None:
    assert printability.measured_range_warning(d, 1.0) == MEASURED_RANGE.format(d=repr(d))


async def _inline_backend(p: FastenerParams, fmt: str, quality: str) -> bytes:
    # In process, so the check needs no pool (as tests/test_parity.py).
    return export(p, cast(Format, fmt), cast(Quality, quality))


@pytest.mark.parametrize(("kind", "params"), [
    ("bolt", {"d": 2.0, "pitch": 0.4, "s": 4.0, "k": 1.4, "length": 6.0, "thread_length": 6.0}),
    ("nut", {"d": 2.0, "pitch": 0.4, "s": 4.0, "m": 1.6})])
def test_a_part_below_the_printability_threshold_still_builds(
        kind: str, params: dict[str, float]) -> None:
    # D-13, L02: the warning is the only change; the part is neither refused nor capped.
    client = TestClient(app)
    app.dependency_overrides[build_backend] = lambda: _inline_backend
    info = client.get(f"/api/{kind}/info", params=params)
    assert info.status_code == 200
    assert sum("run 06-print-run-2" in w for w in info.json()["warnings"]) == 1
    try:
        model = client.get(f"/api/{kind}/model.stl", params={**params, "quality": "preview"})
    finally:
        app.dependency_overrides.pop(build_backend, None)
    assert model.status_code == 200
    assert len(model.content) > 84  # a binary STL header and count, plus triangles


def test_the_printability_warning_keeps_the_warning_order(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # A nut crossing both D-09 and D-13 carries two separate sentences, D-09 first; the standing
    # warning leads and the counterpart's off-row sentence stays last (D-09, D-13, D-15).
    nut = NutParams(d=5.0, pitch=0.4, s=9.0, m=4.0, clearance=0.1)
    info = derive(nut)
    outside = MEASURED_RANGE.format(d="5")
    (below,) = _printability_warnings(nut)
    assert outside != below
    assert info.warnings[0] == STANDING_WARNING
    assert info.warnings.index(outside) + 1 == info.warnings.index(below)
    off_row = derive(NutParams(d=12.0, pitch=0.5, s=19.0, m=8.0, clearance=0.1)).warnings
    assert off_row[-2].startswith("pitch 0.5 mm is below P_min 0.7 mm")
    assert off_row[-1].startswith("no ISO 4017:2022 row for")
    bolt = derive(BoltParams(d=3.0, pitch=0.5, s=5.5, k=2.0, length=10.0, thread_length=10.0))
    assert bolt.warnings[0] == STANDING_WARNING
    # With the sentence switched off the rows and every other warning are the same.
    with monkeypatch.context() as m:
        m.setattr(calc, "printability_warning", lambda d, pitch: None)
        plain = derive(nut)
    assert info.rows == plain.rows
    assert [w for w in info.warnings if w != below] == plain.warnings
