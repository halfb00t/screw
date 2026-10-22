"""CadQuery solid construction and STL/STEP export.

This package is the only doorway to `cadquery`/`OCP` (import-linter contract 8), and it runs
inside a worker process, not the serving process: `app.py` reaches `export()` only through
a spawned `BuildPool`, never by importing this package (contract 5). OpenCascade is not
safe to drive from several threads at once, so every kernel call goes through one lock; it
stays uncontended under one-task-per-worker. The solid built for a parameter set is cached
here, per worker (`SCREW_SOLID_CACHE`, entries), because rebuilding it needs the kernel
that only a worker has. The exported-bytes cache lives one level up, in the serving
process (`app.py`'s `_BlobCache`): a repeat download never wakes a worker at all.

No `cadquery` object leaves this package: callers get `bytes`, or `BuildError`. Every build
passes `check_solid` (THRD-04) inside the function `lru_cache` wraps, so a build the gate
refuses is neither cached nor exported.
"""

from __future__ import annotations

import ctypes
import struct
import tempfile
import threading
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_ReturnStatus

if TYPE_CHECKING:
    from collections.abc import Callable

from screw import int_env
from screw.build_errors import BuildError
from screw.calc.thread import (
    CHAMFER_ANGLE_DEG,
    COUNTERSINK_HALF_ANGLE_DEG,
    TIP_ANGLE_DEG,
    bolt_end_closed_volume,
    built_thread_length,
    closed_volume,
    countersink_face_radius,
    countersink_volume,
    end_depths,
    face_chamfer_volume,
    fillet_radius,
    fillet_ring_volume,
    nut_end_closed_volume,
    piece_refusal,
    tip_cone_fits,
    tip_cone_volume,
    volume_check,
)
from screw.params import BoltParams, FastenerParams, NutParams
from screw.solid import bolt, nut

Format = Literal["stl", "step"]
Quality = Literal["preview", "fine"]

# (linear deflection mm, angular deflection rad) for STL tessellation, absolute millimetres
# (`relative=False` in `_write_export`). The "fine" value is the Mesh deviation (Phase 5, D-21)
# rule's, not spur's: the largest step on the ladder 0.01, 0.0075, 0.005, 0.0025 mm (0.1 rad)
# whose measured maximum radial deviation over M2, M3, M6, M10, M20, both hands, is at most
# 0.5 x the 0.05 mm proof clearance (the owner's R6 fraction), 0.025 mm. The rule and the ladder
# were committed in bench/mesh_deviation.py before the run; bench/RESULTS.md "Mesh deviation
# (Phase 5, D-21)" selects 0.01 mm, worst row 0.0161 mm (M20), 64 % of the bound, and the
# triangles and bytes at every step. It is the value `2026-10-08-a-ladder` and every fine-STL cap
# in calc/thread.py (FINE_STL_ROWS) were measured at, so the rule kept the caps. The preview is
# coarser on purpose: 0.0587 to 0.1299 mm measured, up to 2.6 x the whole clearance, which is why
# no number on the panel comes from a mesh (FRNT-06). tests/test_mesh.py pins the fine bound and
# that the preview breaks it.
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


# Relative error bound of `BRepGProp.VolumeProperties_s`, per face. Read from the OCP
# docstring: above 0.001 the integration is non-adaptive. 1e-7 cost 2x (0.4-2.0 s against
# 0.2-1.0 s per row) for no gain: 1.53e-6 against 1.62e-6 at M6 L20 (RESEARCH Code Example 4).
PRECISE_EPS = 1e-6


def precise_volume(shape: cq.Shape) -> float:
    """Volume to `PRECISE_EPS`, signed: an inverted solid reads about -1 times its closed form.

    L11's estimator, never the default `Volume()`, which reads -1.001 of the closed form on an
    inverted solid and +6.3 % on a ruled-surface thread while `isValid()` stays True.
    """
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props, PRECISE_EPS, False, False)
    return float(props.Mass())


