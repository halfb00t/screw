"""Placeholder so the harness tests can be written first (GREEN replaces it)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from screw.params import BoltParams


@dataclass(frozen=True)
class GzipRow:
    level: int
    single_ms: float
    out_bytes: int
    concurrent_ms: float


def maxrss_bytes(raw: int, _system: str) -> int:
    return raw


def select_gzip_level(_rows: list[GzipRow]) -> int:
    return 9


def find_set(_sweep: Path | None, _label: str) -> BoltParams:
    raise SystemExit(3)
