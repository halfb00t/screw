"""Shared fixtures for the whole suite.

Autouse root-logger reset: `records.configure()` installs a handler bound to
whatever `sys.stderr` was at construction time. Without this fixture, any test that
calls `configure()` directly, or drives the app's `lifespan()` (which also calls it),
would leave that handler -- and the stream object it captured -- installed on the root
logger for every test that runs afterwards, including tests with no interest in logging
at all. Snapshotting the handler list and level before each test and restoring them
after is also what lets each `configure()`-touching test in tests/test_records.py start
from a genuinely unconfigured root logger, rather than depending on test execution order.

`REQUIRED_VALUES` and `part_of` are the one place a test learns a valid value for a required
field (the nut's `clearance`): a registry-wide test builds `part_of(kind)` instead of `model()`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator

import pytest

from screw.params import KINDS, FastenerParams

# A test input for each required field, never a product default (D-01, PAIR-01): the product has
# none, and test_parity pins that this table names exactly the required fields of every kind.
REQUIRED_VALUES: dict[str, dict[str, float]] = {"nut": {"clearance": 0.1}}


@pytest.fixture
def part_of() -> Callable[[str], FastenerParams]:
    return lambda kind: KINDS[kind].model_validate(REQUIRED_VALUES.get(kind, {}))


@pytest.fixture(autouse=True)
def _reset_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    handlers_before = list(root.handlers)
    level_before = root.level
    yield
    for handler in list(root.handlers):
        if handler not in handlers_before:
            root.removeHandler(handler)
    root.setLevel(level_before)