def check_structure(shape: cq.Shape) -> None:
    """Exactly one solid and valid: the checks `check_solid` runs before it reads a volume."""
    count = len(shape.Solids())
    if count != 1:
        raise BuildError(f"Geometry kernel produced {count} solids for these parameters, "
                         "expected exactly 1.")
    if not shape.isValid():
        raise BuildError("Geometry kernel produced an invalid solid for these parameters.")


def check_solid(shape: cq.Shape, closed: float, part: str = "solid",
                volume: float | None = None) -> float:
    """The THRD-04 postcondition (D-08, L11): exactly one solid, valid, and the right volume.

    `part` names what was judged in the volume message (`thread` for the bare thread gate).
    `volume` is a precise volume the caller already measured of this same shape (the end pieces
    are judged from it too), so the kernel integrates it once; it is read after the structural
    checks, never before. Returns the volume judged, for the same reason.

    `_build` runs it inside the function `lru_cache` wraps, so a refusal is never cached or
    exported; tests and `bench/` call it on shapes no parameter set builds (the positive
    controls, the void). The checks run in this order and the first failure is the one named.
    """
    check_structure(shape)
    measured = precise_volume(shape) if volume is None else volume
    refusal = volume_check(measured, closed)
    if refusal is not None:
        raise BuildError(f"Geometry kernel produced the wrong {part}: {refusal}.")
    return measured


def _build(p: FastenerParams) -> cq.Solid:
    if isinstance(p, BoltParams):
        return _build_bolt(p)
    if isinstance(p, NutParams):
        return _build_nut(p)
    raise TypeError(f"no solid builder for kind {p.kind!r}")


def _build_nut(p: NutParams) -> cq.Solid:
    # The void is gated against the bare section first, like the bolt's thread: it is the whole
    # of what the nut subtracts, so an error in it is not diluted by the prism (D-13, RESEARCH F3).
    # The sign of the nut's volume is kept: an inverted result reads about -1 times the form.
    thread_void = nut.void(p)
    check_solid(thread_void, closed_volume(p.d, p.pitch, p.m + 2 * p.pitch, p.clearance),
                part="void")
    body = nut.assemble(p, thread_void)
    check_structure(body)
    volume = precise_volume(body)
    # Each countersink and each chamfer is judged by the volume it removed, against its own
    # oracle at T_PIECE, before the whole nut is judged at T_GATE: a countersink is under 1 % of
    # the nut and a skipped one hides inside the gate (P8, D-10). The structure is checked first
    # so a broken cut is named as one.
    csk, chamfer, _ = end_depths(p.d, p.pitch, p.clearance, p.s, p.m)
    oracle = {
        "lead-in countersink": 0.0 if csk <= 0 else countersink_volume(
            p.d, p.pitch, p.clearance, p.s, countersink_face_radius(p.d),
            COUNTERSINK_HALF_ANGLE_DEG, csk),
        "face chamfer": face_chamfer_volume(p.s, p.s / 2, CHAMFER_ANGLE_DEG, chamfer),
    }
    for what, cut in nut.finish(p, body):
        check_structure(cut)
        after = precise_volume(cut)
        piece = piece_refusal(volume - after, oracle[what], what)
        if piece is not None:
            raise BuildError(f"Geometry kernel produced the wrong {what}: {piece}.")
        body, volume = cut, after
    check_solid(body, nut_end_closed_volume(p.d, p.pitch, p.s, p.m, p.clearance), volume=volume)
    return body.Solids()[0]


