"""The preset catalogue through the front ends: `--preset`, the round trip and the refused count.

The tables are tested in `tests/test_tables.py` and the document in `tests/test_api.py`; this
module holds what joins them to a built part (D-09, D-10, D-11, TABL-01, THRD-03).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from screw import cli
from screw.calc import derive, download_refusal
from screw.calc.presets import PresetEntry, catalogue_document, expand
from screw.calc.thread import FINE_STL_ROWS, built_thread_length, thread_length_conflict
from screw.params import KINDS, BoltParams, NutParams

ROWS = catalogue_document("bolt").rows


def _info(argv: list[str], capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    capsys.readouterr()
    cli.main(["info", "bolt", *argv])
    document: dict[str, object] = json.loads(capsys.readouterr().out)
    return document


def _exit(argv: list[str]) -> str | int | None:
    with pytest.raises(SystemExit) as stop:
        cli.main(argv)
    return stop.value.code


def _row_values(document: dict[str, object]) -> dict[str, float]:
    rows = document["rows"]
    assert isinstance(rows, list)
    return {row["key"]: row["value"] for row in rows}


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r.id)
def test_every_catalogue_row_round_trips(row: PresetEntry) -> None:
    # The invariant accepted at the assumption-delta checkpoint: a row's fields build a valid
    # part, that part reads back as the exact match of its own id, and `expand` returns the
    # same fields. Nothing here consults a nearest row (D-09).
    p = BoltParams.model_validate(row.fields)
    preset = derive(p).preset
    assert preset is not None
    assert preset.status == "exact"
    assert preset.id == row.id
    assert preset.display == row.display
    assert expand("bolt", row.id) == row.fields
    # The CLI's conflict rule would otherwise refuse the row's own fields on `--preset`.
    assert thread_length_conflict(row.fields["length"], row.fields["thread_length"]) is None


def test_every_kind_expands_and_an_unknown_id_is_none() -> None:
    for kind in KINDS:
        assert expand(kind, "nope") is None
    assert expand("bolt", ROWS[0].id) == ROWS[0].fields
    assert expand("bolt", "iso4017:m6x20") is None, "ids are case-sensitive"
    # A bolt's id is not a nut's, and every registered kind has a non-empty catalogue.
    assert expand("nut", "iso4017:M6x20") is None
    assert expand("bolt", "iso4032:M6") is None
    for kind in KINDS:
        assert catalogue_document(kind).rows, kind
    with pytest.raises(TypeError, match="washer"):
        expand("washer", ROWS[0].id)
    with pytest.raises(TypeError, match="washer"):
        catalogue_document("washer")


def test_the_preset_m6_x_20_is_the_part_the_empty_command_builds(
        capsys: pytest.CaptureFixture[str]) -> None:
    # D-09: the empty query is the ISO 4017 M6 x 20 exact match, so the preset adds nothing.
    assert _info(["--preset", "iso4017:M6x20"], capsys) == _info([], capsys)


def test_an_iso_4014_preset_fills_the_thread_length_from_its_band(
        capsys: pytest.CaptureFixture[str]) -> None:
    document = _info(["--preset", "iso4014:M10x80"], capsys)
    values = _row_values(document)
    assert values["d"] == 10.0
    assert values["length"] == 80.0
    assert values["thread_length"] == 26.0
    assert document["preset"] == {"status": "exact", "id": "iso4014:M10x80",
                                  "display": "ISO 4014 M10 \u00d7 80"}


def test_an_explicit_flag_wins_over_the_preset(capsys: pytest.CaptureFixture[str]) -> None:
    document = _info(["--preset", "iso4014:M10x80", "--length", "85"], capsys)
    values = _row_values(document)
    assert values["length"] == 85.0
    assert values["thread_length"] == 26.0
    preset = document["preset"]
    assert isinstance(preset, dict)
    assert preset["status"] == "custom"
    assert preset["id"] is None
    # A flag beside a preset changes only that field: the pitch is still the row's.
    assert _row_values(_info(["--preset", "iso4014:M10x80", "--d", "8"], capsys))["pitch"] == 1.5


def test_a_conflict_between_the_preset_and_an_explicit_flag_exits_2_naming_both_fields(
        capsys: pytest.CaptureFixture[str]) -> None:
    capsys.readouterr()
    assert _exit(["info", "bolt", "--preset", "iso4014:M10x80", "--length", "20"]) == 2
    assert capsys.readouterr().err.startswith("error: thread_length and length: ")


def test_a_preset_never_sets_the_head_chamfer(capsys: pytest.CaptureFixture[str]) -> None:
    # D-13: the standard prints a 15 to 30 degree band, not a number, so no row carries an angle.
    for row in ROWS:
        assert "head_chamfer" not in row.fields, row.id
        assert "head_chamfer" not in (expand("bolt", row.id) or {}), row.id
    exact = ["--preset", "iso4017:M6x20"]
    plain = _info(exact, capsys)
    assert _row_values(plain)["head_chamfer"] == 30.0
    typed = _info([*exact, "--head-chamfer", "15"], capsys)
    assert _row_values(typed)["head_chamfer"] == 15.0
    for document in (plain, typed):
        preset = document["preset"]
        assert isinstance(preset, dict)
        assert preset["status"] == "exact"


def test_a_preset_beside_an_explicit_head_chamfer_deeper_than_half_its_k_exits_2(
        capsys: pytest.CaptureFixture[str]) -> None:
    # D-05: the preset's s and k count as given, because the flags are laid over the row first.
    capsys.readouterr()
    assert _exit(["info", "bolt", "--preset", "iso4017:M6x20", "--head-chamfer", "80"]) == 2
    assert capsys.readouterr().err.startswith("error: head_chamfer and k: ")


def test_an_unknown_preset_exits_2_naming_it_and_where_to_list_them(
        capsys: pytest.CaptureFixture[str]) -> None:
    capsys.readouterr()
    assert _exit(["info", "bolt", "--preset", "iso4017:M99x1"]) == 2
    err = capsys.readouterr().err
    assert "iso4017:M99x1" in err
    assert "screw presets bolt" in err
    assert _exit(["info", "bolt", "--preset", "iso4017:m6x20"]) == 2, "ids are case-sensitive"


def test_a_repeated_preset_exits_2_on_info_and_on_export(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    capsys.readouterr()
    twice = ["--preset", "iso4017:M6x20", "--preset", "iso4017:M6x25"]
    assert _exit(["info", "bolt", *twice]) == 2
    assert "--preset" in capsys.readouterr().err
    assert _exit(["export", "bolt", "-o", str(tmp_path / "x.stl"), *twice]) == 2
    assert "--preset" in capsys.readouterr().err


def test_export_builds_the_preset_part(tmp_path: Path) -> None:
    out = tmp_path / "x.stl"
    cli.main(["export", "bolt", "--preset", "iso4017:M6x20", "-o", str(out),
              "--quality", "preview"])
    assert len(out.read_bytes()) > 84


def test_an_export_of_a_preset_refused_as_a_fine_stl_exits_2_and_writes_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "x.stl"
    capsys.readouterr()
    assert _exit(["export", "bolt", "--preset", "iso4017:M8x70", "-o", str(out)]) == 2
    assert "2026-10-08-a-grid" in capsys.readouterr().err
    assert not out.exists()


def test_the_fine_stl_refused_presets_are_counted() -> None:
    # TYPE-02: the ISO 4017 rows are threaded to the head, so a long screw is a long thread and
    # the right-hand caps of `2026-10-08-a-grid` (FINE_STL_ROWS) refuse its fine STL. 62 is the
    # count the shipped catalogue yields, which is what RESEARCH Alert 7 estimated; the Phase 7
    # re-sweep moves the caps and with them this literal. Every ISO 4014 row is threaded only
    # b of the way, so none is refused.
    refused: list[str] = []
    for row in ROWS:
        p = BoltParams.model_validate(row.fields)
        if download_refusal(p, "stl", "fine") is None:
            continue
        refused.append(row.id)
        assert row.id.startswith("iso4017:"), row.id
        assert built_thread_length(p.thread_length, p.length) > FINE_STL_ROWS[
            p.d, p.pitch, p.left_hand], row.id
    assert len(refused) == 62
    longest = max(row.fields["length"] for row in ROWS if row.id.startswith("iso4017:"))
    assert longest == 200.0


def test_every_catalogue_rows_document_agrees_with_the_shared_download_rule() -> None:
    # G-04-3, T-04-29: the page links the first served entry per format (plan 04-16), so a row
    # whose document disagreed with the rule `_serve` and `screw export` call would link a 422.
    for row in ROWS:
        p = BoltParams.model_validate(row.fields)
        downloads = derive(p).downloads
        for entry in downloads:
            assert entry.refusal == download_refusal(p, entry.format, entry.quality), row.id
            if entry.format == "step":
                assert entry.refusal is None, row.id
        # No preset leaves a format without a link.
        served = {e.format for e in downloads if e.refusal is None}
        assert served == {e.format for e in downloads}, row.id


def test_the_rows_whose_stl_falls_back_to_the_preview_are_the_fine_stl_refused_rows() -> None:
    # Both lists are read from the catalogue, never typed: rule 17 applied in Python to the
    # document's STL entries against the rule itself. TYPE-02: only the long ISO 4017 screws,
    # threaded to the head, are past a cap; no ISO 4014 row is threaded past its own.
    falls_back: list[str] = []
    refused: list[str] = []
    for row in ROWS:
        p = BoltParams.model_validate(row.fields)
        stl = [e for e in derive(p).downloads if e.format == "stl"]
        first_served = next(e for e in stl if e.refusal is None)
        if first_served is not stl[0] and first_served.quality == "preview":
            falls_back.append(row.id)
        if download_refusal(p, "stl", "fine") is not None:
            refused.append(row.id)
    assert falls_back
    assert falls_back == refused
    assert all(row_id.startswith("iso4017:") for row_id in falls_back)


NUT_ROWS = catalogue_document("nut").rows
# The sizes GOST ISO 4032-2014 prints from M2 to M20; it prints no M7 (05-OWNER-READS.md).
NUT_SIZES = ["M2", "M2.5", "M3", "M3.5", "M4", "M5", "M6", "M8", "M10", "M12", "M14", "M16",
             "M18", "M20"]
# ISO 262's second-choice sizes among them; they are also the sizes the text prints in Table 2.
SECOND_CHOICE = {"M3.5", "M14", "M18"}


def test_the_nut_catalogue_is_the_fourteen_gost_iso_4032_rows_with_no_m7() -> None:
    document = catalogue_document("nut")
    assert document.axes == ["Standard", "Size"]
    assert [row.id for row in document.rows] == [f"iso4032:{size}" for size in NUT_SIZES]
    assert "iso4032:M7" not in {row.id for row in document.rows}
    assert len({row.id for row in document.rows}) == len(NUT_ROWS) == 14


@pytest.mark.parametrize("row", NUT_ROWS, ids=lambda r: r.id)
def test_every_nut_row_reads_the_same_in_the_picker_the_display_and_the_citation(
        row: PresetEntry) -> None:
    size = row.id.removeprefix("iso4032:")
    bracketed = size in SECOND_CHOICE
    shown = f"({size})" if bracketed else size
    # Every display is exactly `ISO 4032 <size>`, bracketed for a second choice, no suffix (owner
    # ruling 2026-10-20: no informative rows).
    assert row.display == f"ISO 4032 {shown}"
    assert re.fullmatch(r"ISO 4032 (M[0-9.]+|\(M[0-9.]+\))", row.display)
    assert row.picker == ["ISO 4032", shown]
    assert row.designation == (
        f"Hexagon regular nut GOST ISO 4032 - {size.replace('.', ',')}")
    assert list(row.fields) == ["d", "pitch", "s", "m"]
    # M3.5, M14 and M18 are Table 2 (additional threads); every other size is Table 1.
    table = "Table 2" if bracketed else "Table 1"
    assert f"GOST ISO 4032-2014 (ISO 4032:2012) {table}" in row.citation


def test_a_nut_row_expands_to_its_four_millimetre_fields() -> None:
    assert expand("nut", "iso4032:M6") == {"d": 6.0, "pitch": 1.0, "s": 10.0, "m": 5.2}
    assert expand("nut", "iso4032:M3.5") == {"d": 3.5, "pitch": 0.6, "s": 6.0, "m": 2.8}
    assert expand("nut", "iso4032:m6") is None, "ids are case-sensitive"
    assert expand("nut", "iso4032:M7") is None, "the text prints no M7"
    assert expand("nut", "iso4017:M6x20") is None


def test_a_nut_row_writes_only_fields_the_nut_has_and_never_the_pair_fields() -> None:
    # Picking a row leaves `clearance` and `left_hand` as the user set them (D-01, D-17).
    names = {name for row in NUT_ROWS for name in row.fields}
    assert names == {"d", "pitch", "s", "m"}
    assert names <= set(NutParams.model_fields)


def test_the_screw_presets_nut_command_prints_the_catalogue_document(
        capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["presets", "nut"])
    printed = json.loads(capsys.readouterr().out)
    assert printed == json.loads(catalogue_document("nut").model_dump_json())
    assert len(printed["rows"]) == 14
