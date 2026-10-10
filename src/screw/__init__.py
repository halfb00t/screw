"""screw: parametric thread and fastener generator.

This package holds one registered `bolt` kind that builds a threaded rod (Phase 3): the
ISO 68-1:2023 basic profile, right- or left-hand, with no head, table or nut yet. The thread
maths is `calc/thread.py`, the one builder is `solid/helical.py`, and every build passes the
`solid` postcondition before it is cached or served, by the runtime ported from spur.
`AGENTS.md` and `docs/architecture/overview.md` say what the finished product looks like.
"""

import os

# One literal line: hatch reads the version out of this file at install time (D-06 keeps
# the skeleton at 0.0.x, never released).
__version__ = "0.0.0"


def int_env(name: str, default: int) -> int:
    """A positive integer setting from the environment, falling back on nonsense."""
    try:
        return max(1, int(os.environ.get(name) or default))
    except ValueError:
        return default
