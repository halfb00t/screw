"""The per-artifact vocabulary the build timeout, the budgets and the cost model share (D-09).

One name per file a download can produce, so a timeout, a budget and a measured cost all key
on the same three strings.
"""

from __future__ import annotations

import pytest

from screw.calc.cost import ARTIFACTS, BUILD_TIMEOUT_S, artifact_of


@pytest.mark.parametrize(("fmt", "quality", "want"), [
    ("stl", "preview", "stl-preview"),
    ("stl", "fine", "stl-fine"),
    ("step", "preview", "step"),
    ("step", "fine", "step"),
])
def test_an_artifact_is_named_by_the_file_a_download_produces(
        fmt: str, quality: str, want: str) -> None:
    """STEP ignores the quality, so both qualities are one artifact with one timeout."""
    assert artifact_of(fmt, quality) == want


@pytest.mark.parametrize(("fmt", "quality"), [
    ("obj", "fine"),
    ("stl", "draft"),
    ("step", "draft"),
    ("", ""),
])
def test_what_no_download_produces_is_not_an_artifact(fmt: str, quality: str) -> None:
    with pytest.raises(ValueError, match="artifact"):
        artifact_of(fmt, quality)


def test_the_artifacts_are_the_three_downloads() -> None:
    assert ARTIFACTS == ("stl-preview", "stl-fine", "step")


def test_every_artifact_has_a_positive_build_timeout_and_nothing_else_does() -> None:
    assert set(BUILD_TIMEOUT_S) == set(ARTIFACTS)
    assert all(seconds > 0 for seconds in BUILD_TIMEOUT_S.values())
