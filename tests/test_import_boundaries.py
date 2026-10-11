"""The runtime half of import-linter contract 6 (SC2): a link rebuilds without a table.

grimp does not model the package `__init__` edge, so a contract on `screw.params` and
`screw.calc.thread` passes even when `screw/calc/__init__.py` imports the tables at import time
(RESEARCH Alert 3). A fresh interpreter, `-I` so no environment or user site leaks in, is the
only thing that sees what a process actually loads.
"""

from __future__ import annotations

import subprocess
import sys

import pytest


def _loads_tables(code: str) -> bool:
    out = subprocess.run(
        [sys.executable, "-I", "-c", f"import sys; {code}; print('screw.tables' in sys.modules)"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert out in {"True", "False"}, out
    return out == "True"


@pytest.mark.parametrize(
    "code",
    ["from screw.params import BoltParams; BoltParams()", "import screw.solid"],
    ids=["BoltParams", "screw.solid"],
)
def test_a_part_is_rebuilt_from_its_fields_without_loading_a_table(code: str) -> None:
    assert _loads_tables(code) is False


def test_the_probe_sees_the_tables_once_they_are_imported() -> None:
    # The control: without it a probe that always prints False would pass the test above.
    assert _loads_tables("import screw.tables.presets") is True


def test_deriving_the_info_document_loads_the_tables_it_matches_against() -> None:
    # The converse (04-08): `_bolt` reads the catalogue to report the matching row, so a probe
    # that stayed False here would mean the match never ran. `derive` is the only way in.
    assert _loads_tables("from screw.calc import derive; from screw.params import BoltParams;"
                         " derive(BoltParams())") is True


def test_importing_the_calc_package_alone_does_not_load_the_tables() -> None:
    # `screw.calc.thread` runs `screw/calc/__init__.py`, so a top-of-module import of
    # `screw.calc.presets` there would put the tables behind every rebuilt link.
    assert _loads_tables("import screw.calc") is False
