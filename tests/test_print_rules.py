"""The home of Phase 6's printed-test tests: the rules and the strict reader of the owner's record.

The synthetic records here are positive and negative controls written before any real record, so
every rule and the escape clause are shown to fire before the data exists (PAIR-02, INFO-04). The
tests read no kernel and no product code beyond the ISO 262 table the rule module's literal is
pinned to.
"""

from __future__ import annotations

import hashlib
import random
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from bench import print_matrix as matrix
from bench import print_rules as rules
from screw.calc.presets import expand
from screw.tables import iso262

type MatrixOk = Callable[[str, float, int], bool]
type SizedOk = Callable[[str, int], bool]


def _matrix(ok: MatrixOk) -> dict[tuple[str, float, int], bool]:
    return {(s, c, n): ok(s, c, n) for (s, c, n) in rules.matrix_keys()}


def _small(ok: SizedOk) -> dict[tuple[str, int], bool]:
    return {(s, n): ok(s, n) for (s, n) in rules.small_keys()}


def _text(columns: tuple[str, ...], rows: list[list[str]]) -> str:
    return "\n".join(["\t".join(columns), *("\t".join(r) for r in rows)]) + "\n"


def _result_cells(is_pass: bool) -> list[str]:
    """`result`, `turns` and `note` of one sample."""
    return ["pass", "-", "-"] if is_pass else ["bind", "2", "-"]


def _matrix_rows(ok: MatrixOk) -> list[list[str]]:
    return [[s, repr(c), str(n), "P1", str(rules.LADDER.index(c) + 1), *_result_cells(ok(s, c, n))]
            for (s, c, n) in rules.matrix_keys()]


def _small_rows(ok: SizedOk) -> list[list[str]]:
    return [[s, str(n), "P1", *_result_cells(ok(s, n))] for (s, n) in rules.small_keys()]


def _from_015(s: str, c: float, n: int) -> bool:
    return c >= 0.15


def test_the_default_is_the_smallest_step_every_size_passes_from_there_up() -> None:
    assert rules.default_from(_matrix(lambda s, c, n: True)) == 0.05
    assert rules.default_from(_matrix(_from_015)) == 0.15
    # M12 alone needs 0.25: the other three sizes do not lower it.
    assert rules.default_from(_matrix(lambda s, c, n: s != "M12" or c >= 0.25)) == 0.25


def test_two_of_three_is_not_a_passing_cell() -> None:
    def ok(s: str, c: float, n: int) -> bool:
        return c >= 0.1 and not (s == "M8" and c == 0.1 and n == 2)

    assert rules.default_from(_matrix(ok)) == 0.15


@pytest.mark.parametrize("ok", [
    lambda s, c, n: s != "M10",
    lambda s, c, n: not (s == "M10" and c == 0.25),
], ids=["a-size-never-passes", "a-size-binds-at-the-top-step"])
def test_no_default_ships_when_no_step_passes_at_every_size(ok: MatrixOk) -> None:
    assert rules.default_from(_matrix(ok)) is None


def test_no_default_ships_when_a_size_is_not_monotone() -> None:
    # M8 passes at 0.1 and binds one sample at 0.15, while every step from 0.2 up passes at
    # every size: without the monotone clause this would read as 0.2.
    def ok(s: str, c: float, n: int) -> bool:
        return not (s == "M8" and c == 0.15 and n == 1)

    assert rules.default_from(_matrix(ok)) is None


def test_the_default_does_not_depend_on_the_order_of_the_rows() -> None:
    def ok(s: str, c: float, n: int) -> bool:
        return c >= 0.15 or (s == "M6" and n != 3)

    rows = _matrix_rows(ok)
    ordered = rules.default_from(rules.read_matrix(_text(rules.MATRIX_COLUMNS, rows)))
    random.Random(6).shuffle(rows)
    shuffled = rules.default_from(rules.read_matrix(_text(rules.MATRIX_COLUMNS, rows)))
    assert ordered == shuffled == 0.15


def test_a_complete_record_is_read_as_written() -> None:
    def ok(s: str, c: float, n: int) -> bool:
        return c >= 0.1 and (s, n) != ("M10", 2)

    assert rules.read_matrix(_text(rules.MATRIX_COLUMNS, _matrix_rows(ok))) == _matrix(ok)
    assert rules.read_small(_text(rules.SMALL_COLUMNS, _small_rows(lambda s, n: s != "M3"))) \
        == _small(lambda s, n: s != "M3")


