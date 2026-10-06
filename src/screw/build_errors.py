"""Build-failure exception types, kept free of the CAD kernel on purpose.

`app.py` has to name a build failure (to map it to a 422) without importing `cadquery`:
the serving process must not reach the kernel by any path (import-linter contract 5).
Defining these two exceptions here, not in the solid package, is what makes that possible:
`screw.solid` raises them, but the import that matters -- `from .build_errors import
BuildError` in `app.py` -- never drags OpenCascade in behind it.

`BuildTimeout` is its own class, not the builtin `TimeoutError`, because it is the one
timeout `app.py` turns into a 503 with its own error `type` ("timeout"), distinct from
`BrokenProcessPool`'s 503 -- a client can tell "come back in a moment" from "the worker
died" by this class alone. (spur kept it from the 3.10 floor, where `asyncio.TimeoutError`
and the builtin were different classes; on 3.12 they are aliases, so that reason is gone.)
"""

from __future__ import annotations


class BuildError(RuntimeError):
    """The CAD kernel could not produce a valid solid for these parameters."""


class BuildTimeout(Exception):  # noqa: N818 -- named after asyncio.TimeoutError on purpose
    """A build did not finish within its allotted time; the worker was terminated."""
