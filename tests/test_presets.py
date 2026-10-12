"""The preset catalogue through the front ends: `--preset`, the round trip and the refused count.

The tables are tested in `tests/test_tables.py` and the document in `tests/test_api.py`; this
module holds what joins them to a built part (D-09, D-10, D-11, TABL-01, THRD-03).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from screw import cli
from screw.calc import derive, download_refusal
from screw.calc.presets import PresetEntry, catalogue_document, expand
from screw.calc.thread import FINE_STL_ROWS, built_thread_length, thread_length_conflict
from screw.params import KINDS, BoltParams

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
        assert expand(kind, ROWS[0].id) == ROWS[0].fields
        assert expand(kind, "nope") is None
    assert expand("bolt", "iso4017:m6x20") is None, "ids are case-sensitive"
    with pytest.raises(TypeError, match="nut"):
        expand("nut", ROWS[0].id)
    with pytest.raises(TypeError, match="nut"):
        catalogue_document("nut")


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