def _set(row: int, column: str, value: str) -> Callable[[list[str], list[list[str]]], None]:
    def edit(header: list[str], rows: list[list[str]]) -> None:
        rows[row][rules.MATRIX_COLUMNS.index(column)] = value
    return edit


def _bind_with(row: int, turns: str, note: str) -> Callable[[list[str], list[list[str]]], None]:
    def edit(header: list[str], rows: list[list[str]]) -> None:
        rows[row][5:8] = ["bind", turns, note]
    return edit


def _duplicate(header: list[str], rows: list[list[str]]) -> None:
    rows.append(list(rows[0]))


def _drop_last(header: list[str], rows: list[list[str]]) -> None:
    del rows[-1]


def _rename_note(header: list[str], rows: list[list[str]]) -> None:
    header[7] = "notes"


def _extra_cell(header: list[str], rows: list[list[str]]) -> None:
    rows[0].append("x")


# (what is wrong, the edit, the line the reader must name). Row i of the record is line i + 2.
DEFECTS: list[tuple[str, Callable[[list[str], list[list[str]]], None], int]] = [
    ("blank-cell", _set(3, "plate", ""), 5),
    ("capitalised-result", _set(0, "result", "Pass"), 2),
    ("trailing-space", _set(1, "plate", "P1 "), 3),
    ("bind-without-turns", _bind_with(2, "-", "-"), 4),
    ("pass-with-turns", _set(2, "turns", "1"), 4),
    ("loose-on-a-bind", _bind_with(2, "1", "loose"), 4),
    ("fourth-sample", _set(0, "sample", "4"), 2),
    ("duplicated-row", _duplicate, 62),
    ("missing-row", _drop_last, 60),
    ("size-not-pre-registered", _set(0, "size", "M7"), 2),
    ("clearance-off-the-ladder", _set(0, "clearance", "0.12"), 2),
    ("wrong-header", _rename_note, 1),
    ("extra-column", _extra_cell, 2),
    ("orders-not-one-to-five", _set(0, "order", "2"), 6),
]


@pytest.mark.parametrize(("edit", "line"), [(d[1], d[2]) for d in DEFECTS],
                         ids=[d[0] for d in DEFECTS])
def test_an_incomplete_or_ambiguous_record_is_refused_naming_the_line(
    edit: Callable[[list[str], list[list[str]]], None], line: int
) -> None:
    header = list(rules.MATRIX_COLUMNS)
    rows = _matrix_rows(lambda s, c, n: True)
    edit(header, rows)
    text = "\n".join(["\t".join(header), *("\t".join(r) for r in rows)]) + "\n"
    with pytest.raises(ValueError, match=rf"^line {line}: "):
        rules.read_matrix(text)


def test_the_small_record_is_refused_as_strictly() -> None:
    small = _small_rows(lambda s, n: True)
    small[0][0] = "M6"    # a main-matrix size does not belong to run 2
    with pytest.raises(ValueError, match=r"^line 2: "):
        rules.read_small(_text(rules.SMALL_COLUMNS, small))
    with pytest.raises(ValueError, match=r"^line 1: "):
        rules.read_small("")


def test_a_record_that_is_not_the_pinned_one_is_refused(tmp_path: Path) -> None:
    record = tmp_path / "record.tsv"
    record.write_text("size\n", encoding="utf-8")
    digest = hashlib.sha256(record.read_bytes()).hexdigest()
    assert rules.load(record, digest) == "size\n"
    with pytest.raises(ValueError, match=rf"{digest}.*{'0' * 64}"):
        rules.load(record, "0" * 64)


def test_a_rule_given_fewer_keys_than_pre_registered_refuses() -> None:
    matrix = _matrix(lambda s, c, n: True)
    del matrix[("M6", 0.05, 1)]
    with pytest.raises(ValueError, match="pre-registers 60"):
        rules.default_from(matrix)
    small = _small(lambda s, n: True)
    del small[("M3", 1)]
    with pytest.raises(ValueError, match="pre-registers 9"):
        rules.threshold_from(small)


