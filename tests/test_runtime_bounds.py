"""The runtime values stay tied to their evidence (07-16; T-07-40): `runtime.json` is exactly what
`bench.oper_sets.derive_runtime` writes from every committed runner record under
`bench/results/phase-07/`, and every shipped value is the one it derived. A hand edit of either
side, a record added without re-deriving, or a constant typed from a figure fails here.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import cast

import pytest
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient

from bench import oper_sets
from screw import app as app_module
from screw import cli, solid
from screw.calc import cost
from screw.params import BoltParams

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDS = REPO_ROOT / "bench/results/phase-07"
RUNTIME = REPO_ROOT / oper_sets.RUNTIME


def _directories() -> list[Path]:
    return sorted(path for path in RECORDS.iterdir() if path.is_dir())


def _runtime() -> dict[str, object]:
    found: dict[str, object] = json.loads(RUNTIME.read_text())
    return found


def _row(key: str) -> dict[str, object]:
    row = _runtime()[key]
    assert isinstance(row, dict)
    return row


def test_runtime_json_is_what_derive_runtime_writes_from_every_committed_record() -> None:
    assert RUNTIME.read_text() == oper_sets.runtime_text(_directories())


def test_the_shipped_build_timeouts_are_the_derived_ones() -> None:
    derived = json.loads(RUNTIME.read_text())["timeouts"]
    assert dict(cost.BUILD_TIMEOUT_S) == {artifact: float(row["seconds"])
                                          for artifact, row in derived.items()}


def test_runtime_json_holds_every_value_r16_r22_and_r23_decide() -> None:
    """07-16 on the record: N = 1, W(4) qualifies (run 41016510597), the trim is kept (run
    40909754190), and the 60-build drift run 41022812680 levels off, so its largest peak is W."""
    found = json.loads(RUNTIME.read_text())
    assert found["picked_workers"] == 1
    assert found["solid_cache_k"] == 4
    assert found["solid_cache"]["runs"] == ["41016510597"]
    assert found["arenas_kept"] is True
    assert found["recycling"]["max_tasks_per_child"] is None
    assert found["tessellation_kept"]["kept"] is True
    assert all(row["holds"] for row in found["plateau"].values())
    assert found["w"]["bytes"] == found["w"]["drift"]["bytes"] == 1758363648
    assert found["w"]["drift"]["reading"].startswith("41022812680:")
    assert found["shipped_mem_limit"]["bytes"] == 2415919104  # 2.25 GiB


def test_the_lifespan_starts_the_picked_number_of_build_workers(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """R16's pick is the `SCREW_BUILD_WORKERS` default, handed to the pool with the timeouts."""
    monkeypatch.delenv("SCREW_BUILD_WORKERS", raising=False)
    started: list[tuple[int, object]] = []

    class _Pool:
        workers = 0
        replaced = 0

        def __init__(self, workers: int, timeout: object) -> None:
            started.append((workers, timeout))

        def shutdown(self) -> None:
            pass

    monkeypatch.setattr(app_module, "BuildPool", _Pool)
    with TestClient(app_module.app):
        pass
    assert started == [(_runtime()["picked_workers"], cost.BUILD_TIMEOUT_S)]


def test_the_queue_depth_is_r17s(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("SCREW_BUILD_WORKERS", "SCREW_MAX_QUEUED_BUILDS"):
        monkeypatch.delenv(name, raising=False)
    depth = _row("queue_depth")["depth"]
    assert app_module._max_queued_builds() == depth
    assert depth == app_module.MAX_QUEUED_BUILDS


def test_retry_after_is_r18s_median_times_the_live_queue_depth(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The median is the shipped constant; the product is taken at run time (R18, D-11)."""
    medians: dict[str, float] = {}
    for artifact, row in _row("retry_after").items():
        assert isinstance(row, dict)
        assert isinstance(row["median_s"], float)
        medians[artifact] = row["median_s"]
    assert dict(app_module.MEDIAN_BUILD_S) == medians
    for artifact in cost.ARTIFACTS:
        assert app_module.retry_after(artifact) == str(
            max(1, math.ceil(medians[artifact] * app_module.MAX_QUEUED_BUILDS)))
    monkeypatch.setattr(app_module, "MAX_QUEUED_BUILDS", 10)
    assert app_module.retry_after("stl-fine") == str(math.ceil(medians["stl-fine"] * 10))
    monkeypatch.setattr(app_module, "MEDIAN_BUILD_S", {"step": 0.0})
    assert app_module.retry_after("step") == "1"  # never below 1 s


def test_no_503_carries_the_carried_5_s() -> None:
    assert '"Retry-After": "5"' not in Path(app_module.__file__).read_text()


def test_the_export_cache_is_r21s() -> None:
    assert "SCREW_EXPORT_CACHE_MB" not in os.environ
    assert _row("export_cache")["mib"] == app_module.EXPORT_CACHE_MB


def test_the_gzip_middleware_has_r19s_level_and_r20s_minimum_size() -> None:
    [gzip] = [m for m in app_module.app.user_middleware if cast(object, m.cls) is GZipMiddleware]
    assert gzip.kwargs == {"minimum_size": _row("minimum_size")["bytes"],
                           "compresslevel": _row("gzip")["level"]}
    assert _row("gzip")["level"] == app_module._GZIP_LEVEL


def test_no_build_worker_is_recycled_while_r23s_plateau_holds() -> None:
    assert _row("recycling")["max_tasks_per_child"] is None
    pool = Path(app_module.__file__).with_name("pool.py").read_text()
    assert "max_tasks_per_child=" not in pool


def test_the_solid_cache_is_r22s() -> None:
    assert "SCREW_SOLID_CACHE" not in os.environ
    assert solid._build_cached.cache_parameters()["maxsize"] == _runtime()["solid_cache_k"]


def test_an_export_hands_freed_heap_back_while_r23_keeps_the_trim(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """runtime.json keeps the trim (lower retained memory with it at every artifact), so every
    export still ends in malloc_trim(0)."""
    assert _runtime()["arenas_kept"] is True
    trims: list[int] = []

    def _trim(pad: int) -> int:
        trims.append(pad)
        return 1

    monkeypatch.setattr(solid, "_MALLOC_TRIM", _trim)
    solid.export(BoltParams(), "stl", "preview")
    assert trims == [0]


def test_the_cli_serves_r24s_number_of_server_processes(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCREW_WORKERS", raising=False)
    calls: list[dict[str, object]] = []
    monkeypatch.setattr("uvicorn.run", lambda *a, **kw: calls.append(kw))
    cli.main(["serve"])
    assert [kw["workers"] for kw in calls] == [_row("screw_workers")["workers"]]


@pytest.mark.parametrize("module", ["app.py", "pool.py", "cli.py", "solid/__init__.py",
                                    "calc/__init__.py", "calc/cost.py"])
def test_no_runtime_knob_is_left_interim(module: str) -> None:
    text = (Path(app_module.__file__).parent / module).read_text()
    assert "INTERIM" not in text
    assert "Phase 7" not in text
