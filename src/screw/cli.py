"""Command line placeholder so the CLI tests can be written first (GREEN replaces it)."""

from __future__ import annotations


def main(argv: list[str] | None = None) -> None:
    raise SystemExit(f"screw: command line not built yet (argv={argv})")