@pytest.mark.parametrize(("ok", "threshold"), [
    (lambda s, n: True, "M3"),
    (lambda s, n: not (s == "M3" and n == 2), "M4"),
    (lambda s, n: s != "M4", "M5"),
    (lambda s, n: s != "M5", "M6"),
], ids=["all-pass", "m3-binds-once", "m4-binds-m3-and-m5-pass", "m5-binds"])
def test_the_threshold_is_the_smallest_small_size_that_and_every_larger_one_pass(
    ok: SizedOk, threshold: str
) -> None:
    assert rules.threshold_from(_small(ok)) == threshold


def test_the_coarse_sizes_are_the_iso_262_rows() -> None:
    by_label = {size.label: (size.d, size.pitch) for size in iso262.SIZES}
    assert {label: by_label[label] for label in rules.COARSE} == rules.COARSE
    assert set(rules.COARSE) == {*rules.SIZES, *rules.SMALL_SIZES}


def test_the_matrix_prints_exactly_the_pre_registered_parts() -> None:
    run_1 = matrix.exports("run-1")
    assert len(run_1) == 24
    assert [a[3] for a in run_1[:4]] == ["iso4017:M6x12", "iso4017:M8x16", "iso4017:M10x20",
                                         "iso4017:M12x25"]
    assert all(a[:2] == ["export", "bolt"] and "--clearance" not in a for a in run_1[:4])
    assert run_1[4:] == [
        ["export", "nut", "--preset", f"iso4032:{s}", "--clearance", repr(c),
         "--format", "stl", "--quality", "fine"]
        for s in rules.SIZES for c in rules.LADDER]
    # D-10, D-16: these nuts take the shipped default, so no list may name a clearance.
    run_2 = matrix.exports("run-2")
    assert [a[1:4] for a in run_2] == [
        ["bolt", "--preset", "iso4017:M3x6"], ["bolt", "--preset", "iso4017:M4x8"],
        ["bolt", "--preset", "iso4017:M5x10"], ["nut", "--preset", "iso4032:M3"],
        ["nut", "--preset", "iso4032:M4"], ["nut", "--preset", "iso4032:M5"]]
    acceptance = matrix.exports("acceptance")
    assert [a[1:4] for a in acceptance] == [["bolt", "--preset", "iso4017:M8x16"],
                                            ["nut", "--preset", "iso4032:M8"]]
    assert not any("--clearance" in a for a in run_2 + acceptance)
    assert all(a[-4:] == ["--format", "stl", "--quality", "fine"] for a in run_1 + run_2)
    with pytest.raises(ValueError, match="unknown run"):
        matrix.exports("run-3")


def test_every_print_preset_is_a_catalogue_row_of_its_size() -> None:
    for size, (d, pitch) in rules.COARSE.items():
        for kind, presets in (("bolt", matrix.BOLT_PRESETS), ("nut", matrix.NUT_PRESETS)):
            row = expand(kind, presets[size])
            assert row is not None, presets[size]
            assert (row["d"], row["pitch"]) == (d, pitch)


def _key_columns(path: Path, width: int) -> list[tuple[str, ...]]:
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[-1] == ""
    return [tuple(line.split("\t")[:width]) for line in lines[1:-1]]


def test_the_committed_records_list_every_sample_in_order() -> None:
    assert _key_columns(rules.RUN_1, 3) == [
        (s, repr(c), str(n)) for s, c, n in rules.matrix_keys()]
    assert _key_columns(rules.RUN_2, 2) == [(s, str(n)) for s, n in rules.small_keys()]


@pytest.mark.parametrize(("record", "read"), [
    ("run-1", rules.read_matrix), ("run-2", rules.read_small)])
def test_an_unfilled_record_is_refused_at_its_first_row(
    record: str, read: Callable[[str], object]
) -> None:
    with pytest.raises(ValueError, match=r"^line 2: "):
        read(matrix.template(record))


