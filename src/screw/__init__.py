"""screw: parametric thread and fastener generator.

This package holds the walking skeleton (Phase 1): one registered `bolt` kind that builds a
plain unthreaded cylinder, served by the runtime ported from spur. `AGENTS.md` and
`docs/architecture/overview.md` say what the finished product looks like.
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
