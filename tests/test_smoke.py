"""Proves the harness is wired, nothing more: the package in `.venv` is this checkout.

hatch reads the version from src/screw/__init__.py at install time, so a mismatch here
means the editable install points somewhere else (a worktree sharing the main checkout's
.venv -- see docs/HOW_TO_DEVELOP.md, step 5) or is stale. Replaced by real tests as the
first subsystem lands.
"""

from importlib.metadata import version

import screw


def test_the_installed_package_is_this_checkout() -> None:
    assert version("screw") == screw.__version__
