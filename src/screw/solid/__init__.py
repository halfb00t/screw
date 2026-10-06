"""CadQuery solid construction and STL/STEP export.

This package is the only doorway to `cadquery`/`OCP` (import-linter contract 8), and it runs
inside a worker process, not the serving process: `app.py` reaches `export()` only through
a spawned `BuildPool`, never by importing this package (contract 5). OpenCascade is not
safe to drive from several threads at once, so every kernel call goes through one lock; it
stays uncontended under one-task-per-worker. The solid built for a parameter set is cached
here, per worker (`SCREW_SOLID_CACHE`, entries), because rebuilding it needs the kernel
that only a worker has. The exported-bytes cache lives one level up, in the serving
process (`app.py`'s `_BlobCache`): a repeat download never wakes a worker at all.

No `cadquery` object leaves this package: callers get `bytes`, or `BuildError`.
"""

from __future__ import annotations

import ctypes
import tempfile
import threading
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import cadquery as cq

if TYPE_CHECKING:
    from collections.abc import Callable

from screw import int_env
from screw.build_errors import BuildError
from screw.params import BoltParams, FastenerParams
from screw.solid import bolt

Format = Literal["stl", "step"]
Quality = Literal["preview", "fine"]

# INTERIM (D-01): (linear deflection mm, angular deflection rad) for STL tessellation.
# Carried from spur model.py:53 (preview 0.08/0.5, fine 0.01/0.1), where the absolute
# deviation was chosen for gears; not measured for screw. Phase 5 re-chooses it against
# the pair clearance (FRNT-06); Phase 7 re-sweeps (OPER-02).
TESSELLATION: dict[str, tuple[float, float]] = {"preview": (0.08, 0.5), "fine": (0.01, 0.1)}

_LOCK = threading.RLock()


def _load_malloc_trim() -> Callable[[int], int] | None:
    try:
        fn = ctypes.CDLL("libc.so.6").malloc_trim
    except (OSError, AttributeError):
        return None          # musl or macOS: nothing to do
    fn.argtypes = [ctypes.c_size_t]
    return fn


_MALLOC_TRIM = _load_malloc_trim()


def _release_arenas() -> None:
    """Hand freed heap back to the operating system after a build.

    OpenCascade churns through enormous numbers of short-lived allocations, and glibc
    keeps the freed arenas to reuse and never returns them, so a worker that has built a
    few large parts looks like it is leaking and eventually meets the container memory
    limit. INTERIM (D-01): spur measured 1578 MiB resident without this and 360 MiB with
    it over 40 distinct 160-199 tooth gears (spur model.py `_release_arenas`); that is
    spur's gear corpus, not screw's, and has not been measured here. Phase 7 re-sweeps
    (OPER-02). Called after every export().
    """
    if _MALLOC_TRIM is not None:
        _MALLOC_TRIM(0)


def _build(p: FastenerParams) -> cq.Solid:
    if isinstance(p, BoltParams):
        solid = bolt.cylinder(p)
    else:
        raise TypeError(f"no solid builder for kind {p.kind!r}")
    # An invariant a type cannot express is asserted positively: exactly one valid solid.
    if len(solid.Solids()) != 1 or not solid.isValid():
        raise BuildError("Geometry kernel produced an invalid solid for these parameters.")
    return solid


def _build_checked(p: FastenerParams) -> cq.Solid:
    try:
        return _build(p)
    except (BuildError, TypeError):
        # TypeError is the registry's "kind without a builder", a bug in screw that the
        # registry test catches; it must not be reworded as a user-facing kernel failure.
        raise
    except Exception as exc:  # OCCT raises assorted Standard_Failure subclasses
        raise BuildError(f"Geometry kernel failed ({type(exc).__name__}); "
                         "check d and length.") from exc


# INTERIM (D-01): 4 solids per worker, carried from spur model.py:561 where it sized a
# worker's repeat requests for one gear (preview, then STL, then STEP). Not measured for
# screw. Phase 7 re-sweeps (OPER-02).
_build_cached = lru_cache(maxsize=int_env("SCREW_SOLID_CACHE", 4))(_build_checked)


def build(p: FastenerParams) -> cq.Solid:
    """The cached solid for `p`. For tests and `bench/` only: it hands out a kernel object."""
    with _LOCK:
        return _build_cached(p)


def clear_cache() -> None:
    """Drop every cached solid, so `bench/` can time a cold build without a private import."""
    with _LOCK:
        _build_cached.cache_clear()


def _write_export(shape: cq.Solid, p: FastenerParams, fmt: Format, quality: Quality) -> bytes:
    with tempfile.TemporaryDirectory(prefix="screw-") as d:
        path = Path(d) / f"{p.slug()}.{fmt}"
        if fmt == "stl":
            tol, ang = TESSELLATION[quality]
            # exportStl() attaches a triangulation to the solid it is called on.
            # _build_cached hands the same object to every caller for one parameter set,
            # and build() returns it after releasing _LOCK, so meshing it in place would
            # leave .BoundingBox() reading the mesh and make a preview after a fine export
            # reuse the fine mesh. spur measured both (L24): zlen 7.5000 -> 7.5877 mm after
            # a preview export, and 46,278 triangles instead of 9,066. A copy keeps the
            # cached solid mesh-free for its whole life, at 1.4-17.6 ms per export on
            # spur's gears (not measured for screw). No positional argument to copy(): its
            # one parameter is mesh, default False, and copy(mesh=True) would carry a mesh.
            shape.copy().exportStl(str(path), tolerance=tol, angularTolerance=ang,
                                   ascii=False, relative=False)
        else:
            # STEP export attaches no mesh, so the cached solid stays exact and needs no copy.
            shape.exportStep(str(path))
        return path.read_bytes()


def export(p: FastenerParams, fmt: Format, quality: Quality = "fine") -> bytes:
    with _LOCK:
        data = _write_export(_build_cached(p), p, fmt, quality)
        _release_arenas()
        return data
