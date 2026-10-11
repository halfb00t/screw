"""The slow tier of SC4 (D-14): the whole measured thread grid through the THRD-04 gate.

The corpus is the spike's own (`bench.thread_spike.maths.lengths`, never re-picked: the corpus
rule in bench/README.md), both hands, rod and void at `VOID_CLEARANCE`, each row built by
`helical.thread` and judged by `check_solid` against the closed form, the same gate a served
build passes. It records and never gates `main`: `.github/workflows/grid.yml` and `make grid` run
it, `make verify` deselects it (`-m 'not grid'` in pyproject.toml), and nothing here asserts a
timing (02 D-15).

The unmarked tests run in `make verify` and read no kernel: they pin what makes the tier safe,
the cell ids a size selects, the row count, and the workflow's triggers and permissions.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from bench.thread_spike import maths
from screw.calc.thread import closed_volume
from screw.solid import check_solid
from screw.solid.helical import thread
from scripts.pr_land import WORKFLOW

REPO_ROOT = Path(__file__).resolve().parents[1]
GRID_YML = REPO_ROOT / ".github" / "workflows" / "grid.yml"
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_JOBS = REPO_ROOT / ".github" / "workflows" / "required-jobs.txt"

# The 02 D-03 corpus is 7160 rows (15 sizes x right/left x rod/void x every length): the figure
# L11 cites for the host grid. A change to the corpus is a decision, not a drift.
ROWS = 7160
# End faces must sit at z = 0 and z = length to this many mm (a bounding box adds a little slack).
END_FACE_MM = 1e-6

CELLS = [(size, left, kind) for size in maths.SIZES for left in (False, True)
         for kind in ("rod", "void")]


def _id(cell: tuple[str, bool, str]) -> str:
    size, left, kind = cell
    return f"{size}-{'left' if left else 'right'}-{kind}"


IDS = [_id(cell) for cell in CELLS]


@pytest.mark.grid
@pytest.mark.parametrize(("size", "left_hand", "kind"), CELLS, ids=IDS)
def test_every_row_of_a_cell_passes_the_gate_and_ends_at_its_length(
        size: str, left_hand: bool, kind: str) -> None:
    d, pitch = (float(x) for x in maths.PITCH[size])
    clearance = maths.VOID_CLEARANCE if kind == "void" else 0.0
    lengths = maths.lengths(*maths.PITCH[size])
    failures: list[str] = []
    for exact in lengths:
        length = float(exact)
        where = f"{size} {'left' if left_hand else 'right'} {kind} length {length:g}"
        try:
            shape = thread(d, pitch, length, clearance=clearance, left_hand=left_hand)
            check_solid(shape, closed_volume(d, pitch, length, clearance))
            box = shape.BoundingBox()
            if abs(box.zmin) > END_FACE_MM or abs(box.zmax - length) > END_FACE_MM:
                failures.append(f"{where}: z spans [{box.zmin:.9f}, {box.zmax:.9f}]")
        except Exception as exc:  # any failure is that row's finding, listed with the rest
            failures.append(f"{where}: {type(exc).__name__}: {exc}")
    assert not failures, f"{len(failures)} of {len(lengths)} rows failed:\n" + "\n".join(failures)


def test_a_size_selects_exactly_its_four_cells_by_id() -> None:
    """`make grid SIZE=M3` runs `-k 'M3-'`, which matches case-insensitively as a substring:
    M2 must not pull in M12, nor M3 in M3.5."""
    for size in maths.SIZES:
        selected = [i for i in IDS if f"{size}-".lower() in i.lower()]
        assert selected == [f"{size}-{hand}-{kind}" for hand in ("right", "left")
                            for kind in ("rod", "void")]
    assert len(IDS) == len(set(IDS)) == 60


def test_the_grid_is_the_measured_7160_row_corpus() -> None:
    assert sum(len(maths.lengths(*maths.PITCH[size])) for size in maths.SIZES) * 4 == ROWS


def test_the_grid_marker_is_registered_and_deselected_by_default() -> None:
    options = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["tool"]["pytest"][
        "ini_options"]
    assert "-m 'not grid'" in options["addopts"]
    assert any(m.startswith("grid:") for m in options["markers"])


def test_the_grid_workflow_has_no_pull_request_or_push_trigger_and_reads_only() -> None:
    """T-3-14: no fork code runs with this token, and the token cannot write."""
    text = GRID_YML.read_text()
    assert "workflow_dispatch:" in text
    assert re.search(r"^\s*schedule:", text, re.MULTILINE)
    assert not re.search(r"^\s*(pull_request|pull_request_target|push)\s*:", text, re.MULTILINE)
    assert re.search(r"^permissions:\n  contents: read$", text, re.MULTILINE)
    assert "secrets." not in text
    assert "make grid" in text


def test_the_grid_workflow_matrix_is_exactly_the_measured_sizes_in_order() -> None:
    match = re.search(r"^\s*size:\s*\[([^\]]*)\]", GRID_YML.read_text(), re.MULTILINE)
    assert match is not None, "no `size: [...]` matrix found in grid.yml"
    assert tuple(s.strip().strip('"') for s in match.group(1).split(",")) == maths.SIZES


def test_the_grid_tier_is_not_a_required_job() -> None:
    """D-14, L08: every job in ci.yml is required, so the slow tier lives in its own workflow
    and `make pr.land` reads ci.yml runs only."""
    ci = CI_YML.read_text()
    assert "grid" not in ci  # neither `make grid` nor `-m grid`
    required = [line for line in REQUIRED_JOBS.read_text().splitlines()
                if line.strip() and not line.startswith("#")]
    assert not [name for name in required if name.startswith("grid")]
    assert WORKFLOW == "ci.yml"