def test_a_template_is_never_written_over_a_record(tmp_path: Path) -> None:
    record = tmp_path / "print-run-1.tsv"
    text = matrix.template("run-1")
    matrix.write_template(record, text)
    matrix.write_template(record, text)    # the same bytes again is not an overwrite
    filled = text.replace("\t\t\t\t\n", "\tP1\t1\tpass\t-\t-\n", 1)
    record.write_text(filled, encoding="utf-8")
    with pytest.raises(ValueError, match=r"print-run-1\.tsv"):
        matrix.write_template(record, text)
    assert record.read_text(encoding="utf-8") == filled


def _no_subprocess(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
    pytest.fail("an export ran into a directory that is not empty")


def test_an_export_refuses_a_directory_that_holds_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "stl"
    out.mkdir()
    (out / "kept.stl").write_bytes(b"a part someone printed from")
    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    with pytest.raises(ValueError, match="stl"):
        matrix.export("acceptance", out, results=tmp_path)
    assert [p.name for p in out.iterdir()] == ["kept.stl"]


def test_an_export_writes_a_manifest_of_name_bytes_and_digest_and_never_overwrites_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool) -> subprocess.CompletedProcess[bytes]:
        out = Path(cmd[cmd.index("-o") + 1])
        (out / f"part{len(calls)}.stl").write_bytes(b"x" * (len(calls) + 1))
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    manifest = matrix.export("acceptance", tmp_path / "stl", results=tmp_path)
    assert manifest == tmp_path / "manifest-acceptance.tsv"
    assert [c[4:7] for c in calls] == [["bolt", "--preset", "iso4017:M8x16"],
                                       ["nut", "--preset", "iso4032:M8"]]
    assert all(c[-2:] == ["-o", str(tmp_path / "stl")] for c in calls)
    assert manifest.read_text(encoding="utf-8").split("\n") == [
        "name\tbytes\tsha256",
        f"part0.stl\t1\t{hashlib.sha256(b'x').hexdigest()}",
        f"part1.stl\t2\t{hashlib.sha256(b'xx').hexdigest()}",
        ""]
    with pytest.raises(ValueError, match=r"manifest-acceptance\.tsv"):
        matrix.export("acceptance", tmp_path / "stl-again", results=tmp_path)


# The protocol is pre-registered text and the rule module is the code that reads the record: these
# two tests fail the moment they name different numbers, so the method a reader sees is the one
# that runs (SC1).
PROTOCOL = (rules.ROOT / ".planning" / "phases" / "06-printed-pair-acceptance"
            / "06-PRINT-PROTOCOL.md")


def test_the_protocol_has_the_pre_registered_sections_in_order() -> None:
    headings = [line[3:] for line in PROTOCOL.read_text(encoding="utf-8").split("\n")
                if line.startswith("## ")]
    assert headings == ["Question", "Owner rulings", "Print profile", "Method", "Records", "Rules",
                        "Predictions", "Escape clause", "Results"]


def test_the_protocol_states_the_numbers_the_rules_read() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")
    columns = {*rules.MATRIX_COLUMNS, *rules.SMALL_COLUMNS}
    wanted = [
        *(f"{c:.2f}" for c in rules.LADDER),
        *rules.SIZES,
        *rules.SMALL_SIZES,
        *(f"| {s} | {d:g} | {p:.2f} |" for s, (d, p) in rules.COARSE.items()),
        *matrix.BOLT_PRESETS.values(),
        *matrix.NUT_PRESETS.values(),
        "60 nuts", "12 bolts", "9 bolts and 9 nuts", f"{rules.SAMPLES} samples",
        *(p.relative_to(rules.ROOT).as_posix() for p in (rules.RUN_1, rules.RUN_2)),
        *(f"`{c}`" for c in sorted(columns)),
        "default_from", "threshold_from",
    ]
    assert [w for w in wanted if w not in text] == []
    # The counts above are the matrix's own, not just words that happen to agree with it.
    assert len(rules.matrix_keys()) == 60
    assert len(rules.small_keys()) == 9


def test_the_protocol_has_no_owner_slot_left() -> None:
    # The owner's profile is typed before PR A opens (D-06): a slot still holding its marker, or a
    # profile line that is empty after its colon, would pre-register nothing.
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "OWNER-SLOT" not in text
    lines = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
             for line in text.split("\n") if line.startswith("- ") and ":" in line}
    for label in ("Printer", "Material", "Layer height", "Slicer and profile"):
        assert lines[f"- {label}"] != "", label