def _build_bolt(p: BoltParams) -> cq.Solid:
    t = built_thread_length(p.thread_length, p.length)
    bare_thread = bolt.thread(p)
    # Gate the bare thread first (RESEARCH Alert 5): it is 0.19 to 0.57 of the whole volume, so a
    # thread error the whole-part gate dilutes below T_GATE (1.1e-4 to 1.4e-4 at M6 x 20 is
    # passed by the fused check alone) is caught here. Cost: one more precise volume, at most
    # 0.82 s over the grid (`2026-10-08-a-grid` volume_s).
    before = check_solid(bare_thread, closed_volume(p.d, p.pitch, t), part="thread")
    tip = tip_cone_fits(p.pitch, t)
    thread = bare_thread
    if tip:
        # The cone is cut from the bare thread and judged twice: the volume it removed against
        # its own oracle at T_PIECE (checked first, so a skipped or wrong-angle cut is named as
        # the tip and not as a thread that is off), then the cut thread against the closed form
        # less the cone at T_GATE.
        thread = bolt.tip_cut(p, bare_thread)
        check_structure(thread)
        after = precise_volume(thread)
        piece = piece_refusal(before - after, tip_cone_volume(p.d, p.pitch, TIP_ANGLE_DEG),
                              "tip cone")
        if piece is not None:  # R11, P8: the whole-part gate dilutes a piece this small
            raise BuildError(f"Geometry kernel produced the wrong tip cone: {piece}.")
        check_solid(thread, closed_volume(p.d, p.pitch, t)
                    - tip_cone_volume(p.d, p.pitch, TIP_ANGLE_DEG), part="thread", volume=after)
    plain = bolt.assemble(p, thread)
    r = fillet_radius(p.d, p.pitch, p.length, t)
    fused = plain
    volume: float | None = None
    if r is not None:
        # The ring is judged by the volume it added, from precise volumes before and after.
        # The structure is checked first so a broken fuse is named as one.
        fused = bolt.add_fillet(p, plain, r)
        check_structure(fused)
        volume = precise_volume(fused)
        piece = piece_refusal(volume - precise_volume(plain), fillet_ring_volume(p.d, r),
                              "fillet ring")
        if piece is not None:
            raise BuildError(f"Geometry kernel produced the wrong fillet ring: {piece}.")
    check_solid(fused, bolt_end_closed_volume(p.d, p.pitch, p.length, p.s, p.k, t, tip, r),
                volume=volume)
    return fused.Solids()[0]


def _build_checked(p: FastenerParams) -> cq.Solid:
    try:
        return _build(p)
    except (BuildError, TypeError):
        # TypeError is the registry's "kind without a builder", a bug in screw that the
        # registry test catches; it must not be reworded as a user-facing kernel failure.
        raise
    except Exception as exc:  # OCCT raises assorted Standard_Failure subclasses
        # The model's own fields, in declaration order, so a nut's failure never sends the user to a
        # bolt's `length` and `k`.
        names = list(type(p).model_fields)
        raise BuildError(f"Geometry kernel failed ({type(exc).__name__}); "
                         f"check {', '.join(names[:-1])} and {names[-1]}.") from exc


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


def _check_stl(data: bytes) -> None:
    """Refuse an STL whose header count disagrees with its byte length or has fewer than 4
    facets (the fewest a closed solid has): a mesh that is not the part must not be served."""
    count = struct.unpack("<I", data[80:84])[0] if len(data) >= 84 else 0
    if len(data) != 84 + 50 * count or count < 4:
        raise BuildError(f"STL export failed: the kernel wrote {len(data)} bytes claiming "
                         f"{count} facets for these parameters.")


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
            written = shape.copy().exportStl(str(path), tolerance=tol, angularTolerance=ang,
                                             ascii=False, relative=False)
            # False means no file was written; reading it would be a FileNotFoundError.
            if not written:
                raise BuildError("STL export failed: the kernel wrote no file for these "
                                 "parameters.")
            data = path.read_bytes()
            _check_stl(data)
            return data
        # STEP export attaches no mesh, so the cached solid stays exact and needs no copy.
        # cadquery discards the status of the transfer; only the write's is observable.
        status = shape.exportStep(str(path))
        if status != IFSelect_ReturnStatus.IFSelect_RetDone:
            raise BuildError(f"STEP export failed: the kernel reported {status}.")
        return path.read_bytes()


def export(p: FastenerParams, fmt: Format, quality: Quality = "fine") -> bytes:
    with _LOCK:
        data = _write_export(_build_cached(p), p, fmt, quality)
        _release_arenas()
        return data
