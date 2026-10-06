"""Placeholder so the harness tests can be written first (GREEN replaces it)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from screw.params import BoltParams


@dataclass(frozen=True)
class Timing:
    label: str
    build: float
    stl: float
    step: float
    stl_bytes: int
    stl_triangles: int


def load_sweep(_path: Path | None = None) -> list[tuple[str, BoltParams]]:
    return []


def stl_size(data: bytes) -> tuple[int, int]:
    return len(data), 0


def report(_path: Path | None, _timings: list[Timing], _timeout: int,
           _load: tuple[float, float, float]) -> str:
    return ""
