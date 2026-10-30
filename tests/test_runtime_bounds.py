"""The runtime values stay tied to their evidence (07-16; T-07-40): `runtime.json` is exactly what
`bench.oper_sets.derive_runtime` writes from every committed runner record under
`bench/results/phase-07/`, and every shipped value is the one it derived. A hand edit of either
side, a record added without re-deriving, or a constant typed from a figure fails here.
"""

from __future__ import annotations

import json
from pathlib import Path

from bench import oper_sets
from screw.calc import cost

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDS = REPO_ROOT / "bench/results/phase-07"
RUNTIME = REPO_ROOT / oper_sets.RUNTIME


def _directories() -> list[Path]:
    return sorted(path for path in RECORDS.iterdir() if path.is_dir())


def test_runtime_json_is_what_derive_runtime_writes_from_every_committed_record() -> None:
    assert RUNTIME.read_text() == oper_sets.runtime_text(_directories())


def test_the_shipped_build_timeouts_are_the_derived_ones() -> None:
    derived = json.loads(RUNTIME.read_text())["timeouts"]
    assert dict(cost.BUILD_TIMEOUT_S) == {artifact: float(row["seconds"])
                                          for artifact, row in derived.items()}
